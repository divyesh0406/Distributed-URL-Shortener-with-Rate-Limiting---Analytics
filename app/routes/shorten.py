from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import URL
from app.rate_limiter import check_rate_limit
from app.schemas import ShortenRequest, ShortenResponse
from app.shortener import generate_short_code


router = APIRouter()


@router.post("/shorten", response_model=ShortenResponse)
async def shorten(
    payload: ShortenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    allowed = await check_rate_limit(
        client_ip,
        capacity=settings.rate_limit_per_minute,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    long_url = str(payload.long_url)
    idempotency_key = payload.idempotency_key or ""
    short_code = generate_short_code(long_url, idempotency_key)

    existing = await db.execute(select(URL).where(URL.short_code == short_code))
    row = existing.scalar_one_or_none()

    if row is not None and row.long_url != long_url:
        raise HTTPException(status_code=409, detail="Short code collision")

    if row is None:
        row = URL(
            short_code=short_code,
            long_url=long_url,
            idempotency_key=idempotency_key or None,
        )
        db.add(row)
        try:
            await db.commit()
            await db.refresh(row)
        except Exception:
            await db.rollback()
            existing = await db.execute(select(URL).where(URL.short_code == short_code))
            row = existing.scalar_one_or_none()

            if row is None and idempotency_key:
                existing = await db.execute(
                    select(URL).where(URL.idempotency_key == idempotency_key)
                )
                row = existing.scalar_one_or_none()

            if row is None:
                raise HTTPException(status_code=409, detail="Shorten request conflict")

            if row.long_url != long_url:
                raise HTTPException(status_code=409, detail="Short code collision")

    return ShortenResponse(
        short_code=row.short_code,
        short_url=f"{settings.base_url}/{row.short_code}",
        long_url=row.long_url,
        created_at=row.created_at,
    )
