"""Failing test stubs for watchlist API (WATCH-01 through WATCH-05).

Each test is marked xfail(strict=True) — RED phase before router implementation.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.mark.xfail(reason="WATCH-01: watchlist router not implemented", strict=True)
def test_get_watchlist() -> None:
    """GET /api/watchlist returns 200 with a list of objects each containing ticker and price."""
    with TestClient(app) as client:
        response = client.get("/api/watchlist")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "ticker" in first
    assert "price" in first


@pytest.mark.xfail(reason="WATCH-02: watchlist router not implemented", strict=True)
def test_add_ticker() -> None:
    """POST /api/watchlist {ticker:"PYPL"} returns 201; ticker appears in subsequent GET."""
    with TestClient(app) as client:
        response = client.post("/api/watchlist", json={"ticker": "PYPL"})
        assert response.status_code == 201

        get_response = client.get("/api/watchlist")
        assert get_response.status_code == 200
        tickers = [item["ticker"] for item in get_response.json()]
    assert "PYPL" in tickers


@pytest.mark.xfail(reason="WATCH-03: watchlist router not implemented", strict=True)
def test_remove_ticker() -> None:
    """DELETE /api/watchlist/AAPL returns 200 or 204; ticker gone from GET."""
    with TestClient(app) as client:
        response = client.delete("/api/watchlist/AAPL")
        assert response.status_code in (200, 204)

        get_response = client.get("/api/watchlist")
        tickers = [item["ticker"] for item in get_response.json()]
    assert "AAPL" not in tickers


@pytest.mark.xfail(reason="WATCH-04: watchlist router / source integration not implemented", strict=True)
def test_add_ticker_starts_streaming() -> None:
    """POST /api/watchlist calls source.add_ticker (verified via mock)."""
    try:
        from app.routers.watchlist import router  # noqa: F401
    except ImportError:
        pytest.fail("app.routers.watchlist not importable")


@pytest.mark.xfail(reason="WATCH-05: watchlist router / source integration not implemented", strict=True)
def test_remove_ticker_stops_streaming() -> None:
    """DELETE /api/watchlist/{ticker} calls source.remove_ticker (verified via mock)."""
    try:
        from app.routers.watchlist import router  # noqa: F401
    except ImportError:
        pytest.fail("app.routers.watchlist not importable")
