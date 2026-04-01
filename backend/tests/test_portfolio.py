"""Portfolio API tests: GET /api/portfolio, POST /api/portfolio/trade, GET /api/portfolio/history."""

import os
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from main import app


def test_get_portfolio() -> None:
    """GET /api/portfolio returns 200 with cash_balance, positions list, total_value."""
    with TestClient(app) as client:
        response = client.get("/api/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert "cash_balance" in data
    assert "positions" in data
    assert "total_value" in data
    assert data["cash_balance"] == pytest.approx(10000.0)
    assert data["positions"] == []
    assert data["total_value"] == pytest.approx(10000.0)


def test_buy_trade() -> None:
    """POST /api/portfolio/trade buy returns 200; cash decreases; position created."""
    with TestClient(app) as client:
        time.sleep(0.1)  # Let market simulator seed prices
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "buy"},
        )
        assert response.status_code == 200
        portfolio = client.get("/api/portfolio").json()

    assert portfolio["cash_balance"] < 10000.0
    positions = {p["ticker"]: p for p in portfolio["positions"]}
    assert "AAPL" in positions
    assert positions["AAPL"]["quantity"] == pytest.approx(1.0)


def test_sell_trade() -> None:
    """POST /api/portfolio/trade sell returns 200; cash increases; quantity decreases."""
    with TestClient(app) as client:
        time.sleep(0.1)
        # Buy 2 first so there is something to sell
        client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 2, "side": "buy"},
        )
        cash_after_buy = client.get("/api/portfolio").json()["cash_balance"]

        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "sell"},
        )
        assert response.status_code == 200
        portfolio = client.get("/api/portfolio").json()

    assert portfolio["cash_balance"] > cash_after_buy
    positions = {p["ticker"]: p for p in portfolio["positions"]}
    assert "AAPL" in positions
    assert positions["AAPL"]["quantity"] == pytest.approx(1.0)


def test_buy_insufficient_cash() -> None:
    """Buy when cash < cost returns 400, not 500."""
    with TestClient(app) as client:
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 999999, "side": "buy"},
        )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_sell_insufficient_shares() -> None:
    """Sell more shares than owned returns 400, not 500."""
    with TestClient(app) as client:
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 999999, "side": "sell"},
        )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_trade_history_recorded() -> None:
    """After a trade, the trades table has one row for that ticker."""
    db_path = os.environ["DB_PATH"]

    with TestClient(app) as client:
        time.sleep(0.1)
        client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "buy"},
        )

    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT * FROM trades WHERE ticker = 'AAPL' AND user_id = 'default'"
    ).fetchall()
    conn.close()
    assert len(rows) == 1


def test_snapshot_after_trade() -> None:
    """After a trade, portfolio_snapshots table has at least one row."""
    db_path = os.environ["DB_PATH"]

    with TestClient(app) as client:
        time.sleep(0.1)
        client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "buy"},
        )

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT * FROM portfolio_snapshots WHERE user_id = 'default'").fetchall()
    conn.close()
    assert len(rows) >= 1


def test_snapshot_background_task() -> None:
    """record_snapshot is importable and inserts a row into portfolio_snapshots."""
    from app.db import init_db
    from app.market import PriceCache
    from app.routers.portfolio import record_snapshot

    db_path = os.environ["DB_PATH"]
    init_db()

    cache = PriceCache()
    cache.update("AAPL", 150.0)
    record_snapshot(cache)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT * FROM portfolio_snapshots WHERE user_id = 'default'").fetchall()
    conn.close()
    assert len(rows) == 1


def test_portfolio_history() -> None:
    """GET /api/portfolio/history returns 200 with a snapshots list."""
    with TestClient(app) as client:
        time.sleep(0.1)
        # Trigger a snapshot via trade
        client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "buy"},
        )
        response = client.get("/api/portfolio/history")

    assert response.status_code == 200
    data = response.json()
    assert "snapshots" in data
    snapshots = data["snapshots"]
    assert isinstance(snapshots, list)
    assert len(snapshots) >= 1
    assert "total_value" in snapshots[0]
    assert "recorded_at" in snapshots[0]


def test_sell_all_shares_removes_position() -> None:
    """Selling all shares of a ticker removes the position row entirely."""
    with TestClient(app) as client:
        time.sleep(0.1)
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "sell"})
        portfolio = client.get("/api/portfolio").json()

    assert portfolio["positions"] == []


def test_buy_updates_avg_cost() -> None:
    """Second buy of same ticker updates avg_cost to weighted average."""
    with TestClient(app) as client:
        time.sleep(0.1)
        # Buy 1 share, record price
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})
        p1 = client.get("/api/portfolio").json()
        cost1 = p1["positions"][0]["avg_cost"]
        cash1 = p1["cash_balance"]

        # Buy 1 more share at (possibly) same simulator price
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})
        p2 = client.get("/api/portfolio").json()
        cost2 = p2["positions"][0]["avg_cost"]
        cash2 = p2["cash_balance"]

    # avg_cost should be the average of the two purchase prices
    price_of_second_buy = (10000.0 - cash2) - (10000.0 - cash1)
    expected_avg = (cost1 + price_of_second_buy) / 2
    assert cost2 == pytest.approx(expected_avg, rel=1e-4)
    assert p2["positions"][0]["quantity"] == pytest.approx(2.0)


def test_buy_fractional_shares() -> None:
    """Buy 0.5 shares — quantity shows 0.5 in portfolio."""
    with TestClient(app) as client:
        time.sleep(0.1)
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 0.5, "side": "buy"},
        )
        assert response.status_code == 200
        portfolio = client.get("/api/portfolio").json()

    positions = {p["ticker"]: p for p in portfolio["positions"]}
    assert "AAPL" in positions
    assert positions["AAPL"]["quantity"] == pytest.approx(0.5)


def test_sell_fractional_shares() -> None:
    """Buy 1.0 then sell 0.5 — quantity shows 0.5 remaining."""
    with TestClient(app) as client:
        time.sleep(0.1)
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1.0, "side": "buy"})
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 0.5, "side": "sell"})
        portfolio = client.get("/api/portfolio").json()

    positions = {p["ticker"]: p for p in portfolio["positions"]}
    assert "AAPL" in positions
    assert positions["AAPL"]["quantity"] == pytest.approx(0.5)


def test_invalid_trade_side_returns_400() -> None:
    """Trade with side='hold' (invalid) returns HTTP 400."""
    with TestClient(app) as client:
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "hold"},
        )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_trade_response_shape() -> None:
    """Successful buy response contains status, ticker, side, quantity, price fields."""
    with TestClient(app) as client:
        time.sleep(0.1)
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "buy"},
        )
    assert response.status_code == 200
    data = response.json()
    for field in ("status", "ticker", "side", "quantity", "price"):
        assert field in data, f"Missing field: {field}"


def test_portfolio_positions_shape() -> None:
    """Each position in GET /api/portfolio has all required fields."""
    with TestClient(app) as client:
        time.sleep(0.1)
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})
        portfolio = client.get("/api/portfolio").json()

    assert len(portfolio["positions"]) == 1
    pos = portfolio["positions"][0]
    for field in ("ticker", "quantity", "avg_cost", "current_price", "unrealized_pnl", "value"):
        assert field in pos, f"Missing position field: {field}"


def test_portfolio_history_empty() -> None:
    """Fresh DB with no trades returns snapshots=[] from GET /api/portfolio/history."""
    with TestClient(app) as client:
        response = client.get("/api/portfolio/history")
    assert response.status_code == 200
    data = response.json()
    assert "snapshots" in data
    assert data["snapshots"] == []
