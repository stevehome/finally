# External Integrations

**Analysis Date:** 2026-03-30

## APIs & External Services

**Market Data:**
- **Massive (Polygon.io)** - Optional real-time stock market data
  - SDK/Client: `massive>=1.0.0` (`app/market/massive_client.py`)
  - Endpoint: REST API polling (not WebSocket)
  - Authentication: `MASSIVE_API_KEY` environment variable
  - Rate limits: Free tier 5 req/min (poll every 15s), paid tiers every 2-15s
  - Implementation: `MassiveDataSource` class in `app/market/massive_client.py`
  - Fallback: Built-in GBM simulator if key not provided

**LLM/AI:**
- **OpenRouter** - LLM API for chat assistant
  - Provider: Routes to Cerebras inference backend for GPT-OSS 120B model
  - Authentication: `OPENROUTER_API_KEY` environment variable
  - Model: `openrouter/openai/gpt-oss-120b`
  - Client Library: LiteLLM (planned, not yet implemented)
  - Response Format: Structured JSON output with message + trades + watchlist changes
  - Feature: Auto-execution of trades and watchlist modifications based on LLM response
  - Testing Mode: `LLM_MOCK=true` for deterministic mock responses (E2E tests)

## Data Storage

**Databases:**
- **SQLite3** (local file-based)
  - Location: `db/finally.db` (volume-mounted Docker path)
  - Persistence: Docker named volume `finally-data`
  - Client: Python `sqlite3` standard library
  - Lazy initialization: Schema and seed data created on first request if missing

**File Storage:**
- Local filesystem only - no cloud storage integration

**Caching:**
- In-memory price cache: `PriceCache` class in `app/market/cache.py`
  - Thread-safe, monotonic version counter for SSE change detection
  - Holds latest price + previous price + timestamp per ticker
  - Used by both market data sources (simulator and Massive)

## Authentication & Identity

**Auth Provider:**
- None - Single-user design (hardcoded user_id "default")
- All database records include `user_id` column defaulting to "default"
- Future multi-user support requires no schema changes

**Environment-based configuration:**
- API keys stored in `.env` file (never committed)
- Loaded at runtime via `os.environ.get()`

## Monitoring & Observability

**Error Tracking:**
- None detected - error handling via exception logging

**Logs:**
- Python standard `logging` module
- Log level configurable via environment
- `rich` library for enhanced terminal output and formatting in demo scripts

**Health Check:**
- Expected endpoint: `GET /api/health` (per PLAN.md, not yet implemented)

## CI/CD & Deployment

**Hosting:**
- Docker container (single image, single port 8000)
- Designed for: AWS App Runner, Render, any container platform
- Expected Docker volume mount: `finally-data:/app/db`

**CI Pipeline:**
- None detected - E2E test infrastructure exists but CI not configured
- Playwright tests in `test/` with supporting `docker-compose.test.yml`

## Environment Configuration

**Required env vars:**
- `OPENROUTER_API_KEY` - LLM chat functionality (required for AI assistant)

**Optional env vars:**
- `MASSIVE_API_KEY` - Real market data from Polygon.io (defaults to simulator if omitted)
- `LLM_MOCK=true` - Mock LLM responses for testing (defaults to false)

**Secrets location:**
- `.env` file in project root (gitignored)
- Mounted into Docker container via `--env-file .env` or docker-compose
- No secrets manager integration detected

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- Trade execution results → stored in database `trades` table
- Portfolio snapshots → recorded every 30 seconds by background task
- Chat messages → stored in `chat_messages` table with action results

## Real-time Data Flow

**Server-Sent Events (SSE):**
- Endpoint: `GET /api/stream/prices`
- Content-Type: `text/event-stream`
- Client: Browser native `EventSource` API
- Data source: In-memory `PriceCache` fed by market data simulator or Massive poller
- Cadence: ~500ms per update
- Client reconnection: Automatic via EventSource built-in retry

**Background Tasks:**
- Market data simulator: `SimulatorDataSource` runs GBM price generation in background
- Market data poller: `MassiveDataSource` polls REST API on interval (15s default for free tier)
- Portfolio snapshots: Background task records total portfolio value every 30s and after trades

## API Endpoints (Backend → Frontend)

**Market Data:**
- `GET /api/stream/prices` - SSE stream of live price updates

**Portfolio:**
- `GET /api/portfolio` - Current positions, cash, total value, P&L
- `POST /api/portfolio/trade` - Execute trade (ticker, quantity, side)
- `GET /api/portfolio/history` - Portfolio value snapshots over time

**Watchlist:**
- `GET /api/watchlist` - Current watchlist with live prices
- `POST /api/watchlist` - Add ticker
- `DELETE /api/watchlist/{ticker}` - Remove ticker

**Chat:**
- `POST /api/chat` - Send message, receive structured JSON response with actions

**System:**
- `GET /api/health` - Health check (planned)

---

*Integration audit: 2026-03-30*
