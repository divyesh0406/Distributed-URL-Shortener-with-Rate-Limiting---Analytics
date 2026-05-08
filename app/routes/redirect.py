from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.kafka_client import publish_click_event
from app.models import ClickEvent, URL
from app.redis_client import redis_client


router = APIRouter()

CACHE_TTL_SECONDS = 3600


@router.get("/{short_code}")
async def redirect_to_long(
    short_code: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    cache_key = f"url:{short_code}"
    long_url = await redis_client.get(cache_key)

    if long_url is None:
        result = await db.execute(select(URL).where(URL.short_code == short_code))
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Short URL not found")

        long_url = row.long_url
        await redis_client.setex(cache_key, CACHE_TTL_SECONDS, long_url)

    event = {
        "short_code": short_code,
        "timestamp": datetime.utcnow().isoformat(),
        "user_agent": request.headers.get("user-agent", ""),
        "ip_address": request.client.host if request.client else "",
        "referer": request.headers.get("referer", ""),
    }

    if settings.enable_kafka:
        publish_click_event(event)
    else:
        click = ClickEvent(
            short_code=short_code,
            user_agent=event["user_agent"][:512],
            ip_address=event["ip_address"][:45],
            referer=event["referer"][:2048],
        )
        db.add(click)
        await db.execute(
            update(URL)
            .where(URL.short_code == short_code)
            .values(click_count=URL.click_count + 1)
        )
        await db.commit()

    return RedirectResponse(url=long_url, status_code=307)
