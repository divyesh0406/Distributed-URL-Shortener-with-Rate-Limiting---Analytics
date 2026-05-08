from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ClickEvent, URL
from app.schemas import AnalyticsResponse


router = APIRouter()


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
