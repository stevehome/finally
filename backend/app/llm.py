"""LLM call abstraction for FinAlly chat: structured output schema, mock mode, context builders."""

import logging
import os

from litellm import completion
from pydantic import BaseModel

from app.db import get_connection
from app.market import PriceCache

logger = logging.getLogger(__name__)

MODEL = "openrouter/openai/gpt-4o-mini"
EXTRA_BODY: dict = {}
_HISTORY_LIMIT = 20

_SYSTEM_PROMPT_TEMPLATE = """\
You are FinAlly, an AI trading assistant for a simulated portfolio.

Current portfolio state:
{portfolio_context}

You help users analyze their portfolio and execute trades. When the user asks you to buy or sell,
include trade instructions in the 'trades' field. When they ask to add or remove watchlist tickers,
include changes in the 'watchlist_changes' field.

Be concise and data-driven. Always respond with valid JSON matching the required schema.
"""


# --- Pydantic models ---


class TradeAction(BaseModel):
    """A single trade action requested by the LLM."""

    ticker: str
    side: str  # "buy" or "sell"
    quantity: float


class WatchlistAction(BaseModel):
    """A single watchlist change requested by the LLM."""

    ticker: str
    action: str  # "add" or "remove"


class ChatResponse(BaseModel):
    """Structured output schema for LLM chat responses."""

    message: str
    trades: list[TradeAction] = []
    watchlist_changes: list[WatchlistAction] = []


_MOCK_RESPONSE = ChatResponse(
    message="FinAlly here (mock mode). Portfolio looks good — $10,000 cash, no open positions.",
    trades=[],
    watchlist_changes=[],
)


# --- Public API ---


def call_llm(messages: list[dict]) -> ChatResponse:
    """Call LLM via LiteLLM/OpenRouter/Cerebras, or return mock if LLM_MOCK=true."""
    if os.getenv("LLM_MOCK", "").lower() == "true":
        return _MOCK_RESPONSE

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    response = completion(
        model=MODEL,
        messages=messages,
        response_format=ChatResponse,
        api_key=api_key,
    )
    raw = response.choices[0].message.content
    return ChatResponse.model_validate_json(raw)


def build_portfolio_context(price_cache: PriceCache, user_id: str = "default") -> str:
    """Return a human-readable portfolio summary for the LLM system prompt."""
    conn = get_connection()
    try:
        profile = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)
        ).fetchone()
        cash = profile["cash_balance"] if profile else 0.0

        positions = conn.execute(
            "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = ?", (user_id,)
        ).fetchall()

        watchlist = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at", (user_id,)
        ).fetchall()
    finally:
        conn.close()

    lines = [f"Cash balance: ${cash:,.2f}"]
    lines.append("Positions:")
    for pos in positions:
        price = price_cache.get_price(pos["ticker"]) or pos["avg_cost"]
        pnl = (price - pos["avg_cost"]) * pos["quantity"]
        lines.append(
            f"  {pos['ticker']}: {pos['quantity']} shares @ avg ${pos['avg_cost']:.2f}, "
            f"current ${price:.2f}, P&L ${pnl:+.2f}"
        )
    lines.append("Watchlist: " + ", ".join(r["ticker"] for r in watchlist))
    return "\n".join(lines)


def build_system_prompt(portfolio_context: str) -> str:
    """Format the system prompt with current portfolio context."""
    return _SYSTEM_PROMPT_TEMPLATE.format(portfolio_context=portfolio_context)


def load_history(user_id: str = "default") -> list[dict]:
    """Return last N chat messages as LLM message dicts in chronological order.

    Only loads user and assistant roles — system messages are constructed fresh each call.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages "
            "WHERE user_id = ? AND role IN ('user', 'assistant') "
            "ORDER BY created_at DESC LIMIT ?",
            (user_id, _HISTORY_LIMIT),
        ).fetchall()
    finally:
        conn.close()

    # Reverse so messages are in chronological order (query returns newest-first)
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
