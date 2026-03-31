---
phase: 03-chat-api
plan: 03
subsystem: api
tags: [fastapi, litellm, llm, chat, portfolio, watchlist, sqlite, tdd]

# Dependency graph
requires:
  - phase: 03-02
    provides: app/llm.py with call_llm, build_portfolio_context, build_system_prompt, load_history, and internal helpers execute_trade_internal, add_ticker_internal, remove_ticker_internal
  - phase: 02-portfolio-watchlist-api
    provides: portfolio and watchlist routers with internal helpers
provides:
  - backend/app/routers/chat.py — POST /api/chat with LLM integration, auto-trade execution, watchlist changes, history persistence
  - chat router wired into main.py
  - 7 passing chat tests covering all CHAT requirements
affects:
  - frontend (consumes POST /api/chat endpoint)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Import module as alias (import app.llm as llm_module) to enable monkeypatching in tests
    - asyncio.to_thread wrapping sync LLM call to avoid blocking FastAPI event loop
    - actions payload pattern: trades_executed / trades_failed / watchlist_changes returned in chat response

key-files:
  created:
    - backend/app/routers/chat.py
  modified:
    - backend/main.py
    - backend/tests/test_chat.py

key-decisions:
  - "Import app.llm as llm_module in chat.py instead of 'from app.llm import call_llm' — allows monkeypatch.setattr('app.llm.call_llm', ...) to work in tests without coupling to internal binding"
  - "User message saved AFTER loading history so current message doesn't appear in the prior history list sent to LLM"
  - "actions payload always returned even if empty — frontend can always rely on trades_executed/trades_failed/watchlist_changes keys"

patterns-established:
  - "Module alias import pattern: import app.llm as llm_module; use llm_module.call_llm() so test monkeypatching of module attribute works correctly"

requirements-completed: [CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06, CHAT-07]

# Metrics
duration: 8min
completed: 2026-03-31
---

# Phase 03 Plan 03: Chat Router Summary

**POST /api/chat endpoint with LLM call, auto-trade execution, watchlist change application, history persistence, and mock mode — all 7 tests passing**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-31T11:08:00Z
- **Completed:** 2026-03-31T11:16:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Created `backend/app/routers/chat.py` with full POST /api/chat implementation: loads history, saves user message, builds system+context+history messages list, calls LLM via asyncio.to_thread, auto-executes trades, applies watchlist changes, saves assistant message, returns structured actions payload
- Wired chat router into `backend/main.py` after watchlist router
- Promoted all 7 xfail tests to passing tests — removed xfail markers, fixed imports, corrected watchlist response key, full suite 105/105 passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create chat router and wire into main.py** - `66edd5a` (feat)
2. **Task 2: Remove xfail markers and make all chat tests pass** - `727df52` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `backend/app/routers/chat.py` — POST /api/chat handler with LLM integration, auto-execute, history
- `backend/main.py` — Added chat router import and include_router call
- `backend/tests/test_chat.py` — Removed xfail markers, fixed imports and watchlist key

## Decisions Made

- `import app.llm as llm_module` in chat.py so `monkeypatch.setattr("app.llm.call_llm", ...)` works in tests. Direct `from app.llm import call_llm` binds the name locally and makes the monkeypatch ineffective.
- User message is saved to DB *after* loading history, so the current message goes at the end of the messages list via explicit append rather than appearing twice via history.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Module alias import to fix monkeypatch binding**
- **Found during:** Task 2 (running tests — test_chat_includes_portfolio_context and 4 others failing)
- **Issue:** Using `from app.llm import call_llm` bound the name locally in chat.py; `monkeypatch.setattr("app.llm.call_llm", fake)` patches the module attribute but not the already-imported local reference
- **Fix:** Changed to `import app.llm as llm_module` and called `llm_module.call_llm` in the handler
- **Files modified:** backend/app/routers/chat.py
- **Verification:** All 7 tests pass after fix
- **Committed in:** 727df52 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed watchlist response key in test**
- **Found during:** Task 2 (test_chat_applies_watchlist_changes failing)
- **Issue:** Test accessed `watchlist.json()` directly as a list, but GET /api/watchlist returns `{"watchlist": [...]}` dict
- **Fix:** Changed test to access `watchlist.json()["watchlist"]`
- **Files modified:** backend/tests/test_chat.py
- **Verification:** test_chat_applies_watchlist_changes passes
- **Committed in:** 727df52 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (Rule 1 — implementation bugs discovered during test run)
**Impact on plan:** Both necessary for correctness. No scope creep.

## Issues Encountered

The `from app.llm import call_llm` vs `import app.llm as llm_module` distinction is a classic Python monkeypatching pitfall. The STATE.md decision "monkeypatch app.llm.call_llm (not litellm.completion)" implied the module-level attribute pattern, which requires using `llm_module.call_llm` in the production code.

## User Setup Required

None - OPENROUTER_API_KEY is only needed at runtime when `LLM_MOCK` is not set. All tests use mock mode.

## Next Phase Readiness

- Phase 03 (chat-api) is complete. All 3 plans executed, 7 chat requirements delivered.
- POST /api/chat ready for frontend integration
- Full backend test suite: 105 tests passing, ruff clean
- Next: Phase 04 — frontend (Next.js trading terminal UI)

## Self-Check: PASSED

- `backend/app/routers/chat.py` — FOUND
- `backend/tests/test_chat.py` — FOUND
- `03-03-SUMMARY.md` — FOUND
- Commit `66edd5a` (Task 1) — FOUND
- Commit `727df52` (Task 2) — FOUND

---
*Phase: 03-chat-api*
*Completed: 2026-03-31*
