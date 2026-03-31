# Requirements: FinAlly

**Defined:** 2026-03-30
**Core Value:** A Bloomberg-terminal trading workstation where users watch live prices stream, trade a simulated portfolio, and have an AI execute trades on their behalf — one browser tab, zero setup.

## v1 Requirements

### Backend Foundation

- [x] **BACK-01**: Backend FastAPI app starts and serves all API routes on port 8000
- [x] **BACK-02**: SQLite database lazily initializes (creates schema + seeds data on first start)
- [x] **BACK-03**: Default user profile created with $10,000 cash balance
- [x] **BACK-04**: Default watchlist seeded with 10 tickers (AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX)
- [x] **BACK-05**: Health check endpoint returns 200 OK
- [x] **BACK-06**: Market data subsystem (simulator/Massive) integrated at app startup and shutdown

### Portfolio API

- [x] **PORT-01**: User can retrieve current portfolio (cash, positions, total value, unrealized P&L)
- [x] **PORT-02**: User can execute a buy trade (ticker, quantity) — cash decreases, position created/updated
- [x] **PORT-03**: User can execute a sell trade (ticker, quantity) — cash increases, position reduced/removed
- [x] **PORT-04**: Trade rejected if insufficient cash (buy) or insufficient shares (sell)
- [x] **PORT-05**: Trade execution records entry in trades history table
- [x] **PORT-06**: Portfolio snapshot recorded immediately after each trade
- [x] **PORT-07**: Background task records portfolio snapshots every 30 seconds
- [x] **PORT-08**: User can retrieve portfolio value history (for P&L chart)

### Watchlist API

- [x] **WATCH-01**: User can retrieve watchlist with current prices for each ticker
- [x] **WATCH-02**: User can add a ticker to the watchlist
- [x] **WATCH-03**: User can remove a ticker from the watchlist
- [x] **WATCH-04**: Adding a ticker starts price streaming for that ticker
- [x] **WATCH-05**: Removing a ticker stops price streaming for that ticker

### Chat API

- [ ] **CHAT-01**: User can send a chat message and receive an AI response
- [ ] **CHAT-02**: AI response includes the user's portfolio context (cash, positions, prices)
- [ ] **CHAT-03**: AI can execute trades mentioned in its response (auto-executed, no confirmation)
- [ ] **CHAT-04**: AI can add/remove watchlist tickers mentioned in its response
- [ ] **CHAT-05**: Chat conversation history persists and is included in subsequent LLM calls
- [ ] **CHAT-06**: LLM mock mode returns deterministic responses when LLM_MOCK=true
- [ ] **CHAT-07**: Failed trade validation errors are included in chat response

### Frontend Shell

