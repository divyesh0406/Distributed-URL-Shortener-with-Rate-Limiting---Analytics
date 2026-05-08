from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings


def build_async_db_config(database_url: str) -> tuple[str, dict]:
    """
    Convert a production-friendly Postgres URL into asyncpg settings.

    Neon commonly provides URLs with `sslmode=require`. asyncpg does not accept
    `sslmode` directly, so we remove it from the URL and pass SSL separately.
    """
    url = make_url(database_url)
    connect_args = {}

    if url.drivername in {"postgresql", "postgres"}:
        url = url.set(drivername="postgresql+asyncpg")

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    if sslmode in {"require", "prefer", "verify-ca", "verify-full"}:
        connect_args["ssl"] = True

    url = url.set(query=query)
    return url.render_as_string(hide_password=False), connect_args


async_db_url, connect_args = build_async_db_config(settings.database_url)

engine = create_async_engine(
    async_db_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args=connect_args,
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
