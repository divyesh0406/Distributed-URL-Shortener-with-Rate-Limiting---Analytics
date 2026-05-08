import time

from app.redis_client import redis_client


TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1]) or capacity
local last_refill = tonumber(bucket[2]) or now

local elapsed = math.max(0, now - last_refill)
tokens = math.min(capacity, tokens + elapsed * refill_rate)

local allowed = 0
if tokens >= requested then
    tokens = tokens - requested
    allowed = 1
end

redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', key, 3600)

return allowed
"""


async def check_rate_limit(
    identifier: str,
    capacity: int = 100,
    refill_rate: float = 100 / 60,
) -> bool:
    """
    Return True when the request is allowed, or False when rate-limited.

    The Lua script runs atomically inside Redis, so concurrent requests cannot
    race between checking and decrementing the same token bucket.
    """
    key = f"ratelimit:{identifier}"
    now = time.time()
    result = await redis_client.eval(
        TOKEN_BUCKET_LUA,
        1,
        key,
        capacity,
        refill_rate,
        now,
        1,
    )

    return bool(result)
