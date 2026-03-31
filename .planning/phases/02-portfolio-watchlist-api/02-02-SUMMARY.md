---
phase: 02-portfolio-watchlist-api
plan: 02
subsystem: api
tags: [fastapi, sqlite, portfolio, trading, pydantic, sse]

# Dependency graph
requires:
  - phase: 02-portfolio-watchlist-api/02-01
    provides: xfail test stubs (PORT-01 through PORT-08) and db schema

provides:
  - GET /api/portfolio endpoint (cash, positions with live P&L, total_value)
  - POST /api/portfolio/trade endpoint (atomic buy/sell with 400 validation)
  - GET /api/portfolio/history endpoint (portfolio_snapshots list)
  - record_snapshot() helper (computes and persists total portfolio value)
  - _snapshot_loop background task (records snapshot every 30 seconds)
  - app.state.price_cache and app.state.source set in lifespan

affects:
  - 02-03-watchlist (follows same pattern: router in app/routers/, registered in main.py)
  - frontend phases (consumes these API endpoints)
  - 03-chat-llm (reads portfolio context for LLM prompt)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - request.app.state.price_cache for accessing PriceCache in routers (avoids circular import)
    - get_connection() called per-request (reads DB_PATH at call time — test-safe)
    - Explicit BEGIN/commit/rollback SQLite transaction pattern for atomic trade mutations
    - record_snapshot() called after trade execution (outside trade transaction — non-fatal)
    - asyncio.create_task(_snapshot_loop) in lifespan, cancelled with contextlib.suppress on shutdown

key-files:
  created:
    - backend/app/routers/portfolio.py
  modified:
    - backend/main.py
    - backend/tests/test_portfolio.py

key-decisions:
  - "record_snapshot called outside trade transaction — snapshot failure is non-fatal; trade still commits"
  - "current_price falls back to avg_cost when PriceCache has no entry (handles cold start)"
  - "DELETE position row when quantity reaches 0 after sell (clean state)"
  - "Explicit conn.execute('BEGIN') + rollback in except block for atomic trade mutations"

patterns-established:
  - "Router pattern: router = APIRouter(tags=[...]) in app/routers/; registered in main.py with app.include_router(..., prefix='/api')"
  - "State access pattern: request.app.state.price_cache — not imported from main.py to avoid circular import"
  - "DB access pattern: get_connection() called per handler, not shared across requests"

requirements-completed:
  - PORT-01
  - PORT-02
  - PORT-03
  - PORT-04
  - PORT-05
  - PORT-06
  - PORT-07
  - PORT-08

# Metrics
duration: 2min
completed: 2026-03-31
---

# Phase 02 Plan 02: Portfolio Router Summary

**FastAPI portfolio router with atomic buy/sell trade execution, live P&L from PriceCache, and a 30-second background snapshot task persisted to SQLite**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-31T07:05:26Z
- **Completed:** 2026-03-31T07:07:31Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Portfolio router with 3 endpoints (GET /api/portfolio, POST /api/portfolio/trade, GET /api/portfolio/history) serving correct response shapes
- Atomic trade execution with weighted-average cost calculation on buy, DELETE on full sell; returns 400 for insufficient cash or shares
- Background snapshot task started in lifespan and cancelled cleanly on shutdown; record_snapshot() callable standalone for testing

## Task Commits

1. **Task 1: Portfolio router** - `b34ddb3` (feat)
2. **Task 2: Wire into main.py** - `bc3bfc5` (feat)
3. **Task 3: Promote test stubs to real tests** - `b48bbb3` (test)

## Files Created/Modified

- `backend/app/routers/portfolio.py` - Portfolio router with record_snapshot, GET /api/portfolio, POST /api/portfolio/trade, GET /api/portfolio/history
- `backend/main.py` - Added portfolio router import, app.state.price_cache/source, _snapshot_loop background task
- `backend/tests/test_portfolio.py` - 9 xfail stubs replaced with real passing tests

## Decisions Made

- `record_snapshot` called outside the trade transaction so a snapshot failure does not roll back the trade
- `current_price` falls back to `avg_cost` when PriceCache has no entry (handles cold start before simulator seeds prices)
- Position row is deleted when sell reduces quantity to 0 (avoids orphan rows with 0 quantity)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — all 9 tests passed on first run after implementation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Portfolio endpoints are live and tested; ready for watchlist router (02-03)
- app.state.price_cache pattern established — watchlist router can follow the same pattern
- 93 tests passing, 5 xfailed (watchlist stubs awaiting 02-03)

---
*Phase: 02-portfolio-watchlist-api*
*Completed: 2026-03-31*

## Self-Check: PASSED

- backend/app/routers/portfolio.py: FOUND
- backend/main.py: FOUND
- .planning/phases/02-portfolio-watchlist-api/02-02-SUMMARY.md: FOUND
- Commit b34ddb3 (portfolio router): FOUND
- Commit bc3bfc5 (main.py wiring): FOUND
- Commit b48bbb3 (promoted tests): FOUND
