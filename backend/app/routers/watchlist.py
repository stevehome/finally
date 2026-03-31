"""Watchlist router: GET /api/watchlist, POST /api/watchlist, DELETE /api/watchlist/{ticker}."""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db import get_connection

logger = logging.getLogger(__name__)
router = APIRouter(tags=["watchlist"])


class WatchlistAddRequest(BaseModel):
    """Request body for adding a ticker to the watchlist."""

    ticker: str


# --- Public API ---


@router.get("/watchlist")
async def get_watchlist(request: Request) -> dict:
    """Return all watchlist tickers for the default user with their current prices."""
    user_id = "default"
    price_cache = request.app.state.price_cache

    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    watchlist = [
        {"ticker": row["ticker"], "price": price_cache.get_price(row["ticker"])} for row in rows
    ]
    return {"watchlist": watchlist}


@router.post("/watchlist", status_code=201)
async def add_ticker(request: Request, body: WatchlistAddRequest) -> dict:
    """Add a ticker to the watchlist (idempotent) and start streaming its price.

    Uses INSERT OR IGNORE so adding a duplicate ticker never errors.
    Always calls source.add_ticker so the market data source stays in sync.
    """
    user_id = "default"
    ticker = body.ticker.upper()
    source = request.app.state.source

    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, ticker, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    await source.add_ticker(ticker)
    logger.info("Added %s to watchlist", ticker)
    return {"ticker": ticker}


@router.delete("/watchlist/{ticker}")
async def remove_ticker(request: Request, ticker: str) -> dict:
    """Remove a ticker from the watchlist and stop streaming its price.

    Returns 404 if the ticker is not in the watchlist.
    """
    user_id = "default"
    ticker = ticker.upper()
    source = request.app.state.source

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not in watchlist")

        conn.execute(
            "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        )
        conn.commit()
    finally:
        conn.close()

    await source.remove_ticker(ticker)
    logger.info("Removed %s from watchlist", ticker)
    return {"ticker": ticker}
