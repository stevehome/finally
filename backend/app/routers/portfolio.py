"""Portfolio API endpoints — positions, trading, and history."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

from app.database import get_db
from app.market import PriceCache

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


class TradeRequest(BaseModel):
    ticker: str
    quantity: float
    side: str

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        return v

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v


def create_portfolio_router(price_cache: PriceCache) -> APIRouter:
    """Create the portfolio router with access to live prices."""

    @router.get("")
    async def get_portfolio():
        """Return current positions, cash balance, total value, and unrealized P&L."""
        async with get_db() as db:
            # Get cash balance
            cursor = await db.execute(
                "SELECT cash_balance FROM users_profile WHERE id = ?", ("default",)
            )
            user = await cursor.fetchone()
            cash = user["cash_balance"] if user else 10000.0

            # Get positions
            cursor = await db.execute(
                "SELECT ticker, quantity, avg_cost, updated_at FROM positions WHERE user_id = ? AND quantity > 0",
                ("default",),
            )
            rows = await cursor.fetchall()

        positions = []
        total_market_value = 0.0
        total_unrealized_pnl = 0.0

        for row in rows:
            ticker = row["ticker"]
            qty = row["quantity"]
            avg_cost = row["avg_cost"]
            current_price = price_cache.get_price(ticker) or avg_cost
            market_value = qty * current_price
            cost_basis = qty * avg_cost
            unrealized_pnl = market_value - cost_basis
            pnl_percent = ((current_price - avg_cost) / avg_cost * 100) if avg_cost > 0 else 0.0

            total_market_value += market_value
            total_unrealized_pnl += unrealized_pnl

            positions.append({
                "ticker": ticker,
                "quantity": qty,
                "avg_cost": round(avg_cost, 2),
                "current_price": round(current_price, 2),
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2),
                "pnl_percent": round(pnl_percent, 2),
                "updated_at": row["updated_at"],
            })

        total_value = cash + total_market_value

        # Add weight (fraction of total portfolio) per position
        for p in positions:
            p["weight"] = round(p["market_value"] / total_value, 4) if total_value > 0 else 0

        return {
            "cash": round(cash, 2),
            "cash_balance": round(cash, 2),
            "positions": positions,
            "total_market_value": round(total_market_value, 2),
            "total_value": round(total_value, 2),
            "unrealized_pnl": round(total_unrealized_pnl, 2),
        }

    @router.post("/trade")
    async def execute_trade(req: TradeRequest):
        """Execute a market order trade at current price."""
        ticker = req.ticker.upper().strip()
        quantity = req.quantity
        side = req.side

        # Get current price
        current_price = price_cache.get_price(ticker)
        if current_price is None:
            raise HTTPException(status_code=400, detail=f"No price available for {ticker}")

        now = datetime.now(timezone.utc).isoformat()
        trade_cost = quantity * current_price

        async with get_db() as db:
            # Get cash balance
            cursor = await db.execute(
                "SELECT cash_balance FROM users_profile WHERE id = ?", ("default",)
            )
            user = await cursor.fetchone()
            cash = user["cash_balance"]

            # Get existing position
            cursor = await db.execute(
                "SELECT quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            position = await cursor.fetchone()
            existing_qty = position["quantity"] if position else 0.0
            existing_avg_cost = position["avg_cost"] if position else 0.0

            if side == "buy":
                if trade_cost > cash:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient cash. Need ${trade_cost:.2f}, have ${cash:.2f}",
                    )
                new_cash = cash - trade_cost
                new_qty = existing_qty + quantity
                # Weighted average cost
                total_cost = (existing_qty * existing_avg_cost) + (quantity * current_price)
                new_avg_cost = total_cost / new_qty

            else:  # sell
                if quantity > existing_qty:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient shares. Have {existing_qty}, trying to sell {quantity}",
                    )
                new_cash = cash + trade_cost
                new_qty = existing_qty - quantity
                new_avg_cost = existing_avg_cost  # avg cost doesn't change on sell

            # Update cash
            await db.execute(
                "UPDATE users_profile SET cash_balance = ? WHERE id = ?",
                (new_cash, "default"),
            )

            # Update or insert position
            if position:
                if new_qty > 0:
                    await db.execute(
                        "UPDATE positions SET quantity = ?, avg_cost = ?, updated_at = ? WHERE user_id = ? AND ticker = ?",
                        (new_qty, new_avg_cost, now, "default", ticker),
                    )
                else:
                    await db.execute(
                        "DELETE FROM positions WHERE user_id = ? AND ticker = ?",
                        ("default", ticker),
                    )
            else:
                await db.execute(
                    "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), "default", ticker, new_qty, new_avg_cost, now),
                )

            # Record trade
            await db.execute(
                "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (str(uuid.uuid4()), "default", ticker, side, quantity, current_price, now),
            )

            # Snapshot portfolio value after trade
            total_value = await _calc_total_value(db, new_cash, price_cache)
            await db.execute(
                "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), "default", total_value, now),
            )

            await db.commit()

        return {
            "ticker": ticker,
            "side": side,
            "quantity": quantity,
            "price": round(current_price, 2),
            "total_cost": round(trade_cost, 2),
            "cash_remaining": round(new_cash, 2),
        }

    @router.get("/history")
    async def get_history():
        """Return portfolio value snapshots for the P&L chart."""
        async with get_db() as db:
            cursor = await db.execute(
                "SELECT total_value, recorded_at FROM portfolio_snapshots WHERE user_id = ? ORDER BY recorded_at",
                ("default",),
            )
            rows = await cursor.fetchall()

        return [
            {"total_value": round(row["total_value"], 2), "recorded_at": row["recorded_at"]}
            for row in rows
        ]

    return router


async def _calc_total_value(db, cash: float, price_cache: PriceCache) -> float:
    """Calculate total portfolio value (cash + positions at current prices)."""
    cursor = await db.execute(
        "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ? AND quantity > 0",
        ("default",),
    )
    rows = await cursor.fetchall()
    market_value = sum(
        row["quantity"] * (price_cache.get_price(row["ticker"]) or row["avg_cost"])
        for row in rows
    )
    return cash + market_value
