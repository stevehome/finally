---
phase: 02-portfolio-watchlist-api
plan: 01
subsystem: testing
tags: [pytest, xfail, tdd, portfolio, watchlist, fastapi]

# Dependency graph
requires:
  - phase: 01-backend-foundation
    provides: FastAPI app with lifespan, db.py schema, conftest.py tmp_db fixture
provides:
  - PORT-01 through PORT-08 xfail test stubs (backend/tests/test_portfolio.py)
  - WATCH-01 through WATCH-05 xfail test stubs (backend/tests/test_watchlist.py)
affects: [02-02, 02-03]

# Tech tracking
tech-stack:
  added: []
  patterns: [xfail strict=True for TDD RED phase stubs, TestClient(app) as context manager]

key-files:
  created:
    - backend/tests/test_portfolio.py
    - backend/tests/test_watchlist.py
  modified: []

key-decisions:
  - "xfail(strict=True) pattern: ensures tests fail loudly if accidentally passing (not just skipped)"
  - "No import of unimplemented routers at module level — ImportError inside test body triggers pytest.fail for clean collection"
  - "test_snapshot_background_task and streaming tests use try/except ImportError + pytest.fail pattern to fail without collection errors"

patterns-established:
  - "TDD RED stub pattern: @pytest.mark.xfail(strict=True) on every stub; ImportError-safe via try/except inside body"
  - "TestClient(app) context manager used for all HTTP-based stubs to exercise lifespan"

requirements-completed:
  - PORT-01
  - PORT-02
  - PORT-03
  - PORT-04
  - PORT-05
  - PORT-06
  - PORT-07
  - PORT-08
  - WATCH-01
  - WATCH-02
  - WATCH-03
  - WATCH-04
  - WATCH-05

# Metrics
duration: 1min
completed: 2026-03-31
---

# Phase 02 Plan 01: Portfolio and Watchlist Test Stubs Summary

**14 xfail TDD stubs created for portfolio (9) and watchlist (5) APIs, establishing RED phase before router implementation**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-03-31T07:02:35Z
- **Completed:** 2026-03-31T07:03:38Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Created `backend/tests/test_portfolio.py` with 9 xfail stubs covering all PORT-01..PORT-08 requirements
- Created `backend/tests/test_watchlist.py` with 5 xfail stubs covering all WATCH-01..WATCH-05 requirements
- Confirmed full suite: 84 prior tests pass, 14 new stubs xfail, 0 errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Portfolio test stubs (PORT-01 through PORT-08)** - `96367f2` (test)
2. **Task 2: Watchlist test stubs (WATCH-01 through WATCH-05)** - `1cf40fc` (test)
3. **Task 3: Full suite green (existing tests unaffected)** - no code changes needed

**Plan metadata:** (final metadata commit follows)

## Files Created/Modified

- `backend/tests/test_portfolio.py` - 9 xfail stubs: GET portfolio, buy/sell trade, insufficient cash/shares errors, trade history, snapshot after trade, snapshot background task, portfolio history
- `backend/tests/test_watchlist.py` - 5 xfail stubs: GET watchlist, add ticker (201), remove ticker (200/204), streaming integration for add/remove

## Decisions Made

- Used `xfail(strict=True)` so any accidentally-passing stub becomes an error, not a silent pass
- Used `try/except ImportError + pytest.fail()` pattern for stubs testing not-yet-importable modules (router functions), keeping collection clean
- Followed existing `TestClient(app)` as context manager pattern from `test_main.py`

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

All tests in this plan are intentional stubs (xfail). They will be resolved in plans 02-02 and 02-03 when the portfolio and watchlist routers are implemented.

## Next Phase Readiness

- RED phase complete: 14 failing tests define the contract for Wave 2 router implementation
- Plans 02-02 (portfolio router) and 02-03 (watchlist router) can now turn these stubs green
- No blockers

---
*Phase: 02-portfolio-watchlist-api*
*Completed: 2026-03-31*
