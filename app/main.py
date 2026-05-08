from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routes import analytics, redirect, shorten


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="URL Shortener", version="1.0.0", lifespan=lifespan)

app.include_router(shorten.router, tags=["shorten"])
app.include_router(analytics.router, tags=["analytics"])


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


# Keep this catch-all route last so it does not capture /health or /analytics.
app.include_router(redirect.router, tags=["redirect"])
