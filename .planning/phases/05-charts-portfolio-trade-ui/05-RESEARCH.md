# Phase 5: Charts, Portfolio & Trade UI — Research

**Researched:** 2026-03-31
**Confidence:** HIGH

---

## Summary

Phase 5 replaces the placeholder main area in AppShell with a fully-wired dashboard: a full-size price chart, portfolio heatmap (treemap), P&L chart, positions table, trade bar, and AI chat panel. The core charting library (`lightweight-charts` v5.1.0) is already installed and understood from Phase 4 — the Sparkline component is the direct model for the main chart. No new npm packages are needed: the treemap/heatmap will be hand-rolled with CSS grid (the only positions data is a flat array of up to 10 items — recharts/d3 is overkill and introduces SSR friction). The P&L chart reuses `lightweight-charts` AreaSeries against the `/api/portfolio/history` snapshot data.

The chat panel is a straightforward controlled component: `POST /api/chat` returns `{message, actions}` in one shot (no streaming), so the pattern is send → show loading dots → render response including any trade/watchlist confirmations inline. The trade bar posts to `/api/portfolio/trade` and immediately re-invokes the `usePortfolio` fetch — the existing 5s poll hook just needs a `refetch` escape hatch exposed. All API shapes are confirmed from reading the actual backend router code.

Layout expansion uses nested CSS grid within the existing main area cell. The outer AppShell grid stays as-is (300px watchlist | 1fr main); the main cell is replaced with a `grid` of rows (60% chart / 40% bottom) and the bottom row splits into portfolio-left and chat-right. This keeps the structural change minimal and surgical.

---

## Standard Stack

### Core (already installed)

| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| next | 16.2.1 | Framework, static export | package.json |
| react | 19.2.4 | UI library | package.json |
| react-dom | 19.2.4 | DOM renderer | package.json |
| typescript | ^5 | Type safety | package.json |
| tailwindcss | ^4 | Utility CSS + dark theme | package.json |
| @tailwindcss/postcss | ^4 | v4 PostCSS plugin | package.json |
| lightweight-charts | ^5.1.0 | Main chart + P&L chart (AreaSeries/LineSeries) | package.json |

### New packages needed

None. The treemap is hand-rolled CSS (10 positions max). `lightweight-charts` covers both chart requirements. No additional installs required.

---

## Architecture Patterns

### Layout: Main area grid expansion

The AppShell outer grid stays unchanged. The main area `<div>` becomes an inner grid:

```
┌──────────────────────────────────────────────────────────────┐
│  Header (spans full width — unchanged)                       │
├────────────────┬─────────────────────────────────────────────┤
│  Watchlist     │  MainArea (inner grid)                      │
│  300px fixed   │  ┌────────────────────────────────────────┐ │
│                │  │  MainChart (60vh or 60% of main area)  │ │
│                │  ├──────────────────────┬─────────────────┤ │
│                │  │  PortfolioPanels     │  ChatPanel      │ │
│                │  │  (heatmap + table)   │  (docked right) │ │
│                │  └──────────────────────┴─────────────────┘ │
└────────────────┴─────────────────────────────────────────────┘
```

CSS for the inner main area — replace the placeholder `<div>` in AppShell:

```tsx
// The main area cell gets replaced with this structure
<div style={{
  display: 'grid',
  gridTemplateRows: '60% 40%',
  height: '100%',
  overflow: 'hidden',
}}>
  <MainChart ticker={selectedTicker} sparkHistory={sparkHistory} prices={prices} />
  <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', overflow: 'hidden' }}>
    <PortfolioPanels portfolio={portfolio} />
    <ChatPanel />
  </div>
</div>
```

The chat panel is fixed at 380px wide; portfolio panels take remaining space. Both panels scroll internally (overflow-y: auto on their inner containers).

### Component breakdown

New components to build (all in `frontend/components/`):

