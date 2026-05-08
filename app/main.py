from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import analytics, redirect, shorten


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="URL Shortener", version="1.0.0", lifespan=lifespan)

cors_origins = [
    origin.strip()
    for origin in settings.cors_origins.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.head("/", include_in_schema=False)
async def root_head():
    return Response(status_code=204)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# Keep this catch-all route last so it does not capture /health or /analytics.
app.include_router(redirect.router, tags=["redirect"])
