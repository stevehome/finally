"""Chat API tests: POST /api/chat — CHAT-01 through CHAT-07 TDD stubs (RED phase)."""

import time

import pytest
from fastapi.testclient import TestClient

from main import app

try:
    from app.llm import ChatResponse, TradeAction, WatchlistAction
except ImportError:
    pass  # xfail will handle this


@pytest.mark.xfail(strict=True, reason="CHAT-01 not yet implemented")
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


@pytest.mark.xfail(strict=True, reason="CHAT-02 not yet implemented")
def test_chat_includes_portfolio_context(monkeypatch) -> None:
    """CHAT-02: LLM is called with messages containing portfolio context."""
    monkeypatch.setenv("LLM_MOCK", "true")
    captured = {}

    def fake_call_llm(messages: list) -> "ChatResponse":
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


@pytest.mark.xfail(strict=True, reason="CHAT-03 not yet implemented")
def test_chat_auto_executes_trade(monkeypatch) -> None:
    """CHAT-03: Trade in LLM response is auto-executed against the portfolio."""
    monkeypatch.setenv("LLM_MOCK", "true")

    def fake_call_llm(messages: list) -> "ChatResponse":
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


@pytest.mark.xfail(strict=True, reason="CHAT-04 not yet implemented")
def test_chat_applies_watchlist_changes(monkeypatch) -> None:
    """CHAT-04: Watchlist change in LLM response is applied."""
    monkeypatch.setenv("LLM_MOCK", "true")

    def fake_call_llm(messages: list) -> "ChatResponse":
        return ChatResponse(
            message="Added PYPL to your watchlist.",
            trades=[],
            watchlist_changes=[WatchlistAction(ticker="PYPL", action="add")],
        )

    monkeypatch.setattr("app.llm.call_llm", fake_call_llm)

    with TestClient(app) as client:
        client.post("/api/chat", json={"message": "Add PYPL to my watchlist"})
        watchlist = client.get("/api/watchlist").json()

    tickers = [entry["ticker"] for entry in watchlist]
    assert "PYPL" in tickers


@pytest.mark.xfail(strict=True, reason="CHAT-05 not yet implemented")
def test_chat_history_persisted(monkeypatch) -> None:
    """CHAT-05: Prior conversation messages are included in subsequent LLM calls."""
    monkeypatch.setenv("LLM_MOCK", "true")
    call_count = 0
    captured_second = {}

    def fake_call_llm(messages: list) -> "ChatResponse":
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


@pytest.mark.xfail(strict=True, reason="CHAT-06 not yet implemented")
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


@pytest.mark.xfail(strict=True, reason="CHAT-07 not yet implemented")
def test_chat_failed_trade_in_response(monkeypatch) -> None:
    """CHAT-07: Failed trade validation reported in response body, not HTTP 400."""
    monkeypatch.setenv("LLM_MOCK", "true")

    def fake_call_llm(messages: list) -> "ChatResponse":
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
