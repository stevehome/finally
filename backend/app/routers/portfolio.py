"""Portfolio router: GET /api/portfolio, POST /api/portfolio/trade, GET /api/portfolio/history."""

import logging
import sqlite3
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.db import get_connection
from app.market import PriceCache

logger = logging.getLogger(__name__)
router = APIRouter(tags=["portfolio"])


class TradeRequest(BaseModel):
    """Incoming trade request body."""

    ticker: str
    quantity: float
    side: str


# --- Public API ---


def record_snapshot(price_cache: PriceCache, user_id: str = "default") -> None:
    """Compute current portfolio value and insert a row into portfolio_snapshots.

    total_value = cash_balance + sum(quantity * current_price) for all positions.
    Falls back to avg_cost when a ticker is not in the price cache.
    """
    conn = get_connection()
    try:
        profile = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)
        ).fetchone()
        if profile is None:
            return
        cash = profile["cash_balance"]

        positions = conn.execute(
            "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ?", (user_id,)
        ).fetchall()

        total_value = cash
        for pos in positions:
            price = price_cache.get_price(pos["ticker"])
            if price is None:
                price = pos["avg_cost"]
            total_value += pos["quantity"] * price

        conn.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), user_id, total_value, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


@router.get("/portfolio")
async def get_portfolio(request: Request) -> dict:
    """Return cash balance, current positions with live P&L, and total portfolio value."""
    price_cache: PriceCache = request.app.state.price_cache
    user_id = "default"

    conn = get_connection()
    try:
        profile = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)
        ).fetchone()
        cash = profile["cash_balance"] if profile else 10000.0

        rows = conn.execute(
            "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ? ORDER BY ticker",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    positions = []
    positions_value = 0.0
    for row in rows:
        ticker = row["ticker"]
        quantity = row["quantity"]
        avg_cost = row["avg_cost"]
        current_price = price_cache.get_price(ticker)
        if current_price is None:
            current_price = avg_cost
        value = quantity * current_price
        unrealized_pnl = (current_price - avg_cost) * quantity
        positions.append(
            {
                "ticker": ticker,
                "quantity": quantity,
                "avg_cost": avg_cost,
                "current_price": current_price,
                "unrealized_pnl": unrealized_pnl,
                "value": value,
            }
        )
        positions_value += value

    total_value = cash + positions_value
    return {"cash_balance": cash, "positions": positions, "total_value": total_value}


@router.post("/portfolio/trade")
async def execute_trade(request: Request, trade: TradeRequest) -> dict:
    """Execute a market order — buy or sell at the current cached price.

    Validates sufficient cash (buy) or sufficient shares (sell) before any mutation.
    All DB changes run in a single atomic transaction.
    After success, records a portfolio snapshot.
    """
    price_cache: PriceCache = request.app.state.price_cache
    user_id = "default"
    ticker = trade.ticker.upper()
    quantity = trade.quantity
    side = trade.side.lower()

    current_price = price_cache.get_price(ticker)

    conn = get_connection()
    try:
        conn.execute("BEGIN")

        profile = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)
        ).fetchone()
        if profile is None:
            conn.rollback()
            raise HTTPException(status_code=500, detail="User profile not found")
        cash = profile["cash_balance"]

        position = conn.execute(
            "SELECT id, quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
            (user_id, ticker),
        ).fetchone()

        if current_price is None:
            # Fall back to avg_cost if no price cached yet
            current_price = position["avg_cost"] if position else 0.0

        if side == "buy":
            cost = quantity * current_price
            if cash < cost:
                conn.rollback()
                raise HTTPException(status_code=400, detail="Insufficient cash")

            new_cash = cash - cost
            conn.execute(
                "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
                (new_cash, user_id),
            )

            if position is None:
                conn.execute(
                    "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        user_id,
                        ticker,
                        quantity,
                        current_price,
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
            else:
                old_qty = position["quantity"]
                old_avg = position["avg_cost"]
                new_qty = old_qty + quantity
                new_avg = (old_qty * old_avg + quantity * current_price) / new_qty
                conn.execute(
                    "UPDATE positions SET quantity = ?, avg_cost = ?, updated_at = ? "
                    "WHERE user_id = ? AND ticker = ?",
                    (new_qty, new_avg, datetime.now(timezone.utc).isoformat(), user_id, ticker),
                )

        elif side == "sell":
            owned = position["quantity"] if position else 0.0
            if owned < quantity:
                conn.rollback()
                raise HTTPException(status_code=400, detail="Insufficient shares")

            proceeds = quantity * current_price
            new_cash = cash + proceeds
            conn.execute(
                "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
                (new_cash, user_id),
            )

            new_qty = owned - quantity
            if new_qty == 0:
                conn.execute(
                    "DELETE FROM positions WHERE user_id = ? AND ticker = ?",
                    (user_id, ticker),
                )
            else:
                conn.execute(
                    "UPDATE positions SET quantity = ?, updated_at = ? "
                    "WHERE user_id = ? AND ticker = ?",
                    (new_qty, datetime.now(timezone.utc).isoformat(), user_id, ticker),
                )
        else:
            conn.rollback()
            raise HTTPException(status_code=400, detail="Invalid side — must be 'buy' or 'sell'")

        # Record the trade
        conn.execute(
            "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                user_id,
                ticker,
                side,
                quantity,
                current_price,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    except HTTPException:
        raise
    except sqlite3.Error:
        conn.rollback()
        logger.exception("DB error during trade execution for %s", ticker)
        raise HTTPException(status_code=500, detail="Database error")
    finally:
        conn.close()

    # Record snapshot outside the trade transaction — non-fatal if it fails
    try:
        record_snapshot(price_cache, user_id)
    except Exception:
        logger.exception("Failed to record snapshot after trade")

    return {
        "status": "ok",
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price": current_price,
    }


@router.get("/portfolio/history")
async def get_portfolio_history(request: Request) -> dict:
    """Return all portfolio value snapshots ordered by recorded_at."""
    user_id = "default"
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT total_value, recorded_at FROM portfolio_snapshots "
            "WHERE user_id = ? ORDER BY recorded_at",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    snapshots = [{"total_value": r["total_value"], "recorded_at": r["recorded_at"]} for r in rows]
    return {"snapshots": snapshots}
