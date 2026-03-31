---
phase: 04-frontend-shell-watchlist
plan: 02
subsystem: ui
tags: [react, nextjs, typescript, sse, eventsource, tailwind]

# Dependency graph
requires:
  - phase: 04-01
    provides: "Next.js project scaffold with Tailwind v4, dark theme CSS variables, static export config"

provides:
  - "PriceUpdate, PriceMap, WatchlistItem, Portfolio, PositionItem TypeScript types"
  - "usePriceStream hook — SSE connection to /api/stream/prices with sparkline history buffer"
  - "usePortfolio hook — 5s polling of /api/portfolio"
  - "useWatchlist hook — one-time fetch of /api/watchlist on mount"
  - "AppShell component — two-column grid layout with header, watchlist column, main area placeholder"

affects: [04-03, 04-04, 04-05, 04-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Client hooks use 'use client' directive; page.tsx remains Server Component"
    - "SSE sparkline history kept in useRef to avoid unnecessary re-renders"
    - "AppShell receives all data from hooks and owns ticker selection state"
    - "Inline styles for grid layout to avoid Tailwind v4 arbitrary value syntax differences"

key-files:
  created:
    - frontend/types/market.ts
    - frontend/hooks/usePriceStream.ts
    - frontend/hooks/usePortfolio.ts
    - frontend/hooks/useWatchlist.ts
    - frontend/components/AppShell.tsx
  modified:
    - frontend/app/page.tsx

key-decisions:
  - "sparkHistory kept as useRef (not useState) — avoids re-render on every price tick"
  - "AppShell owns selectedTicker state — single source of truth for chart/watchlist coordination"
  - "void sparkHistory in AppShell to suppress lint — it will be passed to WatchlistRow in plan 04-03"

patterns-established:
  - "Hook pattern: 'use client', typed state, cleanup in useEffect return"
  - "All hooks silently catch fetch errors — UI shows loading state, never crashes"

requirements-completed: [FE-04, WUI-01]

# Metrics
duration: 2min
completed: 2026-03-31
---

# Phase 4 Plan 02: Data Hooks and AppShell Layout Summary

**SSE price stream, portfolio/watchlist polling hooks, and two-column grid AppShell wired together with TypeScript types**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-31T14:47:39Z
- **Completed:** 2026-03-31T14:49:54Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Three data hooks implemented: SSE stream with sparkline accumulation, portfolio 5s polling, watchlist fetch
- Shared TypeScript types covering all backend API response shapes
- AppShell renders dark two-column grid with header spanning full width, 300px watchlist column, main area placeholder
- `npm run build` passes with zero TypeScript errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Define shared TypeScript types** - `72749a9` (feat)
2. **Task 2: Implement data hooks and AppShell layout** - `b3dee18` (feat)

## Files Created/Modified
- `frontend/types/market.ts` - PriceUpdate, PriceMap, WatchlistItem, Portfolio, PositionItem types
- `frontend/hooks/usePriceStream.ts` - EventSource SSE hook with 120-point sparkline history buffer
- `frontend/hooks/usePortfolio.ts` - Portfolio fetch with 5s setInterval refresh
- `frontend/hooks/useWatchlist.ts` - Watchlist ticker list fetch on mount
- `frontend/components/AppShell.tsx` - Root grid layout composing all three hooks
- `frontend/app/page.tsx` - Updated to render AppShell (Server Component wrapper)

## Decisions Made
- sparkHistory is a `useRef` not `useState` — price ticks arrive every 500ms and updating state would cause excessive re-renders; ref accumulates data without triggering renders
- AppShell owns `selectedTicker` state because it coordinates between watchlist and main chart area
- `void sparkHistory` suppresses lint warning; it will be passed to WatchlistRow in plan 04-03

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs
- `AppShell.tsx` main area shows "chart coming in Phase 5" placeholder text — intentional per plan, does not block data layer goal

## Issues Encountered
None.

## Next Phase Readiness
- Plan 04-03 (watchlist UI) can immediately import `usePriceStream`, `useWatchlist`, and types from this plan
- Plan 04-04 (header) can use `usePortfolio` and `usePriceStream` connected status
- sparkHistory ref is ready to be passed as prop to WatchlistRow for sparkline rendering

---
*Phase: 04-frontend-shell-watchlist*
*Completed: 2026-03-31*
