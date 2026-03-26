"""Tests for the portfolio API endpoints — GET /api/portfolio, POST /api/portfolio/trade, GET /api/portfolio/history."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import init_db, get_db
from app.market import PriceCache


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
    price_cache.update("TSLA", 250.0)
    price_cache.update("MSFT", 420.0)
    price_cache.update("NVDA", 900.0)
    return price_cache


@pytest.fixture
def client_factory(db_ready, price_cache):
    """Return an async context manager for test client."""
    from app.main import app

    async def _make():
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")

    return _make


# --- GET /api/portfolio ---

class TestGetPortfolio:
    async def test_empty_portfolio(self, client_factory):
        async with await client_factory() as client:
            resp = await client.get("/api/portfolio")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cash"] == 10000.0
        assert data["positions"] == []
        assert data["total_value"] == 10000.0
        assert data["unrealized_pnl"] == 0.0

    async def test_portfolio_with_position(self, client_factory):
        async with await client_factory() as client:
            # Buy first
            await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 10, "side": "buy"
            })
            resp = await client.get("/api/portfolio")
        data = resp.json()
        assert data["cash"] == pytest.approx(10000.0 - 190.0 * 10)
        assert len(data["positions"]) == 1
        pos = data["positions"][0]
        assert pos["ticker"] == "AAPL"
        assert pos["quantity"] == 10.0
        assert pos["avg_cost"] == 190.0
        assert pos["current_price"] == 190.0


# --- POST /api/portfolio/trade ---

class TestExecuteTrade:
    async def test_buy_success(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 5, "side": "buy"
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["side"] == "buy"
        assert data["quantity"] == 5
        assert data["price"] == 190.0
        assert data["cash_remaining"] == pytest.approx(10000.0 - 950.0)

    async def test_sell_success(self, client_factory):
        async with await client_factory() as client:
            await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 10, "side": "buy"
            })
            resp = await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 5, "side": "sell"
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["side"] == "sell"
        assert data["quantity"] == 5

    async def test_buy_insufficient_cash(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/portfolio/trade", json={
                "ticker": "NVDA", "quantity": 100, "side": "buy"
            })
        assert resp.status_code == 400
        assert "Insufficient cash" in resp.json()["detail"]

    async def test_sell_insufficient_shares(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 5, "side": "sell"
            })
        assert resp.status_code == 400
        assert "Insufficient shares" in resp.json()["detail"]

    async def test_no_price_available(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/portfolio/trade", json={
                "ticker": "ZZZZ", "quantity": 1, "side": "buy"
            })
        assert resp.status_code == 400
        assert "No price available" in resp.json()["detail"]

    async def test_invalid_side(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 1, "side": "short"
            })
        assert resp.status_code == 422  # Pydantic validation error

    async def test_invalid_quantity(self, client_factory):
        async with await client_factory() as client:
            resp = await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": -5, "side": "buy"
            })
        assert resp.status_code == 422

    async def test_sell_all_removes_position(self, client_factory):
        async with await client_factory() as client:
            await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 10, "side": "buy"
            })
            await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 10, "side": "sell"
            })
            resp = await client.get("/api/portfolio")
        data = resp.json()
        assert data["positions"] == []
        assert data["cash"] == pytest.approx(10000.0)

    async def test_buy_updates_avg_cost(self, client_factory, price_cache):
        async with await client_factory() as client:
            await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 10, "side": "buy"
            })
            # Change price
            price_cache.update("AAPL", 200.0)
            await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 10, "side": "buy"
            })
            resp = await client.get("/api/portfolio")
        pos = resp.json()["positions"][0]
        assert pos["quantity"] == 20.0
        # Avg cost = (10*190 + 10*200) / 20 = 195
        assert pos["avg_cost"] == pytest.approx(195.0)

    async def test_trade_records_snapshot(self, client_factory):
        async with await client_factory() as client:
            await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 5, "side": "buy"
            })
            resp = await client.get("/api/portfolio/history")
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["total_value"] > 0


# --- GET /api/portfolio/history ---

class TestPortfolioHistory:
    async def test_empty_history(self, client_factory):
        async with await client_factory() as client:
            resp = await client.get("/api/portfolio/history")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_history_after_trades(self, client_factory):
        async with await client_factory() as client:
            await client.post("/api/portfolio/trade", json={
                "ticker": "AAPL", "quantity": 5, "side": "buy"
            })
            await client.post("/api/portfolio/trade", json={
                "ticker": "GOOGL", "quantity": 3, "side": "buy"
            })
            resp = await client.get("/api/portfolio/history")
        data = resp.json()
        assert len(data) == 2
        # Should be chronological
        assert data[0]["recorded_at"] <= data[1]["recorded_at"]
