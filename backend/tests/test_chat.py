"""Chat API tests: POST /api/chat — CHAT-01 through CHAT-07."""

import time

import pytest
from fastapi.testclient import TestClient

from app.llm import ChatResponse, TradeAction, WatchlistAction
from main import app


def test_chat_returns_message(monkeypatch) -> None:
    """CHAT-01: POST /api/chat returns 200 with a message field."""
    monkeypatch.setenv("LLM_MOCK", "true")
    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


def test_chat_includes_portfolio_context(monkeypatch) -> None:
    """CHAT-02: LLM is called with messages containing portfolio context."""
    monkeypatch.setenv("LLM_MOCK", "true")
    captured = {}

    def fake_call_llm(messages: list) -> ChatResponse:
        captured["messages"] = messages
        return ChatResponse(message="ok", trades=[], watchlist_changes=[])

    monkeypatch.setattr("app.llm.call_llm", fake_call_llm)

    with TestClient(app) as client:
        time.sleep(0.1)  # Let market simulator seed prices
        # Buy 1 share so AAPL appears in portfolio
        client.post("/api/portfolio/trade", json={"ticker": "AAPL", "quantity": 1, "side": "buy"})
        client.post("/api/chat", json={"message": "What is my portfolio?"})

    assert "messages" in captured
    system_content = captured["messages"][0]["content"].lower()
    assert "aapl" in system_content
    assert "cash" in system_content


def test_chat_auto_executes_trade(monkeypatch) -> None:
    """CHAT-03: Trade in LLM response is auto-executed against the portfolio."""
    monkeypatch.setenv("LLM_MOCK", "true")

    def fake_call_llm(messages: list) -> ChatResponse:
        return ChatResponse(
            message="Buying 1 AAPL for you.",
            trades=[TradeAction(ticker="AAPL", side="buy", quantity=1)],
            watchlist_changes=[],
        )

    monkeypatch.setattr("app.llm.call_llm", fake_call_llm)

    with TestClient(app) as client:
        time.sleep(0.1)  # Let market simulator seed prices
        client.post("/api/chat", json={"message": "Buy 1 AAPL"})
        portfolio = client.get("/api/portfolio").json()

    positions = {p["ticker"]: p for p in portfolio["positions"]}
    assert "AAPL" in positions
    assert positions["AAPL"]["quantity"] == pytest.approx(1.0)


def test_chat_applies_watchlist_changes(monkeypatch) -> None:
    """CHAT-04: Watchlist change in LLM response is applied."""
    monkeypatch.setenv("LLM_MOCK", "true")

    def fake_call_llm(messages: list) -> ChatResponse:
        return ChatResponse(
            message="Added PYPL to your watchlist.",
            trades=[],
            watchlist_changes=[WatchlistAction(ticker="PYPL", action="add")],
        )

    monkeypatch.setattr("app.llm.call_llm", fake_call_llm)

    with TestClient(app) as client:
        client.post("/api/chat", json={"message": "Add PYPL to my watchlist"})
        watchlist = client.get("/api/watchlist").json()

    tickers = [entry["ticker"] for entry in watchlist["watchlist"]]
    assert "PYPL" in tickers


def test_chat_history_persisted(monkeypatch) -> None:
    """CHAT-05: Prior conversation messages are included in subsequent LLM calls."""
    monkeypatch.setenv("LLM_MOCK", "true")
    call_count = 0
    captured_second = {}

    def fake_call_llm(messages: list) -> ChatResponse:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            captured_second["messages"] = messages
        return ChatResponse(message=f"Response {call_count}", trades=[], watchlist_changes=[])

    monkeypatch.setattr("app.llm.call_llm", fake_call_llm)

    with TestClient(app) as client:
        client.post("/api/chat", json={"message": "First message"})
        client.post("/api/chat", json={"message": "Second message"})

    assert "messages" in captured_second
    # History should include the first user message and first assistant response
    roles_and_content = [(m["role"], m["content"]) for m in captured_second["messages"]]
    user_contents = [content for role, content in roles_and_content if role == "user"]
    assistant_contents = [content for role, content in roles_and_content if role == "assistant"]
    assert any("First message" in c for c in user_contents)
    assert any("Response 1" in c for c in assistant_contents)


