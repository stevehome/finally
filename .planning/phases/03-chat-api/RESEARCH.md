# Phase 03: Chat API - Research

**Researched:** 2026-03-31
**Domain:** LLM integration (LiteLLM/OpenRouter/Cerebras), FastAPI chat router, structured outputs
**Confidence:** HIGH

## Summary

Phase 03 adds the `POST /api/chat` endpoint. The backend collects portfolio context, loads conversation
history from the `chat_messages` table, calls the LLM (or a deterministic mock), parses a structured
JSON response, auto-executes any trades and watchlist changes, persists the exchange to the DB, and
returns the full result to the caller.

The key technical challenge is wiring structured outputs correctly with LiteLLM + OpenRouter + Cerebras,
and reusing existing trade/watchlist logic without duplicating validation code. Both of those are
well-understood from the existing codebase and the cerebras-inference skill.

**Primary recommendation:** Extract `execute_trade_internal` and `apply_watchlist_change_internal`
helper functions (not HTTP handlers) from the existing routers. The chat router calls those helpers
directly, accumulates results/errors, and returns them in the chat response rather than raising
HTTPExceptions.

## Project Constraints (from CLAUDE.md)

- Tech stack fixed: FastAPI + uv, SQLite, Docker single container, port 8000
- Python tooling: always `uv run` / `uv add`, never `python3` / `pip`
- LLM provider: LiteLLM → OpenRouter → Cerebras (`openrouter/openai/gpt-oss-120b`) — structured outputs required
- No auth: single user `"default"`, no login
- Market orders only, instant execution at current price
- Line length 100, ruff formatting, Google-style docstrings

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CHAT-01 | User can send a chat message and receive an AI response | LiteLLM completion call with Cerebras EXTRA_BODY |
| CHAT-02 | AI response includes portfolio context (cash, positions, prices) | Build context string from get_connection() + price_cache |
| CHAT-03 | AI auto-executes trades in its response | Extract trade logic as internal helper from portfolio.py |
| CHAT-04 | AI can add/remove watchlist tickers | Extract watchlist logic as internal helper from watchlist.py |
| CHAT-05 | Chat history persists, included in subsequent LLM calls | Query chat_messages table ordered by created_at, pass as messages list |
| CHAT-06 | LLM_MOCK=true returns deterministic responses | os.getenv("LLM_MOCK") check before LiteLLM call |
| CHAT-07 | Failed trade validation reported in chat response | Return errors list in response, don't raise HTTPException from helpers |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| litellm | 1.82.6 (installed) | LLM API abstraction over OpenRouter | Already in venv per cerebras skill |
| pydantic | 2.12.5 (installed, transitive) | Structured output schema + validation | Required by litellm structured outputs |
| fastapi | 0.115+ (installed) | HTTP router | Already in project |

litellm 1.82.6 is already installed in the backend venv. pydantic 2.12.5 is already present as a
transitive dependency. No `uv add` required unless litellm is not yet in `pyproject.toml` dependencies.

**Verification:** `uv pip list | grep litellm` → `litellm 1.82.6` confirmed present.

**Required pyproject.toml additions:**
```bash
uv add litellm
```
(litellm is in the venv but not yet listed in `pyproject.toml` `[project.dependencies]`. Must be added
so the lockfile reflects it and Docker builds include it.)

## Architecture Patterns

### Recommended Module Structure
```
backend/app/routers/
├── chat.py          # New — POST /api/chat handler + LLM call
backend/app/
├── llm.py           # New — LiteLLM call, mock logic, ChatResponse model
```

Two modules:
- `app/llm.py` — pure LLM concern: Pydantic `ChatResponse` schema, `call_llm()` function, mock logic.
  No FastAPI imports, no DB imports. Testable in isolation.
- `app/routers/chat.py` — FastAPI router: loads context, calls `app/llm.py`, executes side effects,
  persists messages, returns HTTP response.

### Pattern 1: LiteLLM Structured Output Call (from cerebras skill)

