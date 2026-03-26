"""Chat router — POST /api/chat with LLM-powered trading assistant."""

import json
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.database import get_db
from app.market import PriceCache

# LiteLLM constants (Cerebras via OpenRouter)
MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

SYSTEM_PROMPT = """You are FinAlly, an AI trading assistant for a simulated trading platform.
The user has a virtual portfolio with fake money — no real financial risk.

Your capabilities:
- Analyze portfolio composition, risk concentration, and P&L
- Suggest trades with reasoning
- Execute trades when the user asks or agrees (buy/sell shares)
- Manage the watchlist (add/remove tickers)

Rules:
- Be concise and data-driven
- When executing trades, specify ticker, side (buy/sell), and quantity
- For watchlist changes, specify ticker and action (add/remove)
- Always respond with valid JSON matching the required schema"""


# --- Pydantic models for structured output ---

class TradeAction(BaseModel):
    ticker: str
    side: str  # "buy" or "sell"
    quantity: float


class WatchlistChange(BaseModel):
    ticker: str
    action: str  # "add" or "remove"


class ChatResponse(BaseModel):
    """Structured output schema for the LLM."""
    message: str = Field(description="Conversational response to the user")
    trades: list[TradeAction] = Field(default_factory=list, description="Trades to auto-execute")
    watchlist_changes: list[WatchlistChange] = Field(
        default_factory=list, description="Watchlist modifications"
    )


class ChatRequest(BaseModel):
    message: str


class ChatResponseAPI(BaseModel):
    """Full API response including executed action results."""
    message: str
    trades: list[dict] = Field(default_factory=list)
    watchlist_changes: list[dict] = Field(default_factory=list)
    trade_results: list[dict] = Field(default_factory=list)
    watchlist_results: list[dict] = Field(default_factory=list)


def create_chat_router(price_cache: PriceCache) -> APIRouter:
    """Factory that creates the chat router with access to the price cache."""
    router = APIRouter(prefix="/api", tags=["chat"])

    @router.post("/chat", response_model=ChatResponseAPI)
    async def chat(request: ChatRequest):
        now = datetime.now(timezone.utc).isoformat()

        # Store user message
        user_msg_id = str(uuid.uuid4())
        async with get_db() as db:
            await db.execute(
                "INSERT INTO chat_messages (id, user_id, role, content, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_msg_id, "default", "user", request.message, now),
            )
            await db.commit()

        # Build portfolio context
        context = await _build_portfolio_context(price_cache)

        # Load conversation history (last 10 messages)
        history = await _load_chat_history()

        # Get LLM response
        llm_response = await _get_llm_response(context, history, request.message)

        # Auto-execute trades
        trade_results = []
        for trade in llm_response.trades:
            result = await _execute_trade(trade, price_cache)
            trade_results.append(result)

        # Auto-execute watchlist changes
        watchlist_results = []
        for change in llm_response.watchlist_changes:
            result = await _execute_watchlist_change(change)
            watchlist_results.append(result)

        # Build actions JSON for storage
        actions = None
        if llm_response.trades or llm_response.watchlist_changes:
            actions = json.dumps({
                "trades": [t.model_dump() for t in llm_response.trades],
                "watchlist_changes": [w.model_dump() for w in llm_response.watchlist_changes],
                "trade_results": trade_results,
                "watchlist_results": watchlist_results,
            })

        # Store assistant message
        assistant_msg_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        async with get_db() as db:
            await db.execute(
                "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (assistant_msg_id, "default", "assistant", llm_response.message, actions, now),
            )
            await db.commit()

        return ChatResponseAPI(
            message=llm_response.message,
            trades=[t.model_dump() for t in llm_response.trades],
            watchlist_changes=[w.model_dump() for w in llm_response.watchlist_changes],
            trade_results=trade_results,
            watchlist_results=watchlist_results,
        )

    return router