- [ ] **FE-01**: Next.js app builds as static export and is served by FastAPI at root
- [ ] **FE-02**: Dark terminal aesthetic with correct color scheme (bg ~#0d1117, accent #ecad0a, blue #209dd7, purple #753991)
- [ ] **FE-03**: Header shows live portfolio total value, cash balance, and connection status indicator
- [ ] **FE-04**: SSE connection established on page load via EventSource; reconnects automatically

### Watchlist UI

- [ ] **WUI-01**: Watchlist panel shows all watched tickers in a grid/table
- [ ] **WUI-02**: Each ticker row shows symbol, current price, daily change %, and a sparkline
- [ ] **WUI-03**: Price updates flash green (uptick) or red (downtick) with ~500ms CSS fade
- [ ] **WUI-04**: Sparklines accumulate price history from SSE stream since page load
- [ ] **WUI-05**: Clicking a ticker selects it and loads it in the main chart area

### Chart & Portfolio UI

- [ ] **CHART-01**: Main chart area shows price-over-time for the selected ticker
- [ ] **CHART-02**: Portfolio heatmap (treemap) shows positions sized by weight, colored by P&L
- [ ] **CHART-03**: P&L chart shows total portfolio value over time from portfolio_snapshots
- [ ] **CHART-04**: Positions table shows ticker, quantity, avg cost, current price, unrealized P&L, % change

### Trade UI

- [ ] **TRADE-01**: Trade bar has ticker field, quantity field, Buy button, Sell button
- [ ] **TRADE-02**: Executing a trade updates portfolio display without page reload

### Chat UI

- [ ] **CUI-01**: AI chat panel shows message input and scrolling conversation history
- [ ] **CUI-02**: Loading indicator shown while waiting for LLM response
- [ ] **CUI-03**: Trade executions and watchlist changes from AI shown inline as confirmations

### Docker & Deployment

- [ ] **DOCK-01**: Multi-stage Dockerfile builds frontend (Node) then backend (Python) in single image
- [ ] **DOCK-02**: Container serves full app on port 8000 with single `docker run` command
- [ ] **DOCK-03**: SQLite database persists via Docker named volume mount at `/app/db`
- [ ] **DOCK-04**: start_mac.sh builds (if needed) and runs container with volume + env file
- [ ] **DOCK-05**: stop_mac.sh stops and removes container (preserves volume)
- [ ] **DOCK-06**: start_windows.ps1 and stop_windows.ps1 PowerShell equivalents

### Testing

- [ ] **TEST-01**: Backend unit tests for portfolio trade logic (buy, sell, edge cases)
- [ ] **TEST-02**: Backend unit tests for LLM structured output parsing and chat flow
- [ ] **TEST-03**: Backend unit tests for API route status codes and response shapes
- [ ] **TEST-04**: E2E Playwright tests: fresh start shows default watchlist + $10k balance + streaming prices
- [ ] **TEST-05**: E2E Playwright tests: add/remove ticker from watchlist
- [ ] **TEST-06**: E2E Playwright tests: buy shares — cash decreases, position appears
- [ ] **TEST-07**: E2E Playwright tests: sell shares — cash increases, position updates
- [ ] **TEST-08**: E2E Playwright tests: AI chat (mocked) — send message, receive response, trade inline
- [ ] **TEST-09**: E2E test infrastructure: docker-compose.test.yml with app + Playwright containers

## v2 Requirements

### Enhanced Charts

- **V2-01**: Intraday OHLC candlestick chart for selected ticker
- **V2-02**: Volume overlay on main chart

### Advanced Portfolio

- **V2-03**: Sector exposure breakdown in portfolio view
- **V2-04**: Portfolio risk metrics (Sharpe ratio, beta vs market)

### Cloud Deployment

- **V2-05**: Terraform config for AWS App Runner deployment

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-user / authentication | Single-user by design; user_id exists for future-proofing only |
| Limit orders / order book | Market orders only — dramatically simpler, sufficient for demo |
| Real brokerage integration | Simulated portfolio only — no real money |
| Mobile-first design | Desktop-first; functional on tablet is sufficient |
| WebSocket bidirectional comms | SSE is sufficient for one-way price push |
| Frontend unit tests | E2E tests provide sufficient coverage for this course project |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BACK-01 – BACK-06 | Phase 1 | Pending |
| PORT-01 – PORT-08 | Phase 2 | Pending |
| WATCH-01 – WATCH-05 | Phase 2 | Pending |
| CHAT-01 – CHAT-07 | Phase 3 | Pending |
| FE-01 – FE-04 | Phase 4 | Pending |
| WUI-01 – WUI-05 | Phase 4 | Pending |
| CHART-01 – CHART-04 | Phase 5 | Pending |
| TRADE-01 – TRADE-02 | Phase 5 | Pending |
| CUI-01 – CUI-03 | Phase 5 | Pending |
| DOCK-01 – DOCK-06 | Phase 6 | Pending |
| TEST-01 – TEST-09 | Phase 7 | Pending |

**Coverage:**
- v1 requirements: 53 total
- Mapped to phases: 53
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-30*
*Last updated: 2026-03-30 after initial definition*