```python
# Source: .claude/skills/cerebras/SKILL.md
from litellm import completion
from pydantic import BaseModel

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

class TradeAction(BaseModel):
    ticker: str
    side: str      # "buy" or "sell"
    quantity: float

class WatchlistAction(BaseModel):
    ticker: str
    action: str    # "add" or "remove"

class ChatResponse(BaseModel):
    message: str
    trades: list[TradeAction] = []
    watchlist_changes: list[WatchlistAction] = []

def call_llm(messages: list[dict]) -> ChatResponse:
    response = completion(
        model=MODEL,
        messages=messages,
        response_format=ChatResponse,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
    )
    raw = response.choices[0].message.content
    return ChatResponse.model_validate_json(raw)
```

### Pattern 2: Mock Mode

```python
# Source: project spec (CLAUDE.md / planning/PLAN.md)
import os

_MOCK_RESPONSE = ChatResponse(
    message="I'm FinAlly (mock mode). Your portfolio looks great!",
    trades=[],
    watchlist_changes=[],
)

def call_llm(messages: list[dict]) -> ChatResponse:
    if os.getenv("LLM_MOCK", "").lower() == "true":
        return _MOCK_RESPONSE
    # ... real call
```

The mock response must be deterministic for E2E test assertions. A fixed string with no random
components is the right approach.

### Pattern 3: Reusing Trade Execution Logic (no duplication)

The existing `execute_trade` HTTP handler in `portfolio.py` raises `HTTPException` on failure. The
chat router cannot use that handler directly — it needs to collect errors as data, not raise HTTP 400s.

**Solution:** Extract the trade execution logic into a non-HTTP helper function.

```python
# In app/routers/portfolio.py — add this helper

class TradeResult(TypedDict):
    ticker: str
    side: str
    quantity: float
    price: float
    error: str | None  # None = success

def execute_trade_internal(
    conn: sqlite3.Connection,
    price_cache: PriceCache,
    ticker: str,
    quantity: float,
    side: str,
    user_id: str = "default",
) -> TradeResult:
    """Execute a trade within an open connection/transaction.

    Returns a TradeResult with error=None on success, error=<reason> on failure.
    Does NOT raise HTTPException — caller decides how to handle errors.
    """
    # ... same logic as execute_trade but returns error dict instead of raising
```

The HTTP handler `execute_trade` can then call `execute_trade_internal` and convert errors to
HTTPExceptions, keeping the existing behavior unchanged.

### Pattern 4: Reusing Watchlist Logic

Same pattern — extract DB/source mutation into a sync helper:

```python
# In app/routers/watchlist.py — add this helper

async def add_ticker_internal(source, ticker: str, user_id: str = "default") -> None:
    """Add ticker to DB and market data source. Idempotent (INSERT OR IGNORE)."""
    # ... same as add_ticker handler body

async def remove_ticker_internal(source, ticker: str, user_id: str = "default") -> bool:
    """Remove ticker from DB and market data source. Returns False if not found."""
    # ... same as remove_ticker handler body, return False instead of 404
```

### Pattern 5: Building Portfolio Context for System Prompt

```python
def build_portfolio_context(price_cache: PriceCache, user_id: str = "default") -> str:
    """Return a human-readable portfolio summary for the LLM system prompt."""
    conn = get_connection()
    try:
        profile = conn.execute("SELECT cash_balance FROM users_profile WHERE id = ?", (user_id,)).fetchone()
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
        lines.append(f"  {pos['ticker']}: {pos['quantity']} shares @ avg ${pos['avg_cost']:.2f}, "
                     f"current ${price:.2f}, P&L ${pnl:+.2f}")
    lines.append("Watchlist: " + ", ".join(r["ticker"] for r in watchlist))
    return "\n".join(lines)
```

### Pattern 6: Loading Conversation History

```python
_HISTORY_LIMIT = 20  # last 20 messages to avoid token overrun

def load_history(user_id: str = "default") -> list[dict]:
    """Return last N chat messages as LLM message dicts."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT role, content FROM chat_messages "
            "WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, _HISTORY_LIMIT),
        ).fetchall()
    finally:
        conn.close()
    # Reverse so chronological order (DESC query gives newest first)
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
```