async def _build_portfolio_context(price_cache: PriceCache) -> str:
    """Build a text summary of the user's portfolio for the LLM system prompt."""
    async with get_db() as db:
        # Cash balance
        cursor = await db.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", ("default",)
        )
        row = await cursor.fetchone()
        cash = row["cash_balance"] if row else 10000.0

        # Positions
        cursor = await db.execute(
            "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ?", ("default",)
        )
        positions = await cursor.fetchall()

        # Watchlist
        cursor = await db.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ?", ("default",)
        )
        watchlist_rows = await cursor.fetchall()

    watchlist_tickers = [r["ticker"] for r in watchlist_rows]

    # Build positions detail with live prices
    total_positions_value = 0.0
    position_lines = []
    for pos in positions:
        ticker = pos["ticker"]
        qty = pos["quantity"]
        avg_cost = pos["avg_cost"]
        current_price = price_cache.get_price(ticker) or avg_cost
        market_value = qty * current_price
        cost_basis = qty * avg_cost
        unrealized_pnl = market_value - cost_basis
        pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis else 0
        total_positions_value += market_value
        position_lines.append(
            f"  {ticker}: {qty} shares @ avg ${avg_cost:.2f}, "
            f"current ${current_price:.2f}, P&L ${unrealized_pnl:+.2f} ({pnl_pct:+.1f}%)"
        )

    total_value = cash + total_positions_value

    # Watchlist with prices
    watchlist_lines = []
    for ticker in watchlist_tickers:
        price = price_cache.get_price(ticker)
        if price:
            watchlist_lines.append(f"  {ticker}: ${price:.2f}")
        else:
            watchlist_lines.append(f"  {ticker}: (no price)")

    parts = [
        f"Portfolio Summary:",
        f"  Cash: ${cash:,.2f}",
        f"  Total Value: ${total_value:,.2f}",
    ]
    if position_lines:
        parts.append("Positions:")
        parts.extend(position_lines)
    else:
        parts.append("Positions: None")
    parts.append("Watchlist:")
    parts.extend(watchlist_lines if watchlist_lines else ["  (empty)"])

    return "\n".join(parts)


