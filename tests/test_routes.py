from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import Base, engine
from app.main import app


@pytest.fixture(scope="module", autouse=True)
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_shorten_returns_short_code():
    url = f"https://www.example.com/{uuid4()}"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post("/shorten", json={"long_url": url})

    assert response.status_code == 200
    data = response.json()
    assert data["long_url"] == url
    assert "short_code" in data
    assert len(data["short_code"]) == 7


@pytest.mark.asyncio
async def test_shorten_is_idempotent():
    url = f"https://www.example.com/{uuid4()}"
    idempotency_key = f"test-key-{uuid4()}"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post(
            "/shorten",
            json={"long_url": url, "idempotency_key": idempotency_key},
        )
        second = await client.post(
            "/shorten",
            json={"long_url": url, "idempotency_key": idempotency_key},
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["short_code"] == second.json()["short_code"]


@pytest.mark.asyncio
async def test_reusing_idempotency_key_for_different_url_returns_conflict():
    idempotency_key = f"conflict-key-{uuid4()}"
    first_url = f"https://www.example.com/{uuid4()}"
    second_url = f"https://www.example.com/{uuid4()}"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        first = await client.post(
            "/shorten",
            json={"long_url": first_url, "idempotency_key": idempotency_key},
        )
        second = await client.post(
            "/shorten",
            json={"long_url": second_url, "idempotency_key": idempotency_key},
        )

    assert first.status_code == 200
    assert second.status_code == 409
    assert "Idempotency key already used" in second.json()["detail"]


@pytest.mark.asyncio
async def test_redirect_and_analytics():
    url = f"https://www.example.com/{uuid4()}"
    idempotency_key = f"redirect-key-{uuid4()}"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        shorten_response = await client.post(
            "/shorten",
            json={"long_url": url, "idempotency_key": idempotency_key},
        )
        short_code = shorten_response.json()["short_code"]

        redirect_response = await client.get(
            f"/{short_code}",
            follow_redirects=False,
        )
        analytics_response = await client.get(f"/analytics/{short_code}")

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == url

    assert analytics_response.status_code == 200
    analytics = analytics_response.json()
    assert analytics["short_code"] == short_code
    assert analytics["total_clicks"] == 1
    assert analytics["clicks_last_24h"] == 1
    assert analytics["clicks_last_7d"] == 1


@pytest.mark.asyncio
async def test_all_analytics_lists_created_urls():
    url = f"https://www.example.com/{uuid4()}"
    idempotency_key = f"list-key-{uuid4()}"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        shorten_response = await client.post(
            "/shorten",
            json={"long_url": url, "idempotency_key": idempotency_key},
        )
        short_code = shorten_response.json()["short_code"]
        list_response = await client.get("/analytics")

    assert list_response.status_code == 200
    items = list_response.json()
    matching = [item for item in items if item["short_code"] == short_code]
    assert matching
    assert matching[0]["long_url"] == url
    assert matching[0]["short_url"].endswith(f"/{short_code}")


@pytest.mark.asyncio
async def test_delete_url_removes_short_url():
    url = f"https://www.example.com/{uuid4()}"
    idempotency_key = f"delete-key-{uuid4()}"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        shorten_response = await client.post(
            "/shorten",
            json={"long_url": url, "idempotency_key": idempotency_key},
        )
        short_code = shorten_response.json()["short_code"]

        delete_response = await client.delete(f"/urls/{short_code}")
        redirect_response = await client.get(f"/{short_code}", follow_redirects=False)
        analytics_response = await client.get(f"/analytics/{short_code}")

    assert delete_response.status_code == 204
    assert redirect_response.status_code == 404
    assert analytics_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_url_from_analytics_path_removes_short_url():
    url = f"https://www.example.com/{uuid4()}"
    idempotency_key = f"delete-analytics-key-{uuid4()}"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        shorten_response = await client.post(
            "/shorten",
            json={"long_url": url, "idempotency_key": idempotency_key},
        )
        short_code = shorten_response.json()["short_code"]

        delete_response = await client.delete(f"/analytics/{short_code}")
        redirect_response = await client.get(f"/{short_code}", follow_redirects=False)

    assert delete_response.status_code == 204
    assert redirect_response.status_code == 404


@pytest.mark.asyncio
async def test_404_for_unknown_code():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/zzzzzzz", follow_redirects=False)

    assert response.status_code == 404