### Pattern 7: Persisting Chat Messages

The `chat_messages` table schema (from `db.py`):
```
id TEXT PRIMARY KEY
user_id TEXT NOT NULL DEFAULT 'default'
role TEXT NOT NULL          -- "user" or "assistant"
content TEXT NOT NULL
actions TEXT                -- JSON or NULL
created_at TEXT NOT NULL
```

The `actions` column holds a JSON blob of what the assistant did:
```python
import json

actions_payload = {
    "trades_executed": [...],    # TradeResult dicts where error is None
    "trades_failed": [...],      # TradeResult dicts where error is not None
    "watchlist_changes": [...],  # {"ticker": ..., "action": ..., "applied": bool}
}
conn.execute(
    "INSERT INTO chat_messages (id, user_id, role, content, actions, created_at) VALUES (?,?,?,?,?,?)",
    (str(uuid.uuid4()), user_id, "assistant", llm_response.message,
     json.dumps(actions_payload), datetime.now(timezone.utc).isoformat())
)
```

### Pattern 8: Chat Router Complete Flow

```python
# app/routers/chat.py

@router.post("/chat")
async def chat(request: Request, body: ChatRequest) -> dict:
    """Send a message to the LLM with portfolio context; auto-execute returned actions."""
    user_id = "default"
    price_cache: PriceCache = request.app.state.price_cache
    source = request.app.state.source

    # 1. Persist user message
    _save_message(user_id, "user", body.message, actions=None)

    # 2. Build messages list for LLM
    portfolio_context = build_portfolio_context(price_cache, user_id)
    system_prompt = _build_system_prompt(portfolio_context)
    history = load_history(user_id)
    messages = [{"role": "system", "content": system_prompt}] + history + [
        {"role": "user", "content": body.message}
    ]

    # 3. Call LLM (or mock)
    llm_response = call_llm(messages)

    # 4. Auto-execute trades
    trade_results = []
    for trade in llm_response.trades:
        result = execute_trade_internal(price_cache, trade.ticker, trade.quantity, trade.side, user_id)
        trade_results.append(result)

    # 5. Apply watchlist changes
    watchlist_results = []
    for change in llm_response.watchlist_changes:
        applied = await apply_watchlist_change_internal(source, change.ticker, change.action, user_id)
        watchlist_results.append({"ticker": change.ticker, "action": change.action, "applied": applied})

    # 6. Persist assistant message with actions
    actions_payload = {
        "trades_executed": [r for r in trade_results if r["error"] is None],
        "trades_failed": [r for r in trade_results if r["error"] is not None],
        "watchlist_changes": watchlist_results,
    }
    _save_message(user_id, "assistant", llm_response.message, actions=json.dumps(actions_payload))

    # 7. Return complete response
    return {
        "message": llm_response.message,
        "actions": actions_payload,
    }
```

### Anti-Patterns to Avoid
- **Calling the HTTP handlers from the chat router:** The existing `execute_trade` route raises
  `HTTPException(400)` on validation failure. If the chat router calls it, a single failed trade
  aborts the whole chat response. Extract the logic, don't call the handler.
- **Storing history without a limit:** LLMs have token limits. Always cap history (e.g., last 20
  messages) to avoid exceeding context window or increasing latency.
- **Using `asyncio.to_thread` for LiteLLM:** LiteLLM's `completion()` is synchronous and blocking.
  For the chat endpoint (which is `async def`), wrap it: `await asyncio.to_thread(call_llm, messages)`.
  This keeps the FastAPI event loop free during the LLM call.
- **Storing raw API key in source:** Read `OPENROUTER_API_KEY` from `os.environ` at call time or
  module init. Do not hard-code or commit.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured JSON parsing | Manual JSON schema validation | pydantic `BaseModel` + `model_validate_json` | LiteLLM guarantees schema-conforming output; pydantic validates and gives typed objects |
