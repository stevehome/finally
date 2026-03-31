---
phase: 03-chat-api
plan: 02
subsystem: api
tags: [litellm, pydantic, openrouter, cerebras, llm, portfolio, watchlist]

# Dependency graph
requires:
  - phase: 03-01
    provides: TDD stubs for chat API (test_chat.py with xfail tests)
  - phase: 02-portfolio-watchlist-api
    provides: portfolio and watchlist routers that this plan refactors
provides:
  - app/llm.py with ChatResponse schema, call_llm(), build_portfolio_context(), build_system_prompt(), load_history()
  - execute_trade_internal() in portfolio.py — non-HTTP trade helper returning error dict
  - add_ticker_internal() and remove_ticker_internal() in watchlist.py — non-HTTP watchlist helpers
  - litellm added to pyproject.toml and uv.lock
affects:
  - 03-03 (chat router uses all these helpers directly)

# Tech tracking
tech-stack:
  added: [litellm>=1.83.0]
  patterns:
    - Internal helper pattern: extract HTTP handler logic into non-HTTP functions returning error dicts
    - LLM structured output with Pydantic BaseModel + response_format=ChatResponse
    - LLM_MOCK=true env var for deterministic test responses

key-files:
  created:
    - backend/app/llm.py
  modified:
    - backend/app/routers/portfolio.py
    - backend/app/routers/watchlist.py
    - backend/pyproject.toml
    - backend/uv.lock
    - backend/tests/test_chat.py

key-decisions:
  - "execute_trade_internal returns error dict (not HTTPException) so chat router can collect all trade errors"
  - "add_ticker_internal/remove_ticker_internal are async to match source.add_ticker/remove_ticker awaits"
  - "load_history filters to user/assistant roles only — system prompt is always built fresh"
  - "call_llm uses asyncio.to_thread in chat handler to avoid blocking FastAPI event loop"

patterns-established:
  - "Internal helper pattern: router logic split into HTTP handler (raises HTTPException) + internal helper (returns error dict)"
  - "LLM mock mode: os.getenv('LLM_MOCK', '').lower() == 'true' check before any API call"

requirements-completed: [CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-06]

# Metrics
duration: 5min
completed: 2026-03-31
---

# Phase 03 Plan 02: LLM Module and Internal Helpers Summary

**LiteLLM/Pydantic ChatResponse schema, portfolio context builder, history loader, and non-HTTP trade/watchlist helpers extracted for chat router composition**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-31T11:02:01Z
- **Completed:** 2026-03-31T11:04:54Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created `app/llm.py` with full LLM abstraction: ChatResponse/TradeAction/WatchlistAction Pydantic models, call_llm() with mock mode, build_portfolio_context(), build_system_prompt(), load_history()
- Added litellm>=1.83.0 to pyproject.toml and regenerated uv.lock (ensures Docker builds include it)
- Extracted execute_trade_internal() from portfolio.py — same logic as HTTP handler but returns `{"error": ...}` dict instead of raising HTTPException
- Extracted add_ticker_internal() and remove_ticker_internal() from watchlist.py — HTTP handlers now delegate to these helpers
- All 14 existing portfolio and watchlist tests pass unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Add litellm to pyproject.toml and create app/llm.py** - `d18ece5` (feat)
2. **Task 2: Extract internal helpers from portfolio.py and watchlist.py** - `0b023d8` (feat)

## Files Created/Modified

- `backend/app/llm.py` — LLM call abstraction: ChatResponse schema, call_llm(), mock mode, build_portfolio_context(), build_system_prompt(), load_history()
- `backend/app/routers/portfolio.py` — Added execute_trade_internal(); HTTP handler delegates to it
- `backend/app/routers/watchlist.py` — Added add_ticker_internal() and remove_ticker_internal(); HTTP handlers delegate to them
- `backend/pyproject.toml` — Added litellm>=1.83.0 to dependencies
- `backend/uv.lock` — Regenerated with litellm and updated transitive deps
- `backend/tests/test_chat.py` — Removed unused import of call_llm (auto-fix)

## Decisions Made

- execute_trade_internal() manages its own connection (opens/closes) so it can be called independently from the chat router without passing a connection object. Same pattern as existing record_snapshot().
- add_ticker_internal/remove_ticker_internal are async because they await source.add_ticker/remove_ticker — matches project's async patterns throughout.
- History loading filters `role IN ('user', 'assistant')` in SQL rather than Python filtering — cheaper and clearer intent.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused import of call_llm from test_chat.py**
- **Found during:** Task 2 (ruff lint verification)
- **Issue:** test_chat.py imported call_llm but never used it directly (monkeypatch uses string path "app.llm.call_llm"). Ruff F401 lint error.
- **Fix:** Removed call_llm from the import line in the try block
- **Files modified:** backend/tests/test_chat.py
- **Verification:** `ruff check app/ tests/` passes clean
- **Committed in:** 0b023d8 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - unused import lint fix)
**Impact on plan:** Minimal cleanup required. No scope creep.

## Issues Encountered

None — plan executed cleanly. litellm was already in the venv (as noted in RESEARCH.md), `uv add litellm` added it to pyproject.toml and updated the lockfile in seconds.

## User Setup Required

None - no external service configuration required for this plan. The OPENROUTER_API_KEY is only needed at runtime when LLM_MOCK is not set.

## Next Phase Readiness

- All building blocks ready for Plan 03-03: chat router can import call_llm, build_portfolio_context, load_history from app.llm, and execute_trade_internal, add_ticker_internal, remove_ticker_internal from the routers
- The 7 xfail chat tests in test_chat.py are ready to be promoted to passing tests once chat.py router is implemented

---
*Phase: 03-chat-api*
*Completed: 2026-03-31*