| Component | File | Responsibility |
|-----------|------|---------------|
| MainChart | `MainChart.tsx` | Full-size lightweight-charts LineSeries for selected ticker, fed from SSE |
| PortfolioPanels | `PortfolioPanels.tsx` | Wrapper: stacks Heatmap + PositionsTable vertically |
| Heatmap | `Heatmap.tsx` | CSS grid treemap of positions by value, colored by P&L |
| PnlChart | `PnlChart.tsx` | lightweight-charts AreaSeries from portfolio history snapshots |
| PositionsTable | `PositionsTable.tsx` | Table: ticker, qty, avg cost, current price, unrealized P&L, % change |
| TradeBar | `TradeBar.tsx` | Ticker input + quantity input + Buy/Sell buttons |
| ChatPanel | `ChatPanel.tsx` | Message history + input + loading indicator |
| ChatMessage | `ChatMessage.tsx` | Single message bubble, handles trade confirmation variant |

New hooks:

| Hook | File | Responsibility |
|------|------|---------------|
| usePortfolioHistory | `hooks/usePortfolioHistory.ts` | Fetch `/api/portfolio/history` on mount; returns snapshot array |
| useChat | `hooks/useChat.ts` | Chat state: messages array, loading bool, sendMessage function |
| useRefetchPortfolio | (extend existing) | Expose a `refetch()` from `usePortfolio` for post-trade refresh |

### Pattern: Main chart with lightweight-charts v5

Directly modeled on `Sparkline.tsx` — same library, same API, different options. Key differences from the sparkline: axes visible, crosshair enabled, auto-size to container, `fitContent()` called after data load.

```tsx
// MainChart.tsx — 'use client'
import { createChart, LineSeries, ColorType, CrosshairMode } from 'lightweight-charts'
import type { IChartApi, ISeriesApi, UTCTimestamp } from 'lightweight-charts'
import { useEffect, useRef } from 'react'
import type { MutableRefObject } from 'react'
import type { SparkHistory } from '@/hooks/usePriceStream'
import type { PriceMap } from '@/types/market'

export default function MainChart({ ticker, sparkHistory, prices }: MainChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const chartRef = useRef<IChartApi | null>(null)
  const seriesRef = useRef<ISeriesApi<'Line'> | null>(null)
  const prevTickerRef = useRef<string | null>(null)

  // Create chart once on mount
  useEffect(() => {
    if (!containerRef.current) return
    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0d1117' },
        textColor: '#8b949e',
      },
      grid: {
        vertLines: { color: '#21262d' },
        horzLines: { color: '#21262d' },
      },
      crosshair: { mode: CrosshairMode.Normal },
      rightPriceScale: { borderColor: '#30363d' },
      timeScale: { borderColor: '#30363d', timeVisible: true },
      autoSize: true,  // fills container — no fixed width/height needed
    })
    const series = chart.addSeries(LineSeries, {
      color: '#209dd7',
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: true,
    })
    chartRef.current = chart
    seriesRef.current = series
    return () => { chart.remove(); chartRef.current = null; seriesRef.current = null }
  }, [])

  // When ticker changes: load history from sparkHistory ref, fitContent
  useEffect(() => {
    const series = seriesRef.current
    const chart = chartRef.current
    if (!series || !chart || !ticker) return
    if (ticker !== prevTickerRef.current) {
      const history = sparkHistory.current[ticker] ?? []
      series.setData(history.map(p => ({ time: p.time as UTCTimestamp, value: p.value })))
      chart.timeScale().fitContent()
      prevTickerRef.current = ticker
    }
  }, [ticker, sparkHistory])

  // Append new price point as SSE ticks arrive
  useEffect(() => {
    const series = seriesRef.current
    if (!series || !ticker) return
    const update = prices[ticker]
    if (!update) return
    series.update({ time: Math.floor(update.timestamp) as UTCTimestamp, value: update.price })
  }, [prices, ticker])

  return (
    <div style={{ backgroundColor: '#0d1117', borderBottom: '1px solid #30363d', height: '100%' }}>
      {ticker ? (
        <>
          <div style={{ padding: '6px 12px', color: '#e6edf3', fontSize: 12, fontFamily: 'monospace' }}>
            {ticker}
          </div>
          <div ref={containerRef} style={{ height: 'calc(100% - 28px)' }} />
        </>
      ) : (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#8b949e', fontSize: 12 }}>
          Select a ticker to view chart
        </div>
      )}
    </div>
  )
}
```