| LLM provider routing/retry | Custom HTTP client to OpenRouter | LiteLLM `completion()` | LiteLLM handles retries, provider routing, error normalization |
| Async LLM call | `asyncio.run()` or threads manually | `asyncio.to_thread(call_llm, messages)` | FastAPI pattern for calling sync code from async handler |
| Token counting / truncation | Character-based heuristics | Fixed message count (last 20) | Simple and sufficient for single-user demo; avoids tiktoken dependency |

## Common Pitfalls

### Pitfall 1: HTTPException from trade logic bubbles through chat response
**What goes wrong:** Chat router calls existing `execute_trade` handler (or `raise HTTPException` path)
inside a loop over trades. One failed trade causes a 400 to propagate out, killing the entire chat
response even though the LLM message was valid.
**Why it happens:** HTTP handlers are designed to abort on error. Chat context needs collect-all-errors behavior.
**How to avoid:** Extract `execute_trade_internal()` that returns `{"error": "Insufficient cash"}` dict
instead of raising. Chat router accumulates all results.

### Pitfall 2: LiteLLM `completion()` blocks the event loop
**What goes wrong:** `completion()` is a blocking synchronous call. Calling it directly in an `async def`
FastAPI handler blocks the uvicorn event loop for the duration of the LLM call (~1-3s), freezing all
other requests (SSE streams stall, health checks time out).
**How to avoid:** `result = await asyncio.to_thread(call_llm, messages)`

### Pitfall 3: Missing `OPENROUTER_API_KEY` causes cryptic LiteLLM error
**What goes wrong:** If the env var is not set, LiteLLM raises an `AuthenticationError` with a message
that may not clearly point to the missing key.
**How to avoid:** Check for the key at chat module import time (or at first call) and raise a clear
`ValueError` with actionable message. The endpoint should return 500 with a clear detail string.

### Pitfall 4: litellm not in pyproject.toml despite being in the venv
**What goes wrong:** `uv pip list` shows litellm 1.82.6 but `pyproject.toml` `[project.dependencies]`
does not list it. Docker build runs `uv sync` which installs from lockfile — but if litellm was
added ad-hoc to the venv without `uv add`, it won't be in `uv.lock` and will be missing in the
container.
**How to avoid:** Run `uv add litellm` to add it to `pyproject.toml` and regenerate `uv.lock`.

### Pitfall 5: Structured output schema mismatch causes `model_validate_json` failure
**What goes wrong:** LLM returns a response where `trades` field is omitted (valid JSON but not
matching schema), causing pydantic validation to fail.
**How to avoid:** Use `= []` defaults on all optional list fields in the Pydantic model:
`trades: list[TradeAction] = []` and `watchlist_changes: list[WatchlistAction] = []`.

### Pitfall 6: History includes system messages from previous sessions
**What goes wrong:** If old system messages are accidentally stored in `chat_messages` and loaded back,
the LLM receives duplicate/conflicting system prompts.
**How to avoid:** Only persist `role="user"` and `role="assistant"` messages to `chat_messages`. The
system prompt is always constructed fresh at call time from current portfolio state.

## Code Examples

### Complete LLM module (app/llm.py)
```python
# Source: cerebras skill SKILL.md + project spec
import os
from litellm import completion
from pydantic import BaseModel

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

class TradeAction(BaseModel):
    ticker: str
    side: str
    quantity: float

class WatchlistAction(BaseModel):
    ticker: str
    action: str  # "add" or "remove"

class ChatResponse(BaseModel):
    message: str
    trades: list[TradeAction] = []
    watchlist_changes: list[WatchlistAction] = []

_MOCK_RESPONSE = ChatResponse(
    message="FinAlly here (mock mode). Portfolio looks good — $10,000 cash, no open positions.",
    trades=[],
    watchlist_changes=[],
)

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
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
        api_key=api_key,
    )
    raw = response.choices[0].message.content
    return ChatResponse.model_validate_json(raw)
```

### System prompt template
```python
_SYSTEM_PROMPT_TEMPLATE = """\
You are FinAlly, an AI trading assistant for a simulated portfolio.

Current portfolio state:
{portfolio_context}

You help users analyze their portfolio and execute trades. When the user asks you to buy or sell,
include trade instructions in the 'trades' field. When they ask to add or remove watchlist tickers,
include changes in the 'watchlist_changes' field.

Be concise and data-driven. Always respond with valid JSON matching the required schema.
"""

def build_system_prompt(portfolio_context: str) -> str:
    return _SYSTEM_PROMPT_TEMPLATE.format(portfolio_context=portfolio_context)
```

