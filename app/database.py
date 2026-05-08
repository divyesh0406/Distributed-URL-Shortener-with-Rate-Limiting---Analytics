from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings


# Convert the standard PostgreSQL URL into SQLAlchemy's asyncpg driver URL.
async_db_url = settings.database_url.replace(
    "postgresql://",
    "postgresql+asyncpg://",
    1,
)

engine = create_async_engine(
    async_db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