Key points:
- `autoSize: true` eliminates need for a ResizeObserver — lightweight-charts v5 handles it internally
- History comes from `sparkHistory` ref (already accumulated in `usePriceStream`), not a separate API call
- Each SSE tick appends via `series.update()` — same pattern as Sparkline, no full re-render

### Pattern: P&L Chart (AreaSeries)

```tsx
// PnlChart.tsx — fetch /api/portfolio/history, render AreaSeries
import { AreaSeries, ColorType, createChart } from 'lightweight-charts'

// In useEffect:
const series = chart.addSeries(AreaSeries, {
  lineColor: '#209dd7',
  topColor: 'rgba(32, 157, 215, 0.3)',
  bottomColor: 'rgba(32, 157, 215, 0.0)',
  lineWidth: 2,
  priceLineVisible: false,
  lastValueVisible: true,
})

// Data from GET /api/portfolio/history:
// { snapshots: [{ total_value: number, recorded_at: string }] }
// Convert recorded_at ISO string to Unix timestamp for lightweight-charts:
const data = snapshots.map(s => ({
  time: Math.floor(new Date(s.recorded_at).getTime() / 1000) as UTCTimestamp,
  value: s.total_value,
}))
series.setData(data)
chart.timeScale().fitContent()
```

The hook `usePortfolioHistory` fetches once on mount. No polling needed — the P&L chart is historical context, not live. After a trade the user can see the update on the next snapshot (30s cadence) or via a manual re-fetch hook.

### Pattern: Treemap/Heatmap

Recharts and d3 are not installed and introduce SSR risk. With at most 10 positions, a hand-rolled CSS flex/grid treemap is simple and sufficient.

Approach: normalize each position's `value` as a percentage of total positions value, render as horizontal bars or a simple proportional flex layout. Color maps P&L sign: green tones for profit, red for loss. The exact pixel-perfect treemap layout algorithm is unnecessary — proportional flex rows per position convey the same information.

```tsx
// Heatmap.tsx
// portfolio.positions: PositionItem[] — already has value, unrealized_pnl
function Heatmap({ portfolio }: { portfolio: Portfolio }) {
  const total = portfolio.positions.reduce((s, p) => s + p.value, 0) || 1
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 2, padding: 8, height: '100%' }}>
      {portfolio.positions.map(pos => {
        const pct = (pos.value / total) * 100
        const isProfit = pos.unrealized_pnl >= 0
        const intensity = Math.min(Math.abs(pos.unrealized_pnl) / pos.value, 0.4)  // cap at 40%
        const bg = isProfit
          ? `rgba(34, 197, 94, ${0.15 + intensity})`
          : `rgba(239, 68, 68, ${0.15 + intensity})`
        const pnlPct = pos.avg_cost > 0
          ? ((pos.current_price - pos.avg_cost) / pos.avg_cost * 100).toFixed(1)
          : '0.0'
        return (
          <div
            key={pos.ticker}
            style={{
              width: `calc(${pct}% - 2px)`,
              minWidth: 48,
              backgroundColor: bg,
              border: '1px solid #30363d',
              borderRadius: 4,
              padding: '4px 6px',
              flexGrow: pct,
              flexShrink: 0,
            }}
          >
            <div style={{ color: '#e6edf3', fontSize: 11, fontFamily: 'monospace', fontWeight: 600 }}>
              {pos.ticker}
            </div>
            <div style={{ color: isProfit ? '#22c55e' : '#ef4444', fontSize: 10 }}>
              {isProfit ? '+' : ''}{pnlPct}%
            </div>
          </div>
        )
      })}
    </div>
  )
}
```

This renders with no SSR issues, no extra packages, and scales correctly when positions are empty (no render).

### Pattern: Positions Table

Straightforward HTML table with monospace font. The `PositionItem` type is already defined in `types/market.ts`:

```
{ ticker, quantity, avg_cost, current_price, unrealized_pnl, value }
```

Computed column: `pnl_pct = (current_price - avg_cost) / avg_cost * 100`.

Color rule: `unrealized_pnl >= 0` → green (`#22c55e`), else red (`#ef4444`).

Empty state: render a single row with "No positions" when `portfolio.positions.length === 0`.

### Pattern: Trade bar with immediate portfolio refresh

