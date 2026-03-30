# Roadmap: FinAlly — AI Trading Workstation

## Overview

Build a Bloomberg-terminal-aesthetic AI trading workstation in seven phases: first the FastAPI backend with database, then the portfolio and watchlist REST APIs, then LLM chat integration, then the Next.js frontend shell with live price streaming, then all remaining UI panels (charts, heatmap, trade bar, chat), then Docker packaging, and finally the full test suite. Each phase delivers a coherent, independently verifiable capability on top of the already-complete market data subsystem.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Backend Foundation** - FastAPI app wired to SQLite, seeded with default data, market data running
- [ ] **Phase 2: Portfolio & Watchlist API** - Complete REST API for trading, portfolio snapshots, and watchlist management
- [ ] **Phase 3: Chat API** - LLM integration (LiteLLM/Cerebras) with auto-execute and mock mode
- [ ] **Phase 4: Frontend Shell & Watchlist** - Next.js static export served by FastAPI, dark theme, SSE live prices, watchlist panel
- [ ] **Phase 5: Charts, Portfolio & Trade UI** - Main chart, heatmap, P&L chart, positions table, trade bar, AI chat panel
- [ ] **Phase 6: Docker & Deployment** - Multi-stage Dockerfile, start/stop scripts, persistent volume
- [ ] **Phase 7: Testing** - Backend unit tests, E2E Playwright suite, test infrastructure

## Phase Details

### Phase 1: Backend Foundation
**Goal**: The FastAPI backend starts, initializes the database with seed data, and integrates the market data subsystem
**Depends on**: Nothing (market data subsystem already built)
**Requirements**: BACK-01, BACK-02, BACK-03, BACK-04, BACK-05, BACK-06
**Success Criteria** (what must be TRUE):
  1. Calling `GET /api/health` returns HTTP 200
  2. On fresh start, database file is created with schema tables and default user ($10,000 cash)
  3. Default watchlist of 10 tickers (AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX) exists in the database
  4. Price streaming via `GET /api/stream/prices` delivers live SSE events from the market data subsystem
**Plans**: TBD

### Phase 2: Portfolio & Watchlist API
**Goal**: Users can trade a simulated portfolio and manage their watchlist entirely through REST endpoints
**Depends on**: Phase 1
**Requirements**: PORT-01, PORT-02, PORT-03, PORT-04, PORT-05, PORT-06, PORT-07, PORT-08, WATCH-01, WATCH-02, WATCH-03, WATCH-04, WATCH-05
**Success Criteria** (what must be TRUE):
  1. `GET /api/portfolio` returns cash balance, all positions with unrealized P&L, and total portfolio value
  2. `POST /api/portfolio/trade` with a buy order decreases cash and creates/updates a position
  3. `POST /api/portfolio/trade` with a sell order increases cash and reduces/removes a position
  4. A trade with insufficient cash (buy) or insufficient shares (sell) returns an error response, not a 500
  5. Portfolio snapshots are recorded after each trade and every 30 seconds; `GET /api/portfolio/history` returns them
  6. `GET /api/watchlist` returns tickers with current prices; adding and removing tickers updates price streaming
**Plans**: TBD

### Phase 3: Chat API
**Goal**: Users can converse with an AI assistant that has portfolio context and can auto-execute trades and watchlist changes
**Depends on**: Phase 2
**Requirements**: CHAT-01, CHAT-02, CHAT-03, CHAT-04, CHAT-05, CHAT-06, CHAT-07
**Success Criteria** (what must be TRUE):
  1. `POST /api/chat` with a message returns an AI response that includes the user's current portfolio context
  2. If the AI response includes trades, they are auto-executed and confirmed in the response payload
  3. If the AI response includes watchlist changes, they are applied and confirmed in the response payload
  4. Conversation history from prior calls is included in each new LLM request
  5. With `LLM_MOCK=true`, the endpoint returns deterministic responses without calling OpenRouter
  6. Trade validation failures (e.g., insufficient cash) are reported in the chat response rather than silently dropped
**Plans**: TBD

