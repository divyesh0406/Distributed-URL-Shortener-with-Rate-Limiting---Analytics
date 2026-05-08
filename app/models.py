from sqlalchemy import Column, DateTime, Index, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class URL(Base):
    __tablename__ = "urls"

    short_code = Column(String(10), primary_key=True, index=True)
    long_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    click_count = Column(Integer, default=0, nullable=False)
    idempotency_key = Column(String(64), unique=True, index=True, nullable=True)


class ClickEvent(Base):
    __tablename__ = "click_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    short_code = Column(String(10), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_agent = Column(String(512))
    ip_address = Column(String(45))
    referer = Column(String(2048))

    __table_args__ = (
        Index("idx_click_short_code_ts", "short_code", "timestamp"),
    )
