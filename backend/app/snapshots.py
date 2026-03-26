"""Background task that records portfolio value snapshots every 30 seconds."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.market import PriceCache

logger = logging.getLogger(__name__)

SNAPSHOT_INTERVAL = 30  # seconds


async def snapshot_loop(price_cache: PriceCache):
    """Periodically record total portfolio value for the P&L chart."""
    while True:
        await asyncio.sleep(SNAPSHOT_INTERVAL)
        try:
            await record_snapshot(price_cache)
        except Exception:
            logger.exception("Failed to record portfolio snapshot")


async def record_snapshot(price_cache: PriceCache):
    """Calculate and store current total portfolio value."""
    async with get_db() as db:
        # Cash
        cursor = await db.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", ("default",)
        )
        user = await cursor.fetchone()
        cash = user["cash_balance"] if user else 10000.0

        # Positions market value
        cursor = await db.execute(
            "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ? AND quantity > 0",
            ("default",),
        )
        rows = await cursor.fetchall()
        market_value = sum(
            row["quantity"] * (price_cache.get_price(row["ticker"]) or row["avg_cost"])
            for row in rows
        )

        total_value = cash + market_value
        now = datetime.now(timezone.utc).isoformat()

        await db.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), "default", total_value, now),
        )
        await db.commit()
