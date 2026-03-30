# Concerns

## Critical Missing Implementations

### 1. No FastAPI Application Entry Point
- **Missing**: `backend/app/main.py` — no FastAPI app, no server startup
- **Impact**: Backend cannot be started; market data exists but isn't served
- **Status**: `backend/app/routers/` directory exists but is empty

### 2. No Database Layer
- **Missing**: SQLite schema, initialization, migration, and data access code
- **Impact**: All persistent state (portfolio, watchlist, trades, chat history) requires DB
- **Per spec**: Lazy init on first request, tables: `users_profile`, `watchlist`, `positions`, `trades`, `portfolio_snapshots`, `chat_messages`

### 3. No Portfolio Management
- **Missing**: Trade execution (buy/sell), position tracking, P&L calculations
- **Impact**: Core trading functionality absent — `/api/portfolio` and `/api/portfolio/trade` not implemented
- **Edge cases to handle**: insufficient cash, selling more than owned, fractional shares

### 4. No Watchlist CRUD
- **Missing**: REST endpoints for GET/POST/DELETE on `/api/watchlist`
- **Impact**: No way to manage watched tickers via API (only hardcoded seed data at DB init)

### 5. No LLM Chat Integration
- **Missing**: `/api/chat` endpoint, LiteLLM/OpenRouter integration, structured output parsing, auto-execution of trades
- **Impact**: Core capstone "AI copilot" feature not started
- **Dependency**: Requires OPENROUTER_API_KEY in `.env` (key is present)

### 6. No Frontend
- **Missing**: Entire `frontend/` directory is empty — no Next.js project initialized
- **Impact**: No UI at all; app serves nothing at `http://localhost:8000`
- **Per spec**: Next.js TypeScript, static export, Tailwind CSS, Lightweight Charts or Recharts

### 7. No Docker / Deployment Infrastructure
- **Missing**: `Dockerfile`, `docker-compose.yml`, `scripts/start_mac.sh`, etc.
- **Impact**: Cannot build or run as a container; no single-command launch for students

### 8. No E2E Tests
- **Missing**: Playwright test files in `test/` (node_modules installed, no tests written)
- **Per spec**: `test/docker-compose.test.yml` + Playwright scenarios with `LLM_MOCK=true`

## Architecture Gaps

### SSE Streaming Not Wired to FastAPI
- `backend/app/market/stream.py` contains SSE streaming logic but there is no FastAPI app to mount it on
- `GET /api/stream/prices` endpoint does not exist yet

### Portfolio Snapshots Background Task
- Background task for recording `portfolio_snapshots` every 30 seconds not implemented
- This is also needed for the P&L chart

### LLM Mock Mode
- `LLM_MOCK=true` environment variable handling not yet implemented (no LLM code exists)

## Security / Config Concerns

### .env File
- `.env` is gitignored; an `.env.example` should be committed but isn't yet
- `OPENROUTER_API_KEY` is present in `.env` (real key — not exposed in codebase)
- `MASSIVE_API_KEY` is absent/empty → simulator will be used by default

### No Input Validation on Trade Endpoint
- Future concern: trade quantities and tickers must be validated to prevent negative quantities, invalid tickers, etc.

### Single-User Hardcoding
- `user_id = "default"` hardcoded everywhere; fine for now but worth noting for future

## Incomplete Market Data Areas

### Massive Client Error Handling
- Network timeouts and API rate limit (5 req/min free tier) need retry/backoff logic
- Currently depends on `massive>=1.0.0` package which wraps Polygon.io

### Stream Reconnection
- Frontend `EventSource` has built-in reconnection, but backend SSE endpoint should handle client disconnect gracefully

### Ticker Validation
- No validation that a ticker is real/tradeable before adding to watchlist

## Performance / Scaling Concerns

### In-Memory Price Cache
- `PriceCache` holds all prices in memory — fine for single-user simulation but would need persistence for multi-user
- Thread-safe via `threading.Lock` (synchronous); if FastAPI uses async workers, lock strategy should be reviewed

### SQLite for All Writes
- Portfolio snapshots recorded every 30 seconds × all positions could create write contention under heavy load (not a concern for single-user)

### Chat History Loading
- Full conversation history loaded on every `/api/chat` request — should be windowed for long sessions

## Fragile Areas

### GBM Correlation Matrix
- Cholesky decomposition rebuilt when tickers are added/removed — expensive O(n³) operation; acceptable for ≤20 tickers
- `test_cholesky_rebuilds_on_add` covers this behavior

### Simulator "Random Events"
- Occasional 2-5% spike events create realistic drama but could make tests flaky if not properly seeded
- Tests use deterministic seeds where randomness matters

### Static Export + FastAPI Serving
- Next.js `output: 'export'` produces flat HTML files; FastAPI must serve `index.html` for all non-API routes (catch-all route needed)

## Intentional Design Decisions (Not Concerns)

- **Market orders only** — no order book complexity; intentional per spec
- **No auth** — single-user `"default"` user; intentional per spec
- **No confirmation dialogs** — LLM auto-executes trades; intentional for demo impact
- **SQLite not Postgres** — zero config, single container; intentional per spec
