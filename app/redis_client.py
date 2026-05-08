from urllib.parse import urlparse, urlunparse

import redis.asyncio as redis

from app.config import settings


def build_redis_url(redis_url: str) -> str:
    parsed = urlparse(redis_url)

    if parsed.scheme == "redis" and parsed.hostname and "upstash.io" in parsed.hostname:
        parsed = parsed._replace(scheme="rediss")

    return urlunparse(parsed)


redis_client = redis.from_url(
    build_redis_url(settings.redis_url),
    encoding="utf-8",
    decode_responses=True,
    max_connections=20,
)
