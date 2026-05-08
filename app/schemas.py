from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class ShortenRequest(BaseModel):
    long_url: HttpUrl
    idempotency_key: Optional[str] = Field(None, max_length=64)


class ShortenResponse(BaseModel):
    short_code: str
    short_url: str
    long_url: str
    created_at: datetime


class AnalyticsResponse(BaseModel):
    short_code: str
    total_clicks: int
    clicks_last_24h: int
    clicks_last_7d: int
