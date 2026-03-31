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
    rows = conn.execute(
        "SELECT * FROM portfolio_snapshots WHERE user_id = 'default'"
    ).fetchall()
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