The `usePortfolio` hook currently uses a closed `setInterval`. Expose a `refetch` function by moving the fetch out:

```typescript
// usePortfolio.ts — add refetch to return value
export function usePortfolio() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null)

  const fetch_ = useCallback(() =>
    fetch('/api/portfolio')
      .then(r => r.json())
      .then((data: Portfolio) => setPortfolio(data))
      .catch(() => {}),
  [])

  useEffect(() => {
    fetch_()
    const interval = setInterval(fetch_, 5000)
    return () => clearInterval(interval)
  }, [fetch_])

  return { portfolio, refetch: fetch_ }
}
```

TradeBar component:

```tsx
async function handleTrade(side: 'buy' | 'sell') {
  if (!ticker || !quantity) return
  setSubmitting(true)
  try {
    const res = await fetch('/api/portfolio/trade', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticker: ticker.toUpperCase(), quantity: parseFloat(quantity), side }),
    })
    if (!res.ok) {
      const err = await res.json()
      setError(err.detail ?? 'Trade failed')
    } else {
      setTicker('')
      setQuantity('')
      setError(null)
      refetch()  // immediate portfolio refresh — don't wait for 5s poll
    }
  } finally {
    setSubmitting(false)
  }
}
```

No optimistic UI — the trade is fast (instant fill at current price, no network latency to an exchange). Simple fetch → success → refetch is correct here.

POST response on success: `{ status: "ok", ticker, side, quantity, price }`
POST response on failure: HTTP 400 with `{ detail: "Insufficient cash" }` or `{ detail: "Insufficient shares" }`

### Pattern: Chat UI auto-scroll

```tsx
// ChatPanel.tsx
const messagesEndRef = useRef<HTMLDivElement>(null)

useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
}, [messages])

// In JSX:
<div style={{ overflowY: 'auto', flex: 1 }}>
  {messages.map((m, i) => <ChatMessage key={i} msg={m} />)}
  <div ref={messagesEndRef} />
</div>
```

### Pattern: Loading indicator

Pure CSS animated dots — no library. Add to `globals.css`:

```css
.loading-dots span {
  animation: blink 1.2s infinite;
  animation-fill-mode: both;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes blink {
  0%, 80%, 100% { opacity: 0; }
  40% { opacity: 1; }
}
```

In JSX: `<span className="loading-dots"><span>.</span><span>.</span><span>.</span></span>`

### Pattern: Chat state hook

```typescript
// hooks/useChat.ts
export type ChatMessage = {
  role: 'user' | 'assistant'
  content: string
  actions?: ChatActions  // from the response body
}

export type ChatActions = {
  trades_executed: TradeResult[]
  trades_failed: TradeResult[]
  watchlist_changes: WatchlistResult[]
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(false)

  async function sendMessage(text: string) {
    setMessages(prev => [...prev, { role: 'user', content: text }])
    setLoading(true)
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      })
      const data = await res.json()  // { message: string, actions: ChatActions }
      setMessages(prev => [...prev, { role: 'assistant', content: data.message, actions: data.actions }])
    } finally {
      setLoading(false)
    }
  }

  return { messages, loading, sendMessage }
}
```

### Pattern: Inline trade confirmation in chat

The `ChatMessage` component checks `msg.actions` to render confirmations below the text bubble:

```tsx
function ChatMessage({ msg }: { msg: ChatMsg }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ /* bubble styles based on msg.role */ }}>
        {msg.content}
      </div>
      {msg.actions && (
        <div style={{ marginTop: 4, fontSize: 11, color: '#8b949e' }}>
          {msg.actions.trades_executed.map(t => (
            <div key={t.ticker} style={{ color: '#22c55e' }}>
              Executed: {t.side.toUpperCase()} {t.quantity} {t.ticker} @ ${t.price?.toFixed(2)}
            </div>
          ))}
          {msg.actions.trades_failed.map(t => (
            <div key={t.ticker} style={{ color: '#ef4444' }}>
              Failed: {t.side.toUpperCase()} {t.ticker} — {t.error}
            </div>
          ))}
          {msg.actions.watchlist_changes.map(w => (
            <div key={w.ticker} style={{ color: '#ecad0a' }}>
              Watchlist: {w.action === 'add' ? 'Added' : 'Removed'} {w.ticker}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
```

