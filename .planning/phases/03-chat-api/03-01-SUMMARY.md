---
phase: 03-chat-api
plan: 01
subsystem: testing
tags: [pytest, tdd, xfail, chat, llm]

# Dependency graph
requires:
  - phase: 02-portfolio-watchlist-api
    provides: Portfolio/watchlist routers, trade execution, conftest.py patterns
provides:
  - 7 xfail(strict=True) TDD stubs for CHAT-01 through CHAT-07 in backend/tests/test_chat.py
affects: [03-chat-api]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "xfail(strict=True) stubs with ImportError-safe import block for not-yet-implemented modules"
    - "monkeypatch LLM_MOCK + app.llm.call_llm for test isolation without live API calls"

key-files:
  created:
    - backend/tests/test_chat.py
  modified: []

key-decisions:
  - "monkeypatch app.llm.call_llm (not litellm.completion) for trade/watchlist override tests — avoids coupling to internal LLM call chain"
  - "LLM_MOCK=true set via monkeypatch.setenv in each test — ensures test isolation without env leakage"

patterns-established:
  - "Pattern: monkeypatch app.llm.call_llm to return a ChatResponse to control LLM output in integration tests"
  - "Pattern: ImportError-safe try/except import block for modules not yet implemented (xfail handles the failure)"

requirements-completed: [CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06, CHAT-07]

# Metrics
duration: 3min
completed: 2026-03-31
---

# Phase 03 Plan 01: Chat API TDD Stubs Summary

**7 xfail(strict=True) test stubs for chat API covering CHAT-01 through CHAT-07 using monkeypatched LLM mock**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-31T11:00:28Z
- **Completed:** 2026-03-31T11:03:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created `backend/tests/test_chat.py` with 7 xfail(strict=True) test stubs
- All tests XFAIL immediately (app.llm module does not exist yet)
- Full suite runs clean: 98 passed, 7 xfailed, 0 errors
- Each test is mapped to exactly one CHAT-XX requirement via docstring

## Task Commits

1. **Task 1: Create failing test stubs for CHAT-01 through CHAT-07** - `ea865f7` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `backend/tests/test_chat.py` — 7 xfail stubs for CHAT-01 through CHAT-07, ImportError-safe import block

## Decisions Made
- Used `monkeypatch.setattr("app.llm.call_llm", fake_call_llm)` rather than patching `litellm.completion` directly, since the tests verify behavior at the chat API boundary (not the LLM transport boundary)
- Set `LLM_MOCK=true` as baseline via `monkeypatch.setenv` in every test to prevent accidental real LLM calls

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- RED phase complete for all 7 CHAT requirements
- Plan 03-02 can implement `app/llm.py` and `app/routers/chat.py` to turn these tests GREEN
- No blockers or concerns

---
*Phase: 03-chat-api*
*Completed: 2026-03-31*
