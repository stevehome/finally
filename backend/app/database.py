"""SQLite database initialization and connection management."""

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import aiosqlite

DB_PATH = os.environ.get("DB_PATH", "db/finally.db")

DEFAULT_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"]

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users_profile (
    id TEXT PRIMARY KEY,
    cash_balance REAL NOT NULL DEFAULT 10000.0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE(user_id, ticker)
);

CREATE TABLE IF NOT EXISTS positions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    quantity REAL NOT NULL,
    avg_cost REAL NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user_id, ticker)
);

CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    executed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    total_value REAL NOT NULL,
    recorded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    actions TEXT,
    created_at TEXT NOT NULL
);
"""


@asynccontextmanager
async def get_db(db_path: str = None):
    """Async context manager for database connections."""
    path = db_path or DB_PATH
    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def init_db(db_path: str = None):
    """Create all tables and seed default data if missing."""
    path = db_path or DB_PATH

    # Ensure directory exists
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    async with get_db(path) as db:
        await db.executescript(SCHEMA_SQL)

        # Seed default user if not present
        cursor = await db.execute("SELECT id FROM users_profile WHERE id = ?", ("default",))
        if await cursor.fetchone() is None:
            now = datetime.now(timezone.utc).isoformat()
            await db.execute(
                "INSERT INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
                ("default", 10000.0, now),
            )

        # Seed default watchlist tickers
        for ticker in DEFAULT_TICKERS:
            cursor = await db.execute(
                "SELECT id FROM watchlist WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            if await cursor.fetchone() is None:
                now = datetime.now(timezone.utc).isoformat()
                await db.execute(
                    "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                    (str(uuid.uuid4()), "default", ticker, now),
                )

        await db.commit()
