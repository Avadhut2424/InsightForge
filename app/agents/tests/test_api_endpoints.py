import pytest
from httpx import AsyncClient, ASGITransport
from app.api.main import app

@pytest.mark.asyncio
async def test_input_validation_rejects_empty():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/research", json={"topic": ""})
        assert r.status_code == 400
        assert "cannot be empty" in r.json()["detail"]

@pytest.mark.asyncio
async def test_input_validation_rejects_whitespace():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/research", json={"topic": "   "})
        assert r.status_code == 400
        assert "cannot be empty" in r.json()["detail"]

@pytest.mark.asyncio
async def test_input_validation_rejects_too_short():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/research", json={"topic": "ab"})
        assert r.status_code == 400
        assert "too short" in r.json()["detail"]

@pytest.mark.asyncio
async def test_input_validation_rejects_too_long():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/research", json={"topic": "a" * 501})
        assert r.status_code == 400
        assert "too long" in r.json()["detail"]

@pytest.mark.asyncio
async def test_get_nonexistent_run_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/research/999999")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"].lower()
