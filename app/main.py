from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

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


@app.get("/", tags=["meta"])
async def root():
    return {
        "service": "URL Shortener",
        "status": "ok",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# Keep this catch-all route last so it does not capture /health or /analytics.
app.include_router(redirect.router, tags=["redirect"])
