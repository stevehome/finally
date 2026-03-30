"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def event_loop_policy():
    """Use the default event loop policy for all async tests."""
    import asyncio

    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Redirect DB_PATH to a temp file so tests never touch db/finally.db."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    import importlib

    try:
        import app.db as db_mod

        monkeypatch.setattr(db_mod, "DB_PATH", db_file)
    except ImportError:
        pass
    yield db_file
    importlib.invalidate_caches()
