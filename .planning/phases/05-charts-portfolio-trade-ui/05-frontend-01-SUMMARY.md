---
phase: 05-charts-portfolio-trade-ui
plan: 1
type: summary
status: complete
completed_at: "2026-03-31"
commits:
  - bc6d4a5: "refactor(usePortfolio): expose stable refetch callback via useCallback"
  - d0712e1: "feat(AppShell): destructure { portfolio, refetch } and build nested grid main area"
files_modified:
  - frontend/hooks/usePortfolio.ts
  - frontend/components/AppShell.tsx
---

# Plan 05-01 Summary: usePortfolio refetch + AppShell nested grid

## What Was Done

### Task 1: Refactor usePortfolio to expose refetch
- Extracted the fetch function as `useCallback` with `[]` deps for a stable reference
- `useEffect` depends on `fetch_`; because `fetch_` is stable, the interval is created exactly once on mount
- Hook now returns `{ portfolio, refetch: fetch_ }` instead of just `portfolio`
- Eliminates the multiple-interval bug that would occur if fetch_ were recreated on each render

### Task 2: Update AppShell — fix call site and build nested grid
- Destructures `{ portfolio, refetch }` from `usePortfolio()` (previously `const portfolio = usePortfolio()`)
- Passes only `portfolio` to `<Header>` — Header prop type unchanged (`Portfolio | null`)
- Replaced the Phase 4 placeholder main div with a nested CSS grid:
  - Outer: 2 rows (`60% 40%`)
  - Bottom row: 2 columns (`1fr 380px`)
  - Placeholder divs for chart (top), portfolio panels (bottom-left), chat panel (bottom-right)
- `refetch` is destructured but not yet wired to TradeBar — that's Plan 05-04

## Verification

- `npm run build` exits 0 with zero TypeScript errors
- Both files conform to the truths in the plan's `must_haves`

## Key Decisions

- `useCallback(fn, [])` with `useEffect` depending on the stable callback is the correct pattern for a polling hook that must create exactly one interval
- `refetch` is intentionally unused in AppShell for now — TypeScript does not error on unused destructured variables

## Artifacts

| File | Provides |
|------|----------|
| `frontend/hooks/usePortfolio.ts` | Portfolio polling hook with stable refetch callback |
| `frontend/components/AppShell.tsx` | AppShell with nested grid main area |
