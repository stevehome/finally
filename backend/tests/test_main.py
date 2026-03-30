"""Integration tests for FastAPI app startup, health endpoint, and SSE stream."""

import os

import pytest
from fastapi.testclient import TestClient

from main import app


def test_health_returns_200(tmp_db):
    """GET /api/health returns 200 with expected JSON body."""
    with TestClient(app) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "db": "ok", "market_data": "running"}


def test_app_starts_and_has_routes(tmp_db):
    """TestClient(app) initializes without error and expected routes exist."""
    with TestClient(app) as client:
        # Verify app started cleanly by hitting health
        response = client.get("/api/health")
        assert response.status_code == 200

    # Check routes exist on the app
    routes = {route.path for route in app.routes}
    assert "/api/health" in routes
    assert "/api/stream/prices" in routes


def test_lifespan_initializes_db(tmp_db):
    """After app startup, the database file exists and has the expected tables."""
    with TestClient(app):
        # DB should be initialized during lifespan startup
        assert os.path.exists(tmp_db)

        import sqlite3

        conn = sqlite3.connect(tmp_db)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()

    expected_tables = {
        "users_profile",
        "watchlist",
        "positions",
        "trades",
        "portfolio_snapshots",
        "chat_messages",
    }
    assert expected_tables.issubset(tables)


def test_sse_stream_returns_event_stream(tmp_db):
    """GET /api/stream/prices returns content-type text/event-stream."""
    with TestClient(app) as client:
        with client.stream("GET", "/api/stream/prices") as response:
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type
