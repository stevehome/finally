---
phase: 02-portfolio-watchlist-api
plan: 03
subsystem: api
tags: [fastapi, sqlite, watchlist, sse, market-data]

# Dependency graph
requires:
  - phase: 02-portfolio-watchlist-api/02-02
    provides: portfolio router, app.state.price_cache, app.state.source, db.py, main.py lifespan
provides:
  - GET /api/watchlist — returns watchlist tickers with current prices
  - POST /api/watchlist — adds ticker to DB and calls source.add_ticker (idempotent)
  - DELETE /api/watchlist/{ticker} — removes ticker, calls source.remove_ticker, 404 if absent
affects: [03-chat-llm, frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - INSERT OR IGNORE for idempotent watchlist adds
    - request.app.state.source for market data source access in routers (avoids circular imports)
    - AsyncMock patching of app.state.source methods for integration test isolation

key-files:
  created:
    - backend/app/routers/watchlist.py
  modified:
    - backend/main.py
    - backend/tests/test_watchlist.py

key-decisions:
  - "INSERT OR IGNORE keeps POST /api/watchlist idempotent — no 500 on duplicate ticker add"
  - "Existence check before DELETE enables 404 response instead of silent no-op"
  - "AsyncMock patched directly onto app.state.source after TestClient starts — avoids restarting lifespan"

patterns-established:
  - "Watchlist router pattern: DB operation first, then async source call — DB is source of truth"
  - "Ticker normalization: always .upper() on input before DB write or source call"

requirements-completed: [WATCH-01, WATCH-02, WATCH-03, WATCH-04, WATCH-05]

# Metrics
duration: 2min
completed: 2026-03-31
---

# Phase 02 Plan 03: Watchlist Router Summary

**FastAPI watchlist router with GET/POST/DELETE endpoints keeping SQLite DB and market data source in sync, all 98 tests passing**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-31T07:09:18Z
- **Completed:** 2026-03-31T07:11:16Z
- **Tasks:** 4
- **Files modified:** 5

## Accomplishments

- Created `backend/app/routers/watchlist.py` with three fully-tested endpoints
- GET /api/watchlist returns all seeded/added tickers with cached prices (None if not yet cached)
- POST /api/watchlist is idempotent via INSERT OR IGNORE; always calls source.add_ticker
- DELETE /api/watchlist/{ticker} returns 404 for non-existent tickers; calls source.remove_ticker
- All 98 tests pass (84 market data + 7 DB/main + 9 portfolio + 5 watchlist — clean suite)

## Task Commits

Each task was committed atomically:

1. **Task 1+2: Watchlist router and main.py registration** - `b316e02` (feat)
2. **Task 3: Promote test stubs to real tests** - `281c10f` (test)
3. **Task 4: Fix lint/format issues** - `1b9eae9` (chore)

## Files Created/Modified

- `backend/app/routers/watchlist.py` - GET/POST/DELETE watchlist endpoints with DB + source sync
- `backend/main.py` - Added watchlist import and `app.include_router(watchlist.router, prefix="/api")`
- `backend/tests/test_watchlist.py` - Real tests replacing all 5 xfail stubs

## Decisions Made

- INSERT OR IGNORE keeps POST /api/watchlist idempotent — no 500 on duplicate ticker add
- Existence check before DELETE enables 404 response instead of silent no-op
- AsyncMock patched directly onto app.state.source after TestClient starts — avoids restarting lifespan for test isolation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed unused pytest import and applied ruff format**
- **Found during:** Task 4 (full suite gate)
- **Issue:** test_watchlist.py had unused `pytest` import (relic from xfail stubs); 6 files had formatting drift
- **Fix:** Removed unused import, ran `ruff format` on all affected files
- **Files modified:** tests/test_watchlist.py, app/routers/watchlist.py, tests/market/test_models.py, tests/market/test_simulator.py, tests/market/test_simulator_source.py, tests/test_db.py, tests/test_portfolio.py
- **Verification:** ruff check and ruff format --check both exit 0
- **Committed in:** 1b9eae9 (Task 4 commit)

---

**Total deviations:** 1 auto-fixed (lint/format cleanup)
**Impact on plan:** Lint fix was required by plan success criteria. No scope creep.

## Issues Encountered

None — router implementation matched plan spec exactly. Test stubs for WATCH-04 and WATCH-05 passed import check after watchlist.py was created (expected XPASS before stubs were replaced with real tests).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All three watchlist REST endpoints active and tested
- `app.state.source` integration pattern established for chat router (Phase 3)
- Full Phase 2 API surface complete: health, SSE stream, portfolio, watchlist
- Phase 3 (chat/LLM) can use GET /api/watchlist and POST/DELETE /api/watchlist to read and mutate watchlist from AI actions

---
*Phase: 02-portfolio-watchlist-api*
*Completed: 2026-03-31*

## Self-Check: PASSED

- FOUND: backend/app/routers/watchlist.py
- FOUND: .planning/phases/02-portfolio-watchlist-api/02-03-SUMMARY.md
- FOUND commit b316e02 (feat: watchlist router + main.py)
- FOUND commit 281c10f (test: real watchlist tests)
- FOUND commit 1b9eae9 (chore: lint + format)