---

## Don't Hand-Roll

| Problem | Use Instead |
|---------|-------------|
| Main chart rendering | `lightweight-charts` v5 `LineSeries` — already installed, pattern established in Sparkline.tsx |
| P&L chart rendering | `lightweight-charts` v5 `AreaSeries` — same library, same mount pattern |
| Chart resize handling | `autoSize: true` in `createChart` options — built-in to v5, no ResizeObserver needed |
| CSS transitions for loading dots | Plain CSS `@keyframes` — Tailwind animate utilities work too but globals.css is simpler |
| SSE reconnection | `EventSource` handles it automatically — already wired in `usePriceStream` |

---

## Common Pitfalls

### 1. lightweight-charts autoSize requires measured container
`autoSize: true` works only when the container div has a defined height at mount time. With CSS grid rows set to `60%` / `40%`, the container is sized before React mounts — this is fine. Pitfall: if the container has `height: 0` or `height: auto` with no grid constraint, the chart renders at zero height. Fix: ensure the outer grid row has an explicit `minHeight` or the grid row definition is non-zero.

### 2. lightweight-charts must be 'use client' — enforce strictly
`createChart` uses `document` and canvas APIs. All chart components and the Sparkline already have `'use client'`. New chart components (MainChart, PnlChart) must also have `'use client'` at the top. Next.js static export doesn't do SSR at runtime but it does at build time — missing `'use client'` causes build failure.

### 3. UTCTimestamp type is nominal over number
lightweight-charts requires `time` fields typed as `UTCTimestamp` (a branded number). Always cast: `Math.floor(timestamp) as UTCTimestamp`. Forgetting the cast causes a TypeScript error even though the runtime value is correct.

### 4. series.update() rejects out-of-order timestamps
SSE events may arrive with the same or slightly earlier timestamp if two updates fire within the same second. `Math.floor(update.timestamp)` as the time means two updates in the same second get the same integer — `series.update()` will silently skip the duplicate. This is benign for the chart but means the chart updates at ~1Hz effective rate despite 500ms SSE cadence. Acceptable for a main chart.

### 5. Chat POST blocks on slow LLM response
`POST /api/chat` is synchronous (not streaming) — it can take 2-10 seconds. The `loading` state in `useChat` must be set before the fetch and cleared in a `finally` block. The input should be disabled while loading is true to prevent double-sends.

### 6. Trade bar: ticker must be uppercased before POST
The backend does `trade.ticker.upper()` internally, but showing lowercase ticker symbols in the UI looks wrong. Call `.toUpperCase()` on the ticker state value in the display or before submit.

### 7. usePortfolio refetch and interval cleanup
When adding a `refetch` callback to `usePortfolio` using `useCallback`, the `fetch_` reference must be stable (no dependency changes) to avoid the `useEffect` re-running and creating multiple intervals. Use `useCallback` with `[]` dependencies.

### 8. Heatmap with zero positions
When `portfolio.positions` is empty, the heatmap container renders empty. Show a placeholder message: "No positions — buy something to see your portfolio here."

### 9. P&L chart with zero snapshots
`GET /api/portfolio/history` returns `{ snapshots: [] }` when no trades have occurred (first launch). `series.setData([])` is valid and renders an empty chart. Show a label or subtitle: "Trade to start tracking P&L".

### 10. AppShell refactor: usePortfolio return type change
If `usePortfolio` is changed to return `{ portfolio, refetch }` instead of just `portfolio`, the Header component (which currently receives `portfolio` from AppShell) needs to be updated to destructure correctly. All call sites must be updated together.

---

## Phase Requirements Map