def test_chat_mock_mode(monkeypatch) -> None:
    """CHAT-06: LLM_MOCK=true returns a deterministic response without calling litellm."""
    monkeypatch.setenv("LLM_MOCK", "true")

    def should_not_be_called(*args, **kwargs):
        raise AssertionError("litellm.completion should NOT be called in mock mode")

    monkeypatch.setattr("litellm.completion", should_not_be_called)

    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "Hello"})

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0


def test_chat_failed_trade_in_response(monkeypatch) -> None:
    """CHAT-07: Failed trade validation reported in response body, not HTTP 400."""
    monkeypatch.setenv("LLM_MOCK", "true")

    def fake_call_llm(messages: list) -> ChatResponse:
        # User has no AAPL shares — selling 999 will fail validation
        return ChatResponse(
            message="Selling 999 AAPL for you.",
            trades=[TradeAction(ticker="AAPL", side="sell", quantity=999)],
            watchlist_changes=[],
        )

    monkeypatch.setattr("app.llm.call_llm", fake_call_llm)

    with TestClient(app) as client:
        response = client.post("/api/chat", json={"message": "Sell 999 AAPL"})

    # Must be 200 — validation failure goes into actions.trades_failed, not HTTP 4xx
    assert response.status_code == 200
    data = response.json()
    assert "actions" in data
    assert "trades_failed" in data["actions"]
    failed = data["actions"]["trades_failed"]
    assert len(failed) > 0
    assert any("error" in t and t["error"] for t in failed)


def test_build_portfolio_context_with_positions() -> None:
    """build_portfolio_context with a position returns string with ticker and cash."""
    import uuid

    from app.db import get_connection, init_db
    from app.llm import build_portfolio_context
    from app.market import PriceCache

    init_db()
    cache = PriceCache()
    cache.update("AAPL", 150.0)

    # Insert a position directly into the DB
    conn = get_connection()
    conn.execute(
        "INSERT INTO positions (id, user_id, ticker, quantity, avg_cost, updated_at) "
        "VALUES (?, 'default', 'AAPL', 2.0, 145.0, datetime('now'))",
        (str(uuid.uuid4()),),
    )
    conn.commit()
    conn.close()

    context = build_portfolio_context(cache, "default")
    assert "AAPL" in context
    assert "cash" in context.lower()


def test_load_history_chronological_order() -> None:
    """load_history returns messages oldest-first (chronological order)."""
    import uuid

    from app.db import get_connection, init_db
    from app.llm import load_history

    init_db()

    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_messages (id, user_id, role, content, created_at) VALUES (?, 'default', 'user', 'First message', ?)",
        (str(uuid.uuid4()), "2024-01-01T10:00:00"),
    )
    conn.execute(
        "INSERT INTO chat_messages (id, user_id, role, content, created_at) VALUES (?, 'default', 'assistant', 'First reply', ?)",
        (str(uuid.uuid4()), "2024-01-01T10:00:01"),
    )
    conn.commit()
    conn.close()

    history = load_history("default")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "First message"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "First reply"


def test_call_llm_raises_without_api_key(monkeypatch) -> None:
    """call_llm raises ValueError when OPENROUTER_API_KEY unset and LLM_MOCK not true."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LLM_MOCK", raising=False)

    import importlib

    import app.llm as llm_mod

    importlib.reload(llm_mod)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        llm_mod.call_llm([{"role": "user", "content": "hello"}])


def test_build_system_prompt_contains_context() -> None:
    """build_system_prompt interpolates the portfolio context string into the template."""
    from app.llm import build_system_prompt

    prompt = build_system_prompt("my_unique_context_string_xyz")
    assert "my_unique_context_string_xyz" in prompt
