---
phase: 05-charts-portfolio-trade-ui
plan: 3
status: complete
date: 2026-03-31
---

# Plan 05-03 Summary: Portfolio Panels

## What Was Built

### Task 1: `usePortfolioHistory` hook (`frontend/hooks/usePortfolioHistory.ts`)

One-shot fetch of `GET /api/portfolio/history` on mount. Returns `{ snapshots: PortfolioSnapshot[] }`.

- Exports `PortfolioSnapshot` type: `{ total_value: number, recorded_at: string }`
- Exports `usePortfolioHistory` function
- `'use client'` directive present
- Errors silently caught (`.catch(() => {})`)

### Task 2: `Heatmap` component (`frontend/components/Heatmap.tsx`)

CSS flex treemap of portfolio positions, sized by value and colored by P&L.

- `'use client'` directive present
- Tile width proportional to `pos.value / total * 100` percent with `flexGrow` for fill
- Color: green `rgba(34, 197, 94, alpha)` for profit, red `rgba(239, 68, 68, alpha)` for loss
- Color intensity: `0.15 + min(|unrealized_pnl| / value, 0.4)` capped at 0.55
- Each tile shows ticker symbol and P&L percentage
- Empty state: centered "No positions — buy something to see your portfolio here"

### Task 3: `PnlChart` component (`frontend/components/PnlChart.tsx`)

lightweight-charts v5 AreaSeries chart displaying portfolio total value over time.

- `'use client'` directive present (required — uses canvas/document APIs)
- `createChart` with `autoSize: true`, dark theme matching MainChart
- AreaSeries: `lineColor '#209dd7'`, blue gradient fill
- Converts `recorded_at` ISO string to `UTCTimestamp` via `Math.floor(new Date(s.recorded_at).getTime() / 1000)`
- Empty state overlay: absolute-positioned "Trade to start tracking P&L" message when snapshots is empty
- Chart mounts always; overlay shown conditionally on top

### Task 4: `PositionsTable` component (`frontend/components/PositionsTable.tsx`)

HTML table with 6 columns: Ticker, Qty, Avg Cost, Price, Unr. P&L, Change %.

- `'use client'` directive present
- Computed column: `pnl_pct = (current_price - avg_cost) / avg_cost * 100`
- P&L coloring: green `#22c55e` for profit, red `#ef4444` for loss
- Formatting: prices/P&L to 2 decimal places with `$`, percentages to 1 decimal with sign prefix
- Empty state: single row "No positions" spanning all 6 columns

### Task 5: `PortfolioPanels` wrapper (`frontend/components/PortfolioPanels.tsx`)

Composite panel composing Heatmap, PnlChart, and PositionsTable.

- `'use client'` directive present
- Calls `usePortfolioHistory()` to get snapshots for PnlChart
- Layout: 2-row grid — top 45% (Heatmap) + bottom 55% (2-col: PnlChart | PositionsTable)
- Section headers: "Positions", "P&L", "Holdings" in muted uppercase 10px
- Null portfolio guard: shows "Loading portfolio…" centered message
- `overflow: hidden` at all boundary divs; child components scroll internally

### Task 6: AppShell wired (`frontend/components/AppShell.tsx`)

- Added `import PortfolioPanels from './PortfolioPanels'`
- Replaced the bottom-left placeholder div ("Portfolio panels coming soon") with:
  `<div style={{ borderRight: '1px solid #30363d', overflow: 'hidden' }}><PortfolioPanels portfolio={portfolio} /></div>`

## Verification

`npm run build` exits 0 with no TypeScript errors. Compiled successfully in ~1143ms, TypeScript check passed in ~1273ms.

## Success Criteria

- [x] `usePortfolioHistory` hook exists, fetches `/api/portfolio/history` once on mount, returns `{ snapshots }`
- [x] `Heatmap` tiles sized proportionally to `pos.value / total`, flexGrow for fill
- [x] Heatmap tiles green-tinted for profit, red-tinted for loss, intensity scaled by P&L magnitude
- [x] Heatmap empty state: "No positions — buy something to see your portfolio here"
- [x] `PnlChart` uses `AreaSeries` with `autoSize: true` and `'use client'` directive
- [x] `PnlChart` shows "Trade to start tracking P&L" overlay when snapshots is empty
- [x] `PositionsTable` renders all 6 columns with P&L coloring
- [x] `PositionsTable` shows "No positions" row when positions array is empty
- [x] `PortfolioPanels` composes all three in a 45%/55% row grid with section headers
- [x] AppShell bottom-left cell renders `<PortfolioPanels portfolio={portfolio} />`
- [x] All components have `'use client'` directive
- [x] `npm run build` exits 0 with zero TypeScript errors
