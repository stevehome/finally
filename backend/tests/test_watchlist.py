"""Tests for the watchlist API endpoints — GET/POST /api/watchlist, DELETE /api/watchlist/{ticker}."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import init_db


@pytest.fixture(autouse=True)
def setup_env(tmp_path, monkeypatch):
    """Use temp DB and mock LLM for all tests."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("LLM_MOCK", "true")
    import app.database
    monkeypatch.setattr(app.database, "DB_PATH", db_path)


@pytest.fixture
async def db_ready():
    await init_db()


@pytest.fixture
def price_cache():
    """Populate the global price_cache used by main.app."""
    from app.main import price_cache
    price_cache.update("AAPL", 190.0)
    price_cache.update("GOOGL", 175.0)
    price_cache.update("MSFT", 420.0)
    price_cache.update("PYPL", 75.0)
    return price_cache


@pytest.fixture
def client_factory(db_ready, price_cache):
    """Return an async context manager for test client."""
    from app.main import app

    async def _make():
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    return _make


# --- GET /api/watchlist ---

class TestGetWatchlist:
    async def test_default_watchlist(self, client_factory):
        async with await client_factory() as client:
            resp = await client.get("/api/watchlist")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 10
        tickers = [item["ticker"] for item in data]
        assert "AAPL" in tickers
        assert "GOOGL" in tickers

    async def test_watchlist_includes_prices(self, client_factory):
        async with await client_factory() as client:
            resp = await client.get("/api/watchlist")
        data = resp.json()
        aapl = next(item for item in data if item["ticker"] == "AAPL")
        assert aapl["price"] == 190.0
        assert aapl["direction"] is not None

    async def test_watchlist_ticker_without_price(self, client_factory):
        """Tickers not in the price cache return null price fields."""
        async with await client_factory() as client:
            resp = await client.get("/api/watchlist")
        data = resp.json()
        # JPM is in default watchlist but not in our price_cache fixture
        jpm = next(item for item in data if item["ticker"] == "JPM")
        assert jpm["price"] is None
        assert jpm["direction"] is None


# --- POST /api/watchlist ---

class TestAddTicker:
    async def test_add_ticker(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/watchlist", json={"ticker": "PYPL"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["ticker"] == "PYPL"
        assert "added_at" in data

    async def test_add_ticker_appears_in_list(self, client_factory):
        async with await client_factory() as client:
            await client.post("/api/watchlist", json={"ticker": "PYPL"})
            resp = await client.get("/api/watchlist")
        tickers = [item["ticker"] for item in resp.json()]
        assert "PYPL" in tickers

    async def test_add_duplicate_ticker(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/watchlist", json={"ticker": "AAPL"})
        assert resp.status_code == 409
        assert "already in watchlist" in resp.json()["detail"]

    async def test_add_ticker_case_insensitive(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/watchlist", json={"ticker": "pypl"})
        assert resp.status_code == 201
        assert resp.json()["ticker"] == "PYPL"

    async def test_add_empty_ticker(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/watchlist", json={"ticker": ""})
        assert resp.status_code == 400


# --- DELETE /api/watchlist/{ticker} ---

class TestRemoveTicker:
    async def test_remove_ticker(self, client_factory):
        async with await client_factory() as client:
            resp = await client.delete("/api/watchlist/AAPL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["removed"] is True

    async def test_remove_ticker_gone_from_list(self, client_factory):
        async with await client_factory() as client:
            await client.delete("/api/watchlist/AAPL")
            resp = await client.get("/api/watchlist")
        tickers = [item["ticker"] for item in resp.json()]
        assert "AAPL" not in tickers
        assert len(resp.json()) == 9

    async def test_remove_nonexistent_ticker(self, client_factory):
        async with await client_factory() as client:
            resp = await client.delete("/api/watchlist/ZZZZ")
        assert resp.status_code == 404
        assert "not in watchlist" in resp.json()["detail"]

    async def test_remove_ticker_case_insensitive(self, client_factory):
        async with await client_factory() as client:
            resp = await client.delete("/api/watchlist/aapl")
        assert resp.status_code == 200
        assert resp.json()["ticker"] == "AAPL"
