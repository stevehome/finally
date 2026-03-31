"""Chat router: POST /api/chat — LLM conversation with auto-execute."""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from pydantic import BaseModel

import app.llm as llm_module
from app.db import get_connection
from app.llm import build_portfolio_context, build_system_prompt, load_history
from app.routers.portfolio import execute_trade_internal
from app.routers.watchlist import add_ticker_internal, remove_ticker_internal

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    message: str


# --- Internals ---


def _save_message(
    user_id: str, role: str, content: str, actions: str | None = None
) -> None:
    """Insert a chat message into the chat_messages table."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()),
                user_id,
                role,
                content,
                actions,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


# --- Public API ---


@router.post("/chat")
async def chat(request: Request, body: ChatRequest) -> dict:
    """Send a message to the LLM, auto-execute any trades/watchlist changes, return results."""
    user_id = "default"
    price_cache = request.app.state.price_cache
    source = request.app.state.source

    # 1. Load history before saving the current message
    history = load_history(user_id)

    # 2. Save user message to DB
    _save_message(user_id, "user", body.message)

    # 3. Build messages list for LLM
    portfolio_context = build_portfolio_context(price_cache, user_id)
    system_prompt = build_system_prompt(portfolio_context)
    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": body.message}]
    )

    # 4. Call LLM in a thread to avoid blocking the event loop
    llm_response = await asyncio.to_thread(llm_module.call_llm, messages)

    # 5. Auto-execute trades
    trade_results = []
    for trade in llm_response.trades:
        result = execute_trade_internal(
            price_cache,
            trade.ticker.upper(),
            trade.quantity,
            trade.side.lower(),
            user_id,
        )
        trade_results.append(result)

    # 6. Apply watchlist changes
    watchlist_results = []
    for change in llm_response.watchlist_changes:
        ticker = change.ticker.upper()
        if change.action == "add":
            applied = await add_ticker_internal(source, ticker, user_id)
        else:
            applied = await remove_ticker_internal(source, ticker, user_id)
        watchlist_results.append({"ticker": ticker, "action": change.action, "applied": applied})

    # 7. Build actions payload
    actions_payload = {
        "trades_executed": [r for r in trade_results if r["error"] is None],
        "trades_failed": [r for r in trade_results if r["error"] is not None],
        "watchlist_changes": watchlist_results,
    }

    # 8. Save assistant message with actions
    _save_message(user_id, "assistant", llm_response.message, actions=json.dumps(actions_payload))

    return {"message": llm_response.message, "actions": actions_payload}