### Async wrapper for sync LiteLLM in FastAPI
```python
# In chat router
import asyncio
from app.llm import call_llm

llm_response = await asyncio.to_thread(call_llm, messages)
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| litellm | LLM calls | Yes | 1.82.6 (in venv) | LLM_MOCK=true for tests |
| pydantic | Structured output parsing | Yes | 2.12.5 (transitive) | — |
| OPENROUTER_API_KEY | Live LLM calls | Env-dependent | — | LLM_MOCK=true |
| SQLite (chat_messages table) | History persistence | Yes | Already in schema | — |

**Missing dependencies with no fallback:** None — LLM_MOCK=true covers the no-key case for tests.

**Action required:** Run `uv add litellm` in `backend/` to add it to `pyproject.toml` and lock file.
Without this, Docker builds will not include litellm.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.24+ |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run --extra dev pytest tests/test_chat.py -v` |
| Full suite command | `uv run --extra dev pytest -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CHAT-01 | POST /api/chat returns 200 with message field | unit | `pytest tests/test_chat.py::test_chat_returns_message -x` | No — Wave 0 |
| CHAT-02 | Response reflects current portfolio state | unit | `pytest tests/test_chat.py::test_chat_includes_portfolio_context -x` | No — Wave 0 |
| CHAT-03 | Trade in LLM response auto-executed | unit | `pytest tests/test_chat.py::test_chat_auto_executes_trade -x` | No — Wave 0 |
| CHAT-04 | Watchlist add/remove from LLM response applied | unit | `pytest tests/test_chat.py::test_chat_applies_watchlist_changes -x` | No — Wave 0 |
| CHAT-05 | History from prior calls included in LLM messages | unit | `pytest tests/test_chat.py::test_chat_history_persisted -x` | No — Wave 0 |
| CHAT-06 | LLM_MOCK=true returns deterministic response | unit | `pytest tests/test_chat.py::test_chat_mock_mode -x` | No — Wave 0 |
| CHAT-07 | Trade validation failure in response, not HTTP 400 | unit | `pytest tests/test_chat.py::test_chat_failed_trade_in_response -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run --extra dev pytest tests/test_chat.py -v`
- **Per wave merge:** `uv run --extra dev pytest -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_chat.py` — covers CHAT-01 through CHAT-07
- [ ] All tests use `LLM_MOCK=true` via monkeypatch to avoid real API calls

## Sources

### Primary (HIGH confidence)
- `.claude/skills/cerebras/SKILL.md` — exact LiteLLM API calls, MODEL constant, EXTRA_BODY, structured output pattern
- `backend/app/db.py` — chat_messages table schema verified directly
- `backend/app/routers/portfolio.py` — trade execution logic verified directly (268 lines)
- `backend/app/routers/watchlist.py` — watchlist add/remove logic verified directly (102 lines)
- `backend/main.py` — app.state structure (price_cache, source) verified directly
- `backend/tests/conftest.py` — test patterns (tmp_db fixture, TestClient) verified directly

### Secondary (MEDIUM confidence)
- LiteLLM 1.82.6 structured outputs with pydantic: `response_format=PydanticModel`, then
  `Model.model_validate_json(response.choices[0].message.content)` — consistent with skill docs
  and standard LiteLLM usage.

### Tertiary (LOW confidence)
- None — all critical claims verified against source files or skill documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — litellm confirmed in venv, pydantic confirmed transitive, all other deps
  already used in project
- Architecture: HIGH — patterns derived directly from existing router code; refactor approach is
  minimal and clear
- Pitfalls: HIGH — all identified from direct code inspection (HTTPException propagation, blocking
  sync call in async handler, missing pyproject.toml entry)

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (LiteLLM API is stable; OpenRouter provider routing pattern is fixed)
