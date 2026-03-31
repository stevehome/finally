"""Failing test stubs for portfolio API (PORT-01 through PORT-08).

Each test is marked xfail(strict=True) — RED phase before router implementation.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.xfail(reason="PORT-01: portfolio router not implemented", strict=True)
def test_get_portfolio() -> None:
    """GET /api/portfolio returns 200 with cash_balance, positions list, total_value."""
    with TestClient(app) as client:
        response = client.get("/api/portfolio")
    assert response.status_code == 200
    data = response.json()
    assert "cash_balance" in data
    assert "positions" in data
    assert "total_value" in data


@pytest.mark.xfail(reason="PORT-02: portfolio router not implemented", strict=True)
def test_buy_trade() -> None:
    """POST /api/portfolio/trade buy returns 200; cash decreases; position created."""
    with TestClient(app) as client:
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 1, "side": "buy"},
        )
        assert response.status_code == 200
        portfolio = client.get("/api/portfolio").json()
    assert portfolio["cash_balance"] < 10000.0
    positions = {p["ticker"]: p for p in portfolio["positions"]}
    assert "AAPL" in positions
    assert positions["AAPL"]["quantity"] > 0


@pytest.mark.xfail(reason="PORT-03: portfolio router not implemented", strict=True)
def test_sell_trade() -> None:
    """POST /api/portfolio/trade sell returns 200; cash increases; quantity decreases."""
    with TestClient(app) as client:
        # Buy first so there is something to sell
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


@pytest.mark.xfail(reason="PORT-04: portfolio router not implemented", strict=True)
def test_buy_insufficient_cash() -> None:
    """Buy when cash < cost returns 400, not 500."""
    with TestClient(app) as client:
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 999999, "side": "buy"},
        )
    assert response.status_code == 400


@pytest.mark.xfail(reason="PORT-05: portfolio router not implemented", strict=True)
def test_sell_insufficient_shares() -> None:
    """Sell more shares than owned returns 400, not 500."""
    with TestClient(app) as client:
        response = client.post(
            "/api/portfolio/trade",
            json={"ticker": "AAPL", "quantity": 999999, "side": "sell"},
        )
    assert response.status_code == 400


@pytest.mark.xfail(reason="PORT-06: portfolio router not implemented", strict=True)
def test_trade_history_recorded() -> None:
    """After a trade, the trades table has one row for that ticker."""
    import sqlite3
    import os

    db_path = os.environ["DB_PATH"]

    with TestClient(app) as client:
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


@pytest.mark.xfail(reason="PORT-07: portfolio router not implemented", strict=True)
def test_snapshot_after_trade() -> None:
    """After a trade, portfolio_snapshots table has at least one row."""
    import sqlite3
    import os

    db_path = os.environ["DB_PATH"]

    with TestClient(app) as client:
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


@pytest.mark.xfail(reason="PORT-08: snapshot background task not implemented", strict=True)
def test_snapshot_background_task() -> None:
    """Snapshot loop function records a snapshot row when called."""
    try:
        from app.routers.portfolio import record_snapshot  # noqa: F401
    except ImportError:
        pytest.fail("record_snapshot not importable from app.routers.portfolio")


@pytest.mark.xfail(reason="PORT-08: portfolio history router not implemented", strict=True)
def test_portfolio_history() -> None:
    """GET /api/portfolio/history returns 200 with a list of snapshots."""
    with TestClient(app) as client:
        response = client.get("/api/portfolio/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
