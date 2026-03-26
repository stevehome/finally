"""Watchlist API endpoints."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.market import PriceCache

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class AddTickerRequest(BaseModel):
    ticker: str


def create_watchlist_router(price_cache: PriceCache) -> APIRouter:
    """Create the watchlist router with access to live prices."""

    @router.get("")
    async def get_watchlist():
        """Return current watchlist tickers with latest prices."""
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT ticker, added_at FROM watchlist WHERE user_id = ? ORDER BY added_at",
                ("default",),
            )
            rows = await cursor.fetchall()

        result = []
        for row in rows:
            ticker = row["ticker"]
            update = price_cache.get(ticker)
            entry = {
                "ticker": ticker,
                "added_at": row["added_at"],
                "price": update.price if update else None,
                "previous_price": update.previous_price if update else None,
                "change": update.change if update else None,
                "change_percent": update.change_percent if update else None,
                "direction": update.direction if update else None,
            }
            result.append(entry)
        return result

    @router.post("", status_code=201)
    async def add_ticker(req: AddTickerRequest):
        """Add a ticker to the watchlist."""
        ticker = req.ticker.upper().strip()
        if not ticker:
            raise HTTPException(status_code=400, detail="Ticker cannot be empty")

        now = datetime.now(timezone.utc).isoformat()
        async with get_db() as db:
            # Check if already in watchlist
            cursor = await db.execute(
                "SELECT id FROM watchlist WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            if await cursor.fetchone():
                raise HTTPException(status_code=409, detail=f"{ticker} already in watchlist")

            row_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                (row_id, "default", ticker, now),
            )
            await db.commit()

        # Add to market data source so prices start flowing
        from app.main import market_source
        await market_source.add_ticker(ticker)

        return {"ticker": ticker, "added_at": now}

    @router.delete("/{ticker}", status_code=200)
    async def remove_ticker(ticker: str):
        """Remove a ticker from the watchlist."""
        ticker = ticker.upper().strip()
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT id FROM watchlist WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            if not await cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"{ticker} not in watchlist")

            await db.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            await db.commit()

        # Remove from market data source
        from app.main import market_source
        await market_source.remove_ticker(ticker)

        return {"ticker": ticker, "removed": True}

    return router