| Req | Component | API | Notes |
|-----|-----------|-----|-------|
| CHART-01 | `MainChart.tsx` | SSE `/api/stream/prices` | History from `sparkHistory` ref; live updates via `prices` prop |
| CHART-02 | `Heatmap.tsx` | `GET /api/portfolio` (via `usePortfolio`) | CSS flex treemap; `PositionItem.value` + `unrealized_pnl` for sizing+color |
| CHART-03 | `PnlChart.tsx` | `GET /api/portfolio/history` | `AreaSeries`; ISO timestamps converted to UTCTimestamp |
| CHART-04 | `PositionsTable.tsx` | `GET /api/portfolio` (via `usePortfolio`) | All fields already in `PositionItem` type; compute `pnl_pct` client-side |
| TRADE-01 | `TradeBar.tsx` | — | Controlled inputs for ticker + quantity; Buy/Sell buttons |
| TRADE-02 | `TradeBar.tsx` + `usePortfolio` | `POST /api/portfolio/trade` | `refetch()` called on success; no page reload |
| CUI-01 | `ChatPanel.tsx` + `useChat` | — | `useRef` scroll-to-bottom on message append |
| CUI-02 | `ChatPanel.tsx` | — | CSS `@keyframes blink` loading dots; input disabled while loading |
| CUI-03 | `ChatMessage.tsx` | `POST /api/chat` | `actions.trades_executed`, `actions.trades_failed`, `actions.watchlist_changes` rendered inline |

---

## API Shape Reference (confirmed from backend source)

### GET /api/portfolio
```json
{
  "cash_balance": 9500.00,
  "total_value": 10200.00,
  "positions": [
    {
      "ticker": "AAPL",
      "quantity": 5.0,
      "avg_cost": 190.00,
      "current_price": 192.50,
      "unrealized_pnl": 12.50,
      "value": 962.50
    }
  ]
}
```

### GET /api/portfolio/history
```json
{
  "snapshots": [
    { "total_value": 10000.0, "recorded_at": "2026-03-31T10:00:00+00:00" }
  ]
}
```

### POST /api/portfolio/trade
Request: `{ "ticker": "AAPL", "quantity": 5, "side": "buy" }`
Success (200): `{ "status": "ok", "ticker": "AAPL", "side": "buy", "quantity": 5.0, "price": 192.50 }`
Error (400): `{ "detail": "Insufficient cash" }` or `{ "detail": "Insufficient shares" }`

### POST /api/chat
Request: `{ "message": "Buy 10 shares of AAPL" }`
Response: `{ "message": "Done! Bought 10 AAPL...", "actions": { "trades_executed": [...], "trades_failed": [...], "watchlist_changes": [...] } }`

Each `trades_executed` item: `{ ticker, side, quantity, price, error: null }`
Each `trades_failed` item: `{ ticker, side, quantity, price, error: "Insufficient cash" }`
Each `watchlist_changes` item: `{ ticker, action: "add"|"remove", applied: true|false }`

---

## Sources

- `/Users/steve/projects/finally/frontend/package.json` — confirmed `lightweight-charts ^5.1.0`, no recharts/d3
- `/Users/steve/projects/finally/frontend/components/Sparkline.tsx` — confirmed v5 API: `createChart`, `addSeries(LineSeries, ...)`, `autoSize` option, `UTCTimestamp` cast pattern
- `/Users/steve/projects/finally/frontend/components/AppShell.tsx` — confirmed 2-col grid structure to expand
- `/Users/steve/projects/finally/frontend/hooks/usePriceStream.ts` — confirmed `sparkHistory` is a `MutableRefObject<SparkHistory>` with `{ time: number, value: number }[]` per ticker
- `/Users/steve/projects/finally/frontend/hooks/usePortfolio.ts` — confirmed current return type is `Portfolio | null`; refetch pattern planned
- `/Users/steve/projects/finally/frontend/types/market.ts` — confirmed `Portfolio`, `PositionItem` types already defined
- `/Users/steve/projects/finally/backend/app/routers/portfolio.py` — confirmed exact response shapes for GET/POST portfolio endpoints; confirmed trade error messages
- `/Users/steve/projects/finally/backend/app/routers/chat.py` — confirmed response: `{ message, actions: { trades_executed, trades_failed, watchlist_changes } }`
- `/Users/steve/projects/finally/.planning/phases/04-frontend-shell-watchlist/RESEARCH.md` — lightweight-charts v5 API patterns, Tailwind v4 patterns, SSR gotchas
- `/Users/steve/projects/finally/.planning/phases/04-frontend-shell-watchlist/04-frontend-04-SUMMARY.md` — confirmed Phase 4 complete; all 10 SC criteria verified
