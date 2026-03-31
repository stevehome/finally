---
phase: 04-frontend-shell-watchlist
plan: 03
subsystem: ui
tags: [react, typescript, lightweight-charts, sparkline, sse, watchlist, animation]

requires:
  - phase: 04-02
    provides: usePriceStream hook with sparkHistory ref, usePortfolio, useWatchlist, AppShell scaffold, globals.css flash animation classes

provides:
  - Sparkline component (lightweight-charts v5 LineSeries, 80x32 canvas, no axes)
  - WatchlistRow with green/red price flash animation (~500ms CSS fade)
  - WatchlistPanel composing WatchlistRow list
  - AppShell wired to WatchlistPanel (replaces inline ticker list)

affects: [05-main-chart, future-phases-using-watchlist]

tech-stack:
  added: []
  patterns:
    - "lightweight-charts v5 addSeries(LineSeries, opts) API — not removed addLineSeries()"
    - "UTCTimestamp cast pattern for SparkPoint.time nominal type compatibility"
    - "Flash animation via setTimeout state toggle — cleanup on rapid ticks prevents class stacking"
    - "sparkHistory ref read directly in WatchlistPanel — updates without triggering re-renders"

key-files:
  created:
    - frontend/components/Sparkline.tsx
    - frontend/components/WatchlistRow.tsx
    - frontend/components/WatchlistPanel.tsx
  modified:
    - frontend/components/AppShell.tsx

key-decisions:
  - "Cast SparkPoint.time as UTCTimestamp (nominal type) — lightweight-charts v5 requires this for setData/update type safety"
  - "WatchlistPanel reads sparkHistory.current directly — ref access avoids re-render on every 500ms tick, sparkline updates piggyback on price state changes"
  - "Flash class reset after 500ms via setTimeout with cleanup — prevents stale animation classes on rapid consecutive ticks"

patterns-established:
  - "Sparkline: chart in useEffect (not render) prevents SSR crash; series.update() for incremental tick, setData() only for initial point"
  - "Row selection: gold left border (#ecad0a) on selected row — Bloomberg-style indicator"

requirements-completed: [WUI-02, WUI-03, WUI-04, WUI-05]

duration: 15min
completed: 2026-03-31
---

# Phase 04 Plan 03: Watchlist Components Summary

**Watchlist panel with per-row price flash animations and lightweight-charts v5 sparklines wired into AppShell**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-31T15:00:00Z
- **Completed:** 2026-03-31T15:14:11Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Sparkline component using lightweight-charts v5 `addSeries(LineSeries)` API — 80x32 canvas, no axes, transparent background, incremental updates
- WatchlistRow with green/red flash animation — 500ms CSS fade via state toggle with timer cleanup
- WatchlistPanel composing WatchlistRow list, reading sparkHistory ref for chart data
- AppShell updated to use WatchlistPanel in place of inline ticker divs; `npm run build` passes clean

## Task Commits

1. **Task 1: Sparkline component** - `6265a9d` (feat)
2. **Task 2: WatchlistRow, WatchlistPanel, AppShell wiring** - `6402a56` (feat)

## Files Created/Modified

- `frontend/components/Sparkline.tsx` — lightweight-charts v5 LineSeries sparkline, 80x32, transparent, no axes
- `frontend/components/WatchlistRow.tsx` — single ticker row with flash-up/flash-down animation, gold selection border
- `frontend/components/WatchlistPanel.tsx` — scrollable list of WatchlistRow; reads sparkHistory MutableRefObject
- `frontend/components/AppShell.tsx` — replaced inline ticker list with WatchlistPanel component

## Decisions Made

- Cast `SparkPoint.time as UTCTimestamp` — lightweight-charts v5 uses a nominal type over `number`; direct assignment fails TypeScript without the cast
- `WatchlistPanel` reads `sparkHistory.current[ticker]` directly from the ref — avoids triggering re-renders on sparkline updates; rows still re-render on `prices` state changes which drives fresh sparkline data
- Flash timer cleanup in `useEffect` return — if a new price tick arrives before 500ms expires, the prior timer is cancelled and a new one starts, preventing stale class stacking

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript type error: SparkPoint not assignable to LineData<Time>**
- **Found during:** Task 1 (Sparkline component)
- **Issue:** `series.setData(points)` and `series.update(point)` rejected `SparkPoint[]` because lightweight-charts v5 uses `UTCTimestamp` (a nominal branded type) for `time`, not plain `number`
- **Fix:** Imported `UTCTimestamp` type; added `toChartPoint` helper casting `p.time as UTCTimestamp`
- **Files modified:** `frontend/components/Sparkline.tsx`
- **Verification:** `npx tsc --noEmit` — no errors
- **Committed in:** `6265a9d` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - type error bug)
**Impact on plan:** Required fix for TypeScript build correctness. No scope creep.

## Issues Encountered

None beyond the UTCTimestamp type cast above.

## Next Phase Readiness

- WUI-02 through WUI-05 satisfied: ticker row shows symbol/price/change%/sparkline, flash animation, sparkline accumulation, selection highlight
- AppShell `selectedTicker` state ready for Phase 5 chart to consume
- No blockers for Phase 5 (main chart area)

## Self-Check: PASSED

- FOUND: frontend/components/Sparkline.tsx
- FOUND: frontend/components/WatchlistRow.tsx
- FOUND: frontend/components/WatchlistPanel.tsx
- FOUND: commit 6265a9d (Sparkline)
- FOUND: commit 6402a56 (WatchlistRow/Panel/AppShell)

---
*Phase: 04-frontend-shell-watchlist*
*Completed: 2026-03-31*