### Phase 4: Frontend Shell & Watchlist
**Goal**: The Next.js app is served by FastAPI, displays a dark trading terminal, connects to the SSE stream, and shows a live-updating watchlist
**Depends on**: Phase 2
**Requirements**: FE-01, FE-02, FE-03, FE-04, WUI-01, WUI-02, WUI-03, WUI-04, WUI-05
**Success Criteria** (what must be TRUE):
  1. Navigating to `http://localhost:8000` loads the Next.js app with a dark terminal aesthetic (bg ~#0d1117, accent #ecad0a, blue #209dd7, purple #753991)
  2. The header shows live portfolio total value, cash balance, and a connection status dot (green when connected)
  3. The watchlist panel shows all 10 default tickers with symbol, current price, daily change %, and a sparkline that grows over time
  4. Price changes flash green (uptick) or red (downtick) with a ~500ms CSS fade animation
  5. Clicking a ticker in the watchlist selects it (highlighted state visible)
**Plans**: TBD
**UI hint**: yes

### Phase 5: Charts, Portfolio & Trade UI
**Goal**: Users can view the full dashboard — main chart, portfolio heatmap, P&L chart, positions table, trade bar, and AI chat panel — all wired to live data
**Depends on**: Phase 4
**Requirements**: CHART-01, CHART-02, CHART-03, CHART-04, TRADE-01, TRADE-02, CUI-01, CUI-02, CUI-03
**Success Criteria** (what must be TRUE):
  1. Clicking a ticker loads its price-over-time chart in the main chart area
  2. The portfolio heatmap (treemap) shows positions sized by weight and colored green (profit) or red (loss)
  3. The P&L chart shows total portfolio value over time using snapshot data
  4. The positions table shows ticker, quantity, avg cost, current price, unrealized P&L, and % change — updated after every trade
  5. The trade bar lets the user type a ticker and quantity, click Buy or Sell, and the portfolio display updates immediately without a page reload
  6. The AI chat panel shows a message input, scrolling history, a loading indicator while awaiting response, and inline confirmations for trade/watchlist actions
**Plans**: TBD
**UI hint**: yes

### Phase 6: Docker & Deployment
**Goal**: The entire application runs from a single Docker command with persistent storage and works on both Mac and Windows
**Depends on**: Phase 5
**Requirements**: DOCK-01, DOCK-02, DOCK-03, DOCK-04, DOCK-05, DOCK-06
**Success Criteria** (what must be TRUE):
  1. `docker build` produces a single image containing both the Next.js static export and the FastAPI backend
  2. `docker run -v finally-data:/app/db -p 8000:8000 --env-file .env finally` starts the full app on port 8000
  3. Stopping and restarting the container preserves portfolio data (trades, watchlist, snapshots) via the named volume
  4. `scripts/start_mac.sh` builds (if needed) and runs the container; `scripts/stop_mac.sh` stops it without deleting the volume
  5. PowerShell equivalents (`start_windows.ps1`, `stop_windows.ps1`) perform the same operations on Windows
**Plans**: TBD

### Phase 7: Testing
**Goal**: The codebase has comprehensive backend unit tests and a full E2E Playwright suite that covers all critical user flows
**Depends on**: Phase 6
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07, TEST-08, TEST-09
**Success Criteria** (what must be TRUE):
  1. Backend unit tests cover trade logic (buy, sell, edge cases), LLM output parsing, and API route shapes — all pass with `uv run pytest`
  2. E2E test: fresh container start shows default watchlist, $10k balance, and streaming prices
  3. E2E test: user can add and remove a ticker from the watchlist
  4. E2E test: buying shares decreases cash and adds a position; selling shares increases cash and updates the position
  5. E2E test: AI chat (mocked) returns a response and shows an inline trade confirmation
  6. `docker-compose.test.yml` in `test/` spins up app + Playwright containers and all tests pass
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Backend Foundation | 0/TBD | Not started | - |
| 2. Portfolio & Watchlist API | 0/TBD | Not started | - |
| 3. Chat API | 0/TBD | Not started | - |
| 4. Frontend Shell & Watchlist | 0/TBD | Not started | - |
| 5. Charts, Portfolio & Trade UI | 0/TBD | Not started | - |
| 6. Docker & Deployment | 0/TBD | Not started | - |
| 7. Testing | 0/TBD | Not started | - |
