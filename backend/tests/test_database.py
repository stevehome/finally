"""Tests for database initialization and schema."""

import os
import tempfile

import pytest

from app.database import DEFAULT_TICKERS, get_db, init_db


@pytest.fixture
async def db_path():
    """Provide a temporary database path, cleaned up after test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, "test.db")


async def test_tables_created(db_path):
    """All expected tables exist after init_db."""
    await init_db(db_path)

    expected_tables = {
        "users_profile",
        "watchlist",
        "positions",
        "trades",
        "portfolio_snapshots",
        "chat_messages",
    }

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        rows = await cursor.fetchall()
        table_names = {row[0] for row in rows}

    assert table_names == expected_tables


async def test_default_user_seeded(db_path):
    """Default user exists with $10,000 cash balance."""
    await init_db(db_path)

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT id, cash_balance FROM users_profile WHERE id = ?", ("default",))
        row = await cursor.fetchone()

    assert row is not None
    assert row[0] == "default"
    assert row[1] == 10000.0


async def test_default_watchlist_seeded(db_path):
    """All 10 default tickers are in the watchlist."""
    await init_db(db_path)

    async with get_db(db_path) as db:
        cursor = await db.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY ticker", ("default",)
        )
        rows = await cursor.fetchall()
        tickers = [row[0] for row in rows]

    assert sorted(tickers) == sorted(DEFAULT_TICKERS)


async def test_idempotent(db_path):
    """Calling init_db twice does not duplicate data or error."""
    await init_db(db_path)
    await init_db(db_path)

    async with get_db(db_path) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM users_profile")
        row = await cursor.fetchone()
        assert row[0] == 1

        cursor = await db.execute("SELECT COUNT(*) FROM watchlist WHERE user_id = ?", ("default",))
        row = await cursor.fetchone()
        assert row[0] == len(DEFAULT_TICKERS)
