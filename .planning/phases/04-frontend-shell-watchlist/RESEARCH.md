# Phase 4 Research: Frontend Shell & Watchlist

**Researched:** 2026-03-31
**Domain:** Next.js 15 static export, React 19, Tailwind CSS v4, SSE/EventSource, Lightweight Charts v5
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FE-01 | Next.js app builds as static export and is served by FastAPI at root | Static export config + FastAPI static mount already in main.py |
| FE-02 | Dark terminal aesthetic with correct color scheme (bg ~#0d1117, accent #ecad0a, blue #209dd7, purple #753991) | Tailwind v4 CSS custom properties pattern |
| FE-03 | Header shows live portfolio total value, cash balance, and connection status indicator | SSE readyState + GET /api/portfolio polling |
| FE-04 | SSE connection established on page load via EventSource; reconnects automatically | Native EventSource with built-in retry + custom hook |
| WUI-01 | Watchlist panel shows all watched tickers in a grid/table | GET /api/watchlist + SSE price updates |
| WUI-02 | Each ticker row shows symbol, current price, daily change %, and a sparkline | SSE PriceUpdate shape has change_percent; sparkline via lightweight-charts LineSeries |
| WUI-03 | Price updates flash green (uptick) or red (downtick) with ~500ms CSS fade | CSS class toggle + Tailwind transition utilities |
| WUI-04 | Sparklines accumulate price history from SSE stream since page load | Local useRef/useState array per ticker |
| WUI-05 | Clicking a ticker selects it and loads it in the main chart area | React state selectedTicker; placeholder panel in phase 4 |
</phase_requirements>

---

## Current State

### Frontend Directory

The `frontend/` directory is completely empty — only the directory itself exists (created 2026-03-27). No `package.json`, no Next.js scaffold, nothing. The entire Next.js project must be initialized from scratch.

### Backend Static Serving

`backend/main.py` already has the static mount wired up:

```python
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
```

The mount is conditional — if `backend/static/` does not exist, the backend starts without it (no crash). The Next.js build output must be placed at `backend/static/`.

---

## API Endpoints Available

All endpoints are live from Phase 2 and 3. These are the endpoints Phase 4 needs:

| Endpoint | Method | Response Shape | Phase 4 Use |
|----------|--------|----------------|-------------|
| `/api/stream/prices` | SSE GET | `data: {TICKER: {ticker, price, previous_price, timestamp, change, change_percent, direction}}` | Live price updates for all watchlist tickers |
| `/api/portfolio` | GET | `{cash_balance, positions: [{ticker, quantity, avg_cost, current_price, unrealized_pnl, value}], total_value}` | Header: total_value + cash_balance |
| `/api/watchlist` | GET | `{watchlist: [{ticker, price}]}` | Initial watchlist load |
| `/api/health` | GET | `{status: "ok"}` | Optional connection check |

### SSE Event Format (exact)

The backend streams a single data event every ~500ms when prices change:

```
retry: 1000

data: {"AAPL": {"ticker": "AAPL", "price": 190.50, "previous_price": 190.20, "timestamp": 1711900000.0, "change": 0.3, "change_percent": 0.1577, "direction": "up"}, ...}
```

Key fields for the watchlist UI:
- `price` — current price to display
- `change_percent` — daily change % to display (note: this is change from the PREVIOUS update, not opening price — suitable for showing live movement)
- `direction` — `"up"` / `"down"` / `"flat"` — drives flash color

---

## Technical Findings

### Next.js Project Setup

**Version:** Next.js 16.2.1 (latest as of research date)
**React:** 19.2.4 (Next.js 16 peer dep supports React 18 or 19)
**TypeScript:** 6.0.2

Initialize with `create-next-app`:

```bash
npx create-next-app@latest . --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*"
```

This scaffolds:
- `app/` directory (App Router)
- `app/layout.tsx` (root layout)
- `app/page.tsx` (root page)
- `app/globals.css` with Tailwind import
- `next.config.ts`
- `tsconfig.json`
- `postcss.config.mjs`
- `tailwind.config.ts` (v4: may be empty or absent — config moves to CSS)

### Next.js Static Export Configuration

Add `output: 'export'` to `next.config.ts`:

```typescript
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'export',
  distDir: '../backend/static',  // Output directly into FastAPI's static dir
  images: {
    unoptimized: true,  // Required for static export — no server-side image optimization
  },
}

export default nextConfig
```

Setting `distDir: '../backend/static'` means `npm run build` drops the export directly where FastAPI expects it. This avoids a manual copy step.

**Static export limitations to know:**
- No Server Actions (not needed — all data fetching is client-side via fetch/SSE)
- No middleware/rewrites/redirects (not needed)
- No dynamic routes with `dynamicParams: true` (not needed — single-page app)
- Image optimization requires `unoptimized: true` or custom loader (use `unoptimized: true`)

**Confidence:** HIGH — verified against Next.js 16.2.1 official docs.

### Tailwind CSS v4 Setup

Tailwind v4 (4.2.2) is a breaking change from v3. Key differences:

1. No `tailwind.config.js` with theme extension (config moves to CSS)
2. PostCSS plugin is `@tailwindcss/postcss`, not `tailwindcss`
3. CSS import is `@import "tailwindcss"` (single line, not three directives)
4. Custom theme values defined with CSS custom properties in globals.css

`postcss.config.mjs`:
```javascript
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
export default config;
```

`app/globals.css`:
```css
@import "tailwindcss";

@theme {
  --color-bg-primary: #0d1117;
  --color-bg-secondary: #1a1a2e;
  --color-accent: #ecad0a;
  --color-blue-primary: #209dd7;
  --color-purple-secondary: #753991;
  --color-green-uptick: #22c55e;
  --color-red-downtick: #ef4444;
  --color-border: #30363d;
  --color-text-primary: #e6edf3;
  --color-text-muted: #8b949e;
}
```

In Tailwind v4, `@theme` custom properties become utility classes automatically: `bg-bg-primary`, `text-accent`, etc.

**Confidence:** HIGH — verified against Tailwind CSS 4.2.2 official docs.

### SSE Connection Pattern

Use native `EventSource` inside a `useEffect` hook. The backend sends `retry: 1000` so EventSource will auto-reconnect after 1 second on disconnect.

Custom hook pattern (no library needed):

```typescript
// hooks/usePriceStream.ts
'use client'

import { useState, useEffect, useRef } from 'react'

export type PriceUpdate = {
  ticker: string
  price: number
  previous_price: number
  timestamp: number
  change: number
  change_percent: number
  direction: 'up' | 'down' | 'flat'
}

export type PriceMap = Record<string, PriceUpdate>

export function usePriceStream() {
  const [prices, setPrices] = useState<PriceMap>({})
  const [connected, setConnected] = useState(false)
  const esRef = useRef<EventSource | null>(null)

  useEffect(() => {
    const es = new EventSource('/api/stream/prices')
    esRef.current = es

    es.onopen = () => setConnected(true)
    es.onerror = () => setConnected(false)
    es.onmessage = (event) => {
      const data: PriceMap = JSON.parse(event.data)
      setPrices(prev => ({ ...prev, ...data }))
    }

    return () => {
      es.close()
      esRef.current = null
    }
  }, [])

  return { prices, connected }
}
```

**Key points:**
- `EventSource` is a browser API — components using this hook must be `'use client'`
- The backend streams ALL watchlist tickers in every event — no per-ticker subscription needed
- `connected` tracks `readyState` via open/error events; drives the header status dot
- Price accumulation for sparklines: maintain a separate `Map<string, number[]>` alongside prices

**Confidence:** HIGH — matches backend SSE format verified in stream.py.

### Sparkline Implementation

**Recommendation: lightweight-charts v5 for sparklines.** Reasoning:
- Canvas-based (no DOM thrashing at 500ms update rate)
- TradingView quality — fits the Bloomberg terminal aesthetic
- v5.1.0 is the latest stable release
- The same library will be used for the main chart in Phase 5

**v5 API (breaking change from v4):**

```typescript
// v5: import the series class, use addSeries()
import { createChart, LineSeries } from 'lightweight-charts'

const chart = createChart(container, { ... })
const series = chart.addSeries(LineSeries, { color: '#209dd7', lineWidth: 1 })
series.setData([{ time: 1711900000 as UTCTimestamp, value: 190.5 }])
```

For sparklines (minimal chart with no axes, no interactions):

```typescript
const chart = createChart(containerRef.current, {
  layout: {
    background: { type: ColorType.Solid, color: 'transparent' },
    textColor: 'transparent',
  },
  grid: { vertLines: { visible: false }, horzLines: { visible: false } },
  leftPriceScale: { visible: false },
  rightPriceScale: { visible: false },
  timeScale: { visible: false },
  crosshair: { mode: CrosshairMode.Hidden },
  handleScroll: false,
  handleScale: false,
  width: 80,
  height: 32,
})
```

**Important for static export + SSR:** lightweight-charts uses `window` and canvas APIs. Components that use it must be `'use client'` and chart creation must happen in `useEffect` (not during render).

**Alternative considered: SVG sparklines (custom)** — simpler but requires manual D3-style math. The overhead of lightweight-charts is justified by Phase 5 reuse.

**Confidence:** HIGH — verified against lightweight-charts 5.1.0 docs and release notes.

### Price Flash Animation

Use CSS classes toggled via `setTimeout`. No animation library needed.

Pattern:
1. On price update, compare `direction` from SSE event
2. Add `flash-up` or `flash-down` class to the price cell
3. After 500ms, remove the class (CSS transition handles the fade)

```css
/* In globals.css */
.flash-up {
  animation: flash-green 500ms ease-out;
}
.flash-down {
  animation: flash-red 500ms ease-out;
}

@keyframes flash-green {
  0% { background-color: rgba(34, 197, 94, 0.4); }
  100% { background-color: transparent; }
}
@keyframes flash-red {
  0% { background-color: rgba(239, 68, 68, 0.4); }
  100% { background-color: transparent; }
}
```

In React:
```typescript
const [flashClass, setFlashClass] = useState('')

useEffect(() => {
  if (direction === 'flat') return
  const cls = direction === 'up' ? 'flash-up' : 'flash-down'
  setFlashClass(cls)
  const timer = setTimeout(() => setFlashClass(''), 500)
  return () => clearTimeout(timer)
}, [price, direction])  // re-triggers on every price change
```

**Confidence:** HIGH — standard CSS animation pattern, no library dependencies.

### Layout Architecture

Single-page app. Phase 4 only implements the header + watchlist panel. Phase 5 adds the rest.

Recommended layout grid (Phase 4 scaffolds the full grid, partially filled):

```
┌─────────────────────────────────────────────────────────────┐
│  Header: logo | total value | cash balance | connection dot │
├───────────────┬─────────────────────────────────────────────┤
│  Watchlist    │  Main Chart Area (placeholder in Phase 4)   │
│  Panel        │                                             │
│  (WUI-01..05) │                                             │
├───────────────┼─────────────────────────────────────────────┤
│               │  Portfolio / Trade panels (Phase 5)         │
└───────────────┴─────────────────────────────────────────────┘
```

CSS Grid is appropriate for this layout. The watchlist column has a fixed width (~280-320px); the main area takes remaining space.

```css
/* Root layout grid */
.app-grid {
  display: grid;
  grid-template-rows: auto 1fr;
  grid-template-columns: 300px 1fr;
  height: 100vh;
  background: #0d1117;
}
```

### Portfolio Header Data

The header needs `total_value` and `cash_balance`. These do NOT come from SSE — they come from polling `GET /api/portfolio`.

Pattern: poll `/api/portfolio` every 5 seconds (or on mount). SSE does not include portfolio value.

```typescript
// hooks/usePortfolio.ts
'use client'

import { useState, useEffect } from 'react'

export function usePortfolio() {
  const [portfolio, setPortfolio] = useState<{ total_value: number; cash_balance: number } | null>(null)

  useEffect(() => {
    const fetchPortfolio = () =>
      fetch('/api/portfolio')
        .then(r => r.json())
        .then(setPortfolio)
        .catch(() => {})

    fetchPortfolio()
    const interval = setInterval(fetchPortfolio, 5000)
    return () => clearInterval(interval)
  }, [])

  return portfolio
}
```

**Confidence:** HIGH — matches GET /api/portfolio response shape confirmed in portfolio.py.

### Component Structure Recommendation

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout: HTML shell, globals.css import
│   ├── page.tsx            # Single page: renders AppShell
│   └── globals.css         # Tailwind import + theme custom properties + animations
├── components/
│   ├── AppShell.tsx        # Outer grid layout, composes Header + Watchlist + MainArea
│   ├── Header.tsx          # Portfolio total, cash, connection status dot
│   ├── WatchlistPanel.tsx  # Scrollable list of WatchlistRow
│   ├── WatchlistRow.tsx    # Ticker, price, change%, sparkline, click handler
│   ├── Sparkline.tsx       # Lightweight-charts wrapper, 'use client'
│   └── MainArea.tsx        # Placeholder for Phase 5 chart
├── hooks/
│   ├── usePriceStream.ts   # SSE connection + price state
│   └── usePortfolio.ts     # Portfolio polling
├── types/
│   └── market.ts           # PriceUpdate, WatchlistItem types
├── next.config.ts
├── postcss.config.mjs
├── tsconfig.json
└── package.json
```

All components that use SSE, EventSource, or browser APIs must be `'use client'`. Server Components work in static export but only run at build time — for this SPA all meaningful work is client-side.

---

## Key Decisions

| Decision | Choice | Reason |
|----------|--------|--------|
| Charting library | lightweight-charts v5.1.0 | Canvas-based, TradingView quality, reused in Phase 5 for main chart; no React wrapper needed (direct DOM ref) |
| Tailwind version | v4.2.2 (latest) | Already what `create-next-app` installs in 2025; CSS-first config is cleaner for custom theme |
| SSE management | Custom hook (no library) | Native EventSource is sufficient; backend handles retry; no auth headers needed |
| Portfolio polling | Simple setInterval (no SWR/React Query) | Only one endpoint, 5s interval, minimal complexity; SWR adds unnecessary dependency |
| Next.js router | App Router (not Pages Router) | Default in Next.js 15/16; static export fully supported |
| `distDir` | `'../backend/static'` | Eliminates manual copy step; `npm run build` in `frontend/` drops files where FastAPI expects them |
| Image optimization | `unoptimized: true` | Required for static export; no images in this app anyway |
| `'use client'` boundary | At hook level + Sparkline component | Keeps server-rendered shell lean; all real-time components opt into client rendering |

---

## Risks & Gotchas

### 1. SSR vs Browser-only APIs
**What goes wrong:** `EventSource`, `window`, canvas — all crash during Next.js build-time SSR if called outside `useEffect`.
**Prevention:** Any component using these must have `'use client'` directive. Never call `new EventSource()` at module level. lightweight-charts chart creation MUST be inside `useEffect`.

### 2. `distDir` Relative Path
**What goes wrong:** `distDir: '../backend/static'` is relative to the `frontend/` project root. If `npm run build` is run from a different working directory, the path resolves differently.
**Prevention:** Always run `npm run build` from inside `frontend/`. The Dockerfile multi-stage build should `WORKDIR /app/frontend && npm run build`.

### 3. Tailwind v4 Breaking Change from v3
**What goes wrong:** Generating the project with an older template may produce v3 config (`tailwind.config.js` + `@tailwind base/components/utilities` directives) that does NOT work with v4.
**Prevention:** Use `npx create-next-app@latest` which scaffolds for the latest Tailwind. Verify `package.json` shows `tailwindcss: ^4.x`. The v4 `globals.css` only needs `@import "tailwindcss"`.

### 4. lightweight-charts v5 API (Breaking from v4)
**What goes wrong:** StackOverflow and older tutorials show `chart.addLineSeries()` — this was removed in v5.
**Prevention:** Use `chart.addSeries(LineSeries, options)` pattern. Import `LineSeries` from `'lightweight-charts'`.

### 5. Sparkline Update Performance
**What goes wrong:** Calling `series.setData(allHistory)` on every SSE tick (500ms) re-renders the entire dataset.
**Prevention:** Use `series.update({ time, value })` to append a single point rather than `setData`. Only call `setData` on initial mount.

### 6. Price Flash Cleanup
**What goes wrong:** Rapid price updates (500ms) can queue up multiple `setTimeout` flash timers, leaving stale CSS classes.
**Prevention:** `useEffect` cleanup function clears the timeout. The `useEffect` re-runs on `price` change — the cleanup runs first, clearing the previous timer before setting a new one.

### 7. FastAPI Static Mount Order
**What goes wrong:** If any API router is mounted AFTER the static files mount, the API routes are shadowed.
**Prevention:** Already handled in `backend/main.py` — API routers are registered before the static mount. Do not change this order.

### 8. Next.js 16 + React 19
**What goes wrong:** `create-next-app` latest installs React 19. Some older patterns (e.g., `ReactDOM.render`) are removed.
**Prevention:** Use React 19 patterns (`createRoot` is used internally by Next.js). No manual `ReactDOM.render` calls needed. Most community examples still work.

---

## Implementation Order

Recommended sequence for planning tasks:

1. **Initialize Next.js project** — `create-next-app` scaffold with TypeScript, Tailwind, App Router; configure `next.config.ts` with `output: 'export'` and `distDir`; verify `npm run build` produces output in `backend/static/` and FastAPI serves `index.html` at root.

2. **Apply dark theme** — Set global CSS body background to `#0d1117`; define color custom properties in `@theme` block; verify browser shows correct colors.

3. **Scaffold layout grid** — `AppShell.tsx` with CSS grid (header row, watchlist column, main area placeholder); all sections stubbed with background colors for visual verification.

4. **SSE hook + watchlist data flow** — `usePriceStream` hook connecting to `/api/stream/prices`; initial watchlist load from `GET /api/watchlist`; `usePortfolio` hook; pass data down as props.

5. **Header component** — Portfolio total value, cash balance, connection status dot (green/yellow/red based on EventSource readyState).

6. **WatchlistRow + flash animation** — Render ticker symbol, price, change %; implement flash CSS animation triggered on direction change.

7. **Sparkline component** — lightweight-charts `LineSeries` in a tiny container; accumulate price history in a `useRef` array; `series.update()` on each SSE tick.

8. **Ticker selection state** — Click handler on `WatchlistRow` updates `selectedTicker` state in parent; selected row gets highlighted border/background.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next.js build | Yes | v22.20.0 | — |
| npm | Package management | Yes | 11.6.1 | — |
| FastAPI backend | Static serving | Yes (Phase 1 complete) | — | — |
| `backend/static/` dir | FastAPI static mount | No — created by build | — | Created by `npm run build` |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | No frontend unit test framework configured (per REQUIREMENTS.md: "Frontend unit tests" are out of scope — E2E tests provide coverage) |
| Config file | none |
| Quick run command | `npm run build` (verifies TypeScript compilation) |
| Full suite command | `npm run build && npm run lint` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Notes |
|--------|----------|-----------|-------------------|-------|
| FE-01 | Next.js builds and FastAPI serves at root | smoke | `curl -s http://localhost:8000/ \| grep -q "html"` | Manual after build+start |
| FE-02 | Dark theme colors applied | visual | manual | No automated color test |
| FE-03 | Header shows portfolio values | smoke | manual browser check | Requires live backend |
| FE-04 | SSE connects and reconnects | smoke | manual — check browser DevTools Network tab | EventSource retry is built-in |
| WUI-01..05 | Watchlist displays and updates | smoke | manual browser check | Requires live backend |

TypeScript build (`npm run build`) is the primary automated gate for Phase 4 — it catches type errors, missing props, and bad imports before runtime.

### Wave 0 Gaps

- [ ] `frontend/package.json` — does not exist, needs `create-next-app` scaffold
- [ ] `frontend/next.config.ts` — does not exist, needs `output: 'export'` + `distDir`
- [ ] `frontend/app/globals.css` — does not exist, needs Tailwind import + theme variables
- [ ] `frontend/postcss.config.mjs` — does not exist, needs `@tailwindcss/postcss`

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | 16.2.1 | Framework + static export | Project spec; latest stable |
| react | 19.2.4 | UI library | Next.js peer dep |
| react-dom | 19.2.4 | React DOM renderer | Required by React |
| typescript | 6.0.2 | Type safety | Project spec |
| tailwindcss | 4.2.2 | Utility CSS | Project spec; dark theme config |
| @tailwindcss/postcss | 4.2.2 | v4 PostCSS integration | Required by Tailwind v4 |
| postcss | latest | CSS build | Required by Tailwind |
| lightweight-charts | 5.1.0 | Sparklines + main chart (Phase 5) | Canvas-based, TradingView quality, performance |

### Installation

```bash
cd frontend
npx create-next-app@latest . --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*"
npm install lightweight-charts
```

`create-next-app` installs next, react, react-dom, typescript, tailwindcss, @tailwindcss/postcss, postcss, eslint, @types/react, @types/node automatically.

---

## Sources

### Primary (HIGH confidence)
- Next.js 16.2.1 official docs (fetched 2026-03-31): static exports guide, configuration reference
- Tailwind CSS 4.2.2 official docs (fetched 2026-03-31): Next.js setup guide
- lightweight-charts 5.1.0 official tutorial (fetched 2026-03-31): React basic integration
- `backend/main.py`, `backend/app/routers/portfolio.py`, `backend/app/routers/watchlist.py`, `backend/app/market/stream.py`, `backend/app/market/models.py` — verified response shapes

### Secondary (MEDIUM confidence)
- npm registry versions for next (16.2.1), lightweight-charts (5.1.0), tailwindcss (4.2.2), react (19.2.4) — verified via `npm view`
- lightweight-charts v4→v5 migration guide: `chart.addSeries(LineSeries, ...)` pattern

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified via npm registry
- Architecture: HIGH — based on actual backend code and official Next.js docs
- Pitfalls: HIGH — derived from verified API changes (v5 lightweight-charts, Tailwind v4)

**Research date:** 2026-03-31
**Valid until:** 2026-04-30 (stable ecosystem — Next.js, Tailwind, lightweight-charts are stable releases)
