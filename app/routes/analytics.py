from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import ClickEvent, URL
from app.redis_client import redis_client
from app.schemas import AnalyticsResponse, URLAnalyticsResponse


router = APIRouter()


@router.get("/analytics", response_model=list[URLAnalyticsResponse])
async def all_analytics(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(URL).order_by(URL.created_at.desc()).limit(100))
    url_rows = result.scalars().all()

    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    responses = []

    for url_row in url_rows:
        count_24h = await db.execute(
            select(func.count(ClickEvent.id)).where(
                ClickEvent.short_code == url_row.short_code,
                ClickEvent.timestamp >= last_24h,
            )
        )
        count_7d = await db.execute(
            select(func.count(ClickEvent.id)).where(
                ClickEvent.short_code == url_row.short_code,
                ClickEvent.timestamp >= last_7d,
            )
        )
        responses.append(
            URLAnalyticsResponse(
                short_code=url_row.short_code,
                short_url=f"{settings.base_url}/{url_row.short_code}",
                long_url=url_row.long_url,
                created_at=url_row.created_at,
                total_clicks=url_row.click_count,
                clicks_last_24h=count_24h.scalar() or 0,
                clicks_last_7d=count_7d.scalar() or 0,
            )
        )

    return responses


@router.get("/analytics/{short_code}", response_model=AnalyticsResponse)
async def analytics(short_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url_row = result.scalar_one_or_none()
    if url_row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    count_24h = await db.execute(
        select(func.count(ClickEvent.id)).where(
            ClickEvent.short_code == short_code,
            ClickEvent.timestamp >= last_24h,
        )
    )
    count_7d = await db.execute(
        select(func.count(ClickEvent.id)).where(
            ClickEvent.short_code == short_code,
            ClickEvent.timestamp >= last_7d,
        )
    )

    return AnalyticsResponse(
        short_code=short_code,
        total_clicks=url_row.click_count,
        clicks_last_24h=count_24h.scalar() or 0,
        clicks_last_7d=count_7d.scalar() or 0,
    )


@router.delete("/urls/{short_code}", status_code=204)
async def delete_url(short_code: str, db: AsyncSession = Depends(get_db)):
    await delete_url_by_code(short_code, db)


@router.delete("/analytics/{short_code}", status_code=204)
async def delete_url_from_analytics(short_code: str, db: AsyncSession = Depends(get_db)):
    await delete_url_by_code(short_code, db)


async def delete_url_by_code(short_code: str, db: AsyncSession):
    result = await db.execute(select(URL).where(URL.short_code == short_code))
    url_row = result.scalar_one_or_none()
    if url_row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")

    await db.execute(delete(ClickEvent).where(ClickEvent.short_code == short_code))
    await db.delete(url_row)
    await db.commit()
    await redis_client.delete(f"url:{short_code}")
