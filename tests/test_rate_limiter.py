from uuid import uuid4

import pytest

from app.rate_limiter import check_rate_limit


@pytest.mark.asyncio
async def test_under_limit_allowed():
    user = f"test-user-under-{uuid4()}"

    allowed = await check_rate_limit(user, capacity=10, refill_rate=10)

    assert allowed is True


@pytest.mark.asyncio
async def test_over_limit_rejected():
    user = f"test-user-over-{uuid4()}"

    for _ in range(10):
        await check_rate_limit(user, capacity=10, refill_rate=0.001)

    allowed = await check_rate_limit(user, capacity=10, refill_rate=0.001)

    assert allowed is False

