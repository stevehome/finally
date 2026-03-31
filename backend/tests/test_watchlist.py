"""Real tests for watchlist API (WATCH-01 through WATCH-05)."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from main import app


def test_get_watchlist() -> None:
    """GET /api/watchlist returns 200 with watchlist list; each item has ticker and price."""
    with TestClient(app) as client:
        response = client.get("/api/watchlist")
    assert response.status_code == 200
    data = response.json()
    assert "watchlist" in data
    watchlist = data["watchlist"]
    assert isinstance(watchlist, list)
    assert len(watchlist) == 10  # seeded with 10 default tickers
    first = watchlist[0]
    assert "ticker" in first
    assert "price" in first


def test_add_ticker() -> None:
    """POST /api/watchlist {ticker:"PYPL"} returns 201; ticker appears in subsequent GET."""
    with TestClient(app) as client:
        response = client.post("/api/watchlist", json={"ticker": "PYPL"})
        assert response.status_code == 201
        assert response.json()["ticker"] == "PYPL"

        get_response = client.get("/api/watchlist")
        assert get_response.status_code == 200
        tickers = [item["ticker"] for item in get_response.json()["watchlist"]]
        assert "PYPL" in tickers
        assert len(tickers) == 11


def test_remove_ticker() -> None:
    """DELETE /api/watchlist/AAPL returns 200; AAPL is absent from subsequent GET."""
    with TestClient(app) as client:
        response = client.delete("/api/watchlist/AAPL")
        assert response.status_code == 200
        assert response.json()["ticker"] == "AAPL"

        get_response = client.get("/api/watchlist")
        tickers = [item["ticker"] for item in get_response.json()["watchlist"]]
        assert "AAPL" not in tickers


def test_add_ticker_starts_streaming() -> None:
    """POST /api/watchlist calls source.add_ticker (verified via mock)."""
    with TestClient(app) as client:
        mock_add = AsyncMock()
        app.state.source.add_ticker = mock_add
        response = client.post("/api/watchlist", json={"ticker": "PYPL"})
        assert response.status_code == 201
        mock_add.assert_called_once_with("PYPL")


def test_remove_ticker_stops_streaming() -> None:
    """DELETE /api/watchlist/{ticker} calls source.remove_ticker (verified via mock)."""
    with TestClient(app) as client:
        mock_remove = AsyncMock()
        app.state.source.remove_ticker = mock_remove
        response = client.delete("/api/watchlist/AAPL")
        assert response.status_code == 200
        mock_remove.assert_called_once_with("AAPL")
