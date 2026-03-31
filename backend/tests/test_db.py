"""Unit tests for database initialization, schema, and seed data."""

import sqlite3

from app.db import get_connection, get_watchlist_tickers, init_db


def test_init_creates_db_file(tmp_db):
    """init_db() creates the SQLite file at the configured DB_PATH."""
    import os

    assert not os.path.exists(tmp_db)
    init_db()
    assert os.path.exists(tmp_db)


def test_init_creates_all_tables(tmp_db):
    """After init_db(), all 6 schema tables exist in the database."""
    init_db()
    conn = sqlite3.connect(tmp_db)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()

    expected = {
        "users_profile",
        "watchlist",
        "positions",
        "trades",
        "portfolio_snapshots",
        "chat_messages",
    }
    assert expected == tables


def test_init_is_idempotent(tmp_db):
    """Calling init_db() twice does not raise and tables still exist."""
    init_db()
    init_db()  # Should not raise

    conn = sqlite3.connect(tmp_db)
    cursor = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
    count = cursor.fetchone()[0]
    conn.close()
    assert count == 6


def test_seed_user_profile(tmp_db):
    """After init_db(), users_profile has id='default' with cash_balance=10000.0."""
    init_db()
    conn = sqlite3.connect(tmp_db)
    cursor = conn.execute("SELECT id, cash_balance FROM users_profile WHERE id = 'default'")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "default"
    assert row[1] == 10000.0


def test_seed_watchlist(tmp_db):
    """After init_db(), watchlist has 10 rows for user_id='default' with the expected tickers."""
    init_db()
    conn = sqlite3.connect(tmp_db)
    cursor = conn.execute(
        "SELECT ticker FROM watchlist WHERE user_id = 'default' ORDER BY added_at"
    )
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert len(tickers) == 10
    expected = {"AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"}
    assert set(tickers) == expected


def test_get_watchlist_tickers(tmp_db):
    """get_watchlist_tickers() returns a list of 10 ticker strings."""
    init_db()
    tickers = get_watchlist_tickers()
    assert isinstance(tickers, list)
    assert len(tickers) == 10
    assert all(isinstance(t, str) for t in tickers)
    expected = {"AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"}
    assert set(tickers) == expected


def test_get_connection_row_factory(tmp_db):
    """get_connection() returns a connection with row_factory=sqlite3.Row."""
    init_db()
    conn = get_connection()
    assert conn.row_factory is sqlite3.Row
    conn.close()