async def _load_chat_history() -> list[dict]:
    """Load the last 10 chat messages for conversation context."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT role, content FROM chat_messages WHERE user_id = ? "
            "ORDER BY created_at DESC LIMIT 10",
            ("default",),
        )
        rows = await cursor.fetchall()

    # Reverse to chronological order
    messages = [{"role": row["role"], "content": row["content"]} for row in reversed(rows)]
    return messages


async def _get_llm_response(
    context: str, history: list[dict], user_message: str
) -> ChatResponse:
    """Call LLM (or return mock) and parse structured output."""
    if os.environ.get("LLM_MOCK", "").lower() == "true":
        return _mock_response(user_message)

    from litellm import completion

    messages = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nCurrent portfolio state:\n{context}"},
        *history,
        {"role": "user", "content": user_message},
    ]

    response = completion(
        model=MODEL,
        messages=messages,
        response_format=ChatResponse,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
    )
    content = response.choices[0].message.content
    return ChatResponse.model_validate_json(content)


def _mock_response(user_message: str) -> ChatResponse:
    """Deterministic mock response for testing."""
    lower = user_message.lower()

    if "buy" in lower:
        # Extract ticker and quantity from simple patterns like "buy 10 AAPL"
        parts = user_message.split()
        quantity = 10.0
        ticker = "AAPL"
        for i, p in enumerate(parts):
            if p.lower() == "buy" and i + 1 < len(parts):
                try:
                    quantity = float(parts[i + 1])
                    if i + 2 < len(parts):
                        ticker = parts[i + 2].upper()
                except ValueError:
                    ticker = parts[i + 1].upper()
        return ChatResponse(
            message=f"Executing buy order: {quantity} shares of {ticker}.",
            trades=[TradeAction(ticker=ticker, side="buy", quantity=quantity)],
        )

    if "sell" in lower:
        parts = user_message.split()
        quantity = 10.0
        ticker = "AAPL"
        for i, p in enumerate(parts):
            if p.lower() == "sell" and i + 1 < len(parts):
                try:
                    quantity = float(parts[i + 1])
                    if i + 2 < len(parts):
                        ticker = parts[i + 2].upper()
                except ValueError:
                    ticker = parts[i + 1].upper()
        return ChatResponse(
            message=f"Executing sell order: {quantity} shares of {ticker}.",
            trades=[TradeAction(ticker=ticker, side="sell", quantity=quantity)],
        )

    if "add" in lower and "watch" in lower:
        ticker = "PYPL"
        parts = user_message.split()
        for p in parts:
            if p.upper() != p.lower() and p.upper() not in ("ADD", "TO", "WATCHLIST", "THE", "MY"):
                ticker = p.upper()
        return ChatResponse(
            message=f"Adding {ticker} to your watchlist.",
            watchlist_changes=[WatchlistChange(ticker=ticker, action="add")],
        )

    if "remove" in lower and "watch" in lower:
        ticker = "TSLA"
        parts = user_message.split()
        for p in parts:
            if p.upper() != p.lower() and p.upper() not in (
                "REMOVE", "FROM", "WATCHLIST", "THE", "MY"
            ):
                ticker = p.upper()
        return ChatResponse(
            message=f"Removing {ticker} from your watchlist.",
            watchlist_changes=[WatchlistChange(ticker=ticker, action="remove")],
        )

    return ChatResponse(
        message="I'm your AI trading assistant. I can help you analyze your portfolio, "
        "execute trades, and manage your watchlist. What would you like to do?",
    )


async def _execute_trade(trade: TradeAction, price_cache: PriceCache) -> dict:
    """Execute a single trade. Returns result dict with success/error."""
    ticker = trade.ticker.upper()
    side = trade.side.lower()
    quantity = trade.quantity

    if quantity <= 0:
        return {"ticker": ticker, "success": False, "error": "Quantity must be positive"}

    current_price = price_cache.get_price(ticker)
    if current_price is None:
        return {"ticker": ticker, "success": False, "error": f"No price available for {ticker}"}

    now = datetime.now(timezone.utc).isoformat()
    trade_id = str(uuid.uuid4())

    async with get_db() as db:
        if side == "buy":
            # Check cash
            cursor = await db.execute(
                "SELECT cash_balance FROM users_profile WHERE id = ?", ("default",)
            )
            row = await cursor.fetchone()
            cash = row["cash_balance"]
            cost = current_price * quantity

            if cost > cash:
                return {
                    "ticker": ticker,
                    "success": False,
                    "error": f"Insufficient cash: need ${cost:.2f}, have ${cash:.2f}",
                }

            # Deduct cash
            await db.execute(
                "UPDATE users_profile SET cash_balance = cash_balance - ? WHERE id = ?",
                (cost, "default"),
            )

            # Update or create position
            cursor = await db.execute(
                "SELECT id, quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            existing = await cursor.fetchone()

            if existing:
                new_qty = existing["quantity"] + quantity
                new_avg = (
                    (existing["quantity"] * existing["avg_cost"] + quantity * current_price)
                    / new_qty
                )
                await db.execute(
                    "UPDATE positions SET quantity = ?, avg_cost = ?, updated_at = ? WHERE id = ?",
                    (new_qty, new_avg, now, existing["id"]),
                )
            else:
                await db.execute(
                    "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (str(uuid.uuid4()), "default", ticker, quantity, current_price, now),
                )

        elif side == "sell":
            # Check position
            cursor = await db.execute(
                "SELECT id, quantity, avg_cost FROM positions WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            existing = await cursor.fetchone()

            if not existing or existing["quantity"] < quantity:
                owned = existing["quantity"] if existing else 0
                return {
                    "ticker": ticker,
                    "success": False,
                    "error": f"Insufficient shares: want to sell {quantity}, own {owned}",
                }

            proceeds = current_price * quantity

            # Add cash
            await db.execute(
                "UPDATE users_profile SET cash_balance = cash_balance + ? WHERE id = ?",
                (proceeds, "default"),
            )

            # Update position
            new_qty = existing["quantity"] - quantity
            if new_qty < 0.0001:  # Effectively zero
                await db.execute("DELETE FROM positions WHERE id = ?", (existing["id"],))
            else:
                await db.execute(
                    "UPDATE positions SET quantity = ?, updated_at = ? WHERE id = ?",
                    (new_qty, now, existing["id"]),
                )
        else:
            return {"ticker": ticker, "success": False, "error": f"Invalid side: {side}"}

        # Record trade
        await db.execute(
            "INSERT INTO trades (id, user_id, ticker, side, quantity, price, executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (trade_id, "default", ticker, side, quantity, current_price, now),
        )

        # Record portfolio snapshot
        cursor = await db.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", ("default",)
        )
        row = await cursor.fetchone()
        new_cash = row["cash_balance"]

        cursor = await db.execute(
            "SELECT ticker, quantity FROM positions WHERE user_id = ?", ("default",)
        )
        pos_rows = await cursor.fetchall()
        positions_value = sum(
            r["quantity"] * (price_cache.get_price(r["ticker"]) or 0)
            for r in pos_rows
        )
        total_value = new_cash + positions_value

        await db.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) "
            "VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), "default", total_value, now),
        )

        await db.commit()

    return {
        "ticker": ticker,
        "side": side,
        "quantity": quantity,
        "price": current_price,
        "success": True,
    }


async def _execute_watchlist_change(change: WatchlistChange) -> dict:
    """Execute a single watchlist change. Returns result dict."""
    ticker = change.ticker.upper()
    action = change.action.lower()
    now = datetime.now(timezone.utc).isoformat()

    async with get_db() as db:
        if action == "add":
            cursor = await db.execute(
                "SELECT id FROM watchlist WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            if await cursor.fetchone():
                return {"ticker": ticker, "action": "add", "success": True, "note": "Already in watchlist"}

            await db.execute(
                "INSERT INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
                (str(uuid.uuid4()), "default", ticker, now),
            )
            await db.commit()
            return {"ticker": ticker, "action": "add", "success": True}

        elif action == "remove":
            cursor = await db.execute(
                "SELECT id FROM watchlist WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            if not await cursor.fetchone():
                return {"ticker": ticker, "action": "remove", "success": False, "error": "Not in watchlist"}

            await db.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND ticker = ?",
                ("default", ticker),
            )
            await db.commit()
            return {"ticker": ticker, "action": "remove", "success": True}

        return {"ticker": ticker, "action": action, "success": False, "error": f"Invalid action: {action}"}
