"""Tests for the chat router — mock mode, structured output parsing, trade execution."""

import os
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import init_db, get_db, DB_PATH
from app.market import PriceCache
from app.routers.chat import (
    ChatResponse,
    TradeAction,
    WatchlistChange,
    _execute_trade,
    _execute_watchlist_change,
    _mock_response,
)


@pytest.fixture(autouse=True)
def mock_env(tmp_path, monkeypatch):
    """Use a temp DB and enable mock mode for all tests."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_path)
    monkeypatch.setenv("LLM_MOCK", "true")
    # Patch the module-level DB_PATH
    import app.database
    monkeypatch.setattr(app.database, "DB_PATH", db_path)


@pytest.fixture
async def db_ready():
    """Initialize DB before tests."""
    await init_db()


@pytest.fixture
def price_cache():
    cache = PriceCache()
    cache.update("AAPL", 190.0)
    cache.update("GOOGL", 175.0)
    cache.update("TSLA", 250.0)
    cache.update("MSFT", 420.0)
    cache.update("NVDA", 900.0)
    return cache


# --- Mock response tests ---

class TestMockResponse:
    def test_generic_message(self):
        resp = _mock_response("hello")
        assert isinstance(resp, ChatResponse)
        assert resp.message
        assert resp.trades == []
        assert resp.watchlist_changes == []

    def test_buy_order(self):
        resp = _mock_response("buy 5 AAPL")
        assert len(resp.trades) == 1
        assert resp.trades[0].ticker == "AAPL"
        assert resp.trades[0].side == "buy"
        assert resp.trades[0].quantity == 5.0

    def test_sell_order(self):
        resp = _mock_response("sell 10 TSLA")
        assert len(resp.trades) == 1
        assert resp.trades[0].ticker == "TSLA"
        assert resp.trades[0].side == "sell"
        assert resp.trades[0].quantity == 10.0

    def test_add_watchlist(self):
        resp = _mock_response("add PYPL to watchlist")
        assert len(resp.watchlist_changes) == 1
        assert resp.watchlist_changes[0].ticker == "PYPL"
        assert resp.watchlist_changes[0].action == "add"

    def test_remove_watchlist(self):
        resp = _mock_response("remove TSLA from watchlist")
        assert len(resp.watchlist_changes) == 1
        assert resp.watchlist_changes[0].action == "remove"


# --- Structured output parsing tests ---

class TestStructuredOutput:
    def test_minimal_response(self):
        data = '{"message": "hello"}'
        resp = ChatResponse.model_validate_json(data)
        assert resp.message == "hello"
        assert resp.trades == []
        assert resp.watchlist_changes == []

    def test_full_response(self):
        data = '''{
            "message": "Buying AAPL",
            "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}],
            "watchlist_changes": [{"ticker": "PYPL", "action": "add"}]
        }'''
        resp = ChatResponse.model_validate_json(data)
        assert resp.message == "Buying AAPL"
        assert len(resp.trades) == 1
        assert resp.trades[0].quantity == 10
        assert len(resp.watchlist_changes) == 1

    def test_multiple_trades(self):
        data = '''{
            "message": "Diversifying",
            "trades": [
                {"ticker": "AAPL", "side": "buy", "quantity": 5},
                {"ticker": "TSLA", "side": "sell", "quantity": 3}
            ]
        }'''
        resp = ChatResponse.model_validate_json(data)
        assert len(resp.trades) == 2

    def test_empty_arrays(self):
        data = '{"message": "ok", "trades": [], "watchlist_changes": []}'
        resp = ChatResponse.model_validate_json(data)
        assert resp.trades == []
        assert resp.watchlist_changes == []


# --- Trade execution tests ---

class TestTradeExecution:
    async def test_buy_success(self, db_ready, price_cache):
        trade = TradeAction(ticker="AAPL", side="buy", quantity=10)
        result = await _execute_trade(trade, price_cache)
        assert result["success"] is True
        assert result["price"] == 190.0

        # Verify cash deducted
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT cash_balance FROM users_profile WHERE id = ?", ("default",)
            )
            row = await cursor.fetchone()
            assert row["cash_balance"] == pytest.approx(10000.0 - 190.0 * 10)

    async def test_buy_insufficient_cash(self, db_ready, price_cache):
        trade = TradeAction(ticker="NVDA", side="buy", quantity=100)
        result = await _execute_trade(trade, price_cache)
        assert result["success"] is False
        assert "Insufficient cash" in result["error"]

    async def test_sell_no_position(self, db_ready, price_cache):
        trade = TradeAction(ticker="AAPL", side="sell", quantity=5)
        result = await _execute_trade(trade, price_cache)
        assert result["success"] is False
        assert "Insufficient shares" in result["error"]

    async def test_sell_success(self, db_ready, price_cache):
        # First buy
        buy = TradeAction(ticker="AAPL", side="buy", quantity=10)
        await _execute_trade(buy, price_cache)

        # Then sell
        sell = TradeAction(ticker="AAPL", side="sell", quantity=5)
        result = await _execute_trade(sell, price_cache)
        assert result["success"] is True

        # Verify position updated
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT quantity FROM positions WHERE user_id = ? AND ticker = ?",
                ("default", "AAPL"),
            )
            row = await cursor.fetchone()
            assert row["quantity"] == pytest.approx(5.0)

    async def test_sell_all_removes_position(self, db_ready, price_cache):
        buy = TradeAction(ticker="AAPL", side="buy", quantity=10)
        await _execute_trade(buy, price_cache)

        sell = TradeAction(ticker="AAPL", side="sell", quantity=10)
        result = await _execute_trade(sell, price_cache)
        assert result["success"] is True

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT quantity FROM positions WHERE user_id = ? AND ticker = ?",
                ("default", "AAPL"),
            )
            row = await cursor.fetchone()
            assert row is None

    async def test_no_price_available(self, db_ready, price_cache):
        trade = TradeAction(ticker="UNKNOWN", side="buy", quantity=1)
        result = await _execute_trade(trade, price_cache)
        assert result["success"] is False
        assert "No price available" in result["error"]

    async def test_invalid_quantity(self, db_ready, price_cache):
        trade = TradeAction(ticker="AAPL", side="buy", quantity=0)
        result = await _execute_trade(trade, price_cache)
        assert result["success"] is False

    async def test_trade_recorded(self, db_ready, price_cache):
        trade = TradeAction(ticker="AAPL", side="buy", quantity=5)
        await _execute_trade(trade, price_cache)

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM trades WHERE user_id = ? AND ticker = ?",
                ("default", "AAPL"),
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row["side"] == "buy"
            assert row["quantity"] == 5.0

    async def test_portfolio_snapshot_recorded(self, db_ready, price_cache):
        trade = TradeAction(ticker="AAPL", side="buy", quantity=5)
        await _execute_trade(trade, price_cache)

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM portfolio_snapshots WHERE user_id = ?", ("default",)
            )
            row = await cursor.fetchone()
            assert row is not None
            assert row["total_value"] > 0


# --- Watchlist change tests ---

class TestWatchlistExecution:
    async def test_add_ticker(self, db_ready):
        change = WatchlistChange(ticker="PYPL", action="add")
        result = await _execute_watchlist_change(change)
        assert result["success"] is True

    async def test_add_duplicate(self, db_ready):
        change = WatchlistChange(ticker="AAPL", action="add")
        # AAPL is in default seed data
        result = await _execute_watchlist_change(change)
        assert result["success"] is True
        assert "Already" in result.get("note", "")

    async def test_remove_ticker(self, db_ready):
        change = WatchlistChange(ticker="AAPL", action="remove")
        result = await _execute_watchlist_change(change)
        assert result["success"] is True

    async def test_remove_nonexistent(self, db_ready):
        change = WatchlistChange(ticker="ZZZZ", action="remove")
        result = await _execute_watchlist_change(change)
        assert result["success"] is False


# --- Full endpoint integration test ---

class TestChatEndpoint:
    async def test_chat_mock_mode(self, db_ready, price_cache, monkeypatch):
        # Import here to get the app after DB_PATH is patched
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/chat", json={"message": "hello"})

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert isinstance(data["trades"], list)
        assert isinstance(data["watchlist_changes"], list)

    async def test_chat_stores_messages(self, db_ready, price_cache, monkeypatch):
        from app.main import app

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await client.post("/api/chat", json={"message": "hello"})

        async with get_db() as db:
            cursor = await db.execute(
                "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY created_at",
                ("default",),
            )
            rows = await cursor.fetchall()
            assert len(rows) == 2
            assert rows[0]["role"] == "user"
            assert rows[1]["role"] == "assistant"
