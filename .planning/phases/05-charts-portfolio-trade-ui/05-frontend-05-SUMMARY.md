---
phase: 05-charts-portfolio-trade-ui
plan: 05
subsystem: ui
tags: [react, typescript, lightweight-charts, heatmap, positions-table, trade-bar, chat, sse]

requires:
  - phase: 04-frontend-shell-watchlist
    provides: AppShell grid, usePriceStream (sparkHistory), usePortfolio, Header, WatchlistPanel
  - phase: 03-chat-api
    provides: POST /api/chat with structured output and auto-execute
  - phase: 02-portfolio-watchlist-api
    provides: POST /api/portfolio/trade, GET /api/portfolio/history

provides:
  - Full dashboard: main price chart, portfolio heatmap, P&L chart, positions table, trade bar, AI chat panel

tech-stack:
  added: []
  patterns:
    - Always-mounted chart container — avoids createChart missing DOM node on initial render
    - Deduplicate sparkHistory timestamps before series.setData() — 500ms SSE cadence produces same-second dupes
    - usePortfolio exposes stable refetch() via useCallback for trade-triggered refresh
    - CSS nested grid inside AppShell main area (60%/40% rows, 1fr/380px bottom cols)
    - Hand-rolled CSS flex treemap — no d3/recharts, no SSR risk, 10 positions max

key-files:
  created:
    - frontend/hooks/usePortfolioHistory.ts
    - frontend/hooks/useChat.ts
    - frontend/components/MainChart.tsx
    - frontend/components/Heatmap.tsx
    - frontend/components/PnlChart.tsx
    - frontend/components/PositionsTable.tsx
    - frontend/components/PortfolioPanels.tsx
    - frontend/components/TradeBar.tsx
    - frontend/components/ChatMessage.tsx
    - frontend/components/ChatPanel.tsx
  modified:
    - frontend/hooks/usePortfolio.ts (added refetch())
    - frontend/components/AppShell.tsx (nested grid, all panels wired)
    - backend/app/llm.py (switched to openai/gpt-4o-mini)

key-decisions:
  - "MainChart container always rendered (visibility:hidden when no ticker) — useEffect with [] needs DOM node at mount"
  - "Deduplicate sparkHistory before setData: Map<time,value> keyed by Math.floor(timestamp), sorted ascending"
  - "series.update() wrapped in try/catch — lightweight-charts throws on non-ascending timestamps"
  - "OpenRouter account restricted to openai provider — switched MODEL from openai/gpt-oss-120b to openai/gpt-4o-mini"
  - "EXTRA_BODY provider routing removed — not needed with gpt-4o-mini, was causing 404s"
  - "Heatmap is hand-rolled CSS flex — recharts/d3 add SSR complexity for <=10 positions"
  - "usePortfolio refetch() uses useCallback([]) for stable reference — TradeBar can call it without recreating effect"

patterns-established:
  - "Chat response shape: {message, actions: {trades_executed, trades_failed, watchlist_changes}} — not {trades, watchlist_changes} from spec"
  - "POST /api/portfolio/trade → on success call refetch() immediately, don't wait for 5s poll"
---

## Phase 5 Complete — All 6 Success Criteria Verified

All Phase 5 requirements met and human-verified:

- **SC-1** ✓ Clicking a ticker loads price-over-time chart (dark theme, blue line, live updates)
- **SC-2** ✓ Portfolio heatmap shows positions sized by weight, green=profit / red=loss
- **SC-3** ✓ P&L area chart shows total portfolio value over time from snapshots
- **SC-4** ✓ Positions table: Ticker, Qty, Avg Cost, Price, Unr. P&L, Change %
- **SC-5** ✓ Trade bar: buy/sell updates portfolio immediately without page reload
- **SC-6** ✓ AI chat panel: loading dots, scrolling history, inline trade confirmations

### Bugs fixed during verification
1. **MainChart blank on click** — container div was conditionally rendered; createChart ran on mount when DOM node absent. Fixed by always mounting the container.
2. **Chart blank for some tickers** — duplicate timestamps in sparkHistory (500ms SSE → same integer second). Fixed by deduplicating via Map before setData.
3. **Chat 500 error** — `openai/gpt-oss-120b` routed to `cerebras` provider which is blocked at account level. Fixed by switching to `openai/gpt-4o-mini`.
