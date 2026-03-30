# Architecture

**Analysis Date:** 2026-03-30

## Pattern Overview

**Overall:** Layered service architecture with pluggable data sources and SSE-based real-time streaming.

**Key Characteristics:**
- Abstraction-driven market data layer supporting multiple implementations (simulator, Massive API)
- Thread-safe shared cache pattern for price data
- Async/await throughout for I/O and background tasks
- Factory pattern for environment-driven selection of market data source
- Stateless API endpoints that read/write to shared cache

## Layers

**Market Data Layer:**
- Purpose: Unified interface for price data acquisition and streaming
- Location: `backend/app/market/`
- Contains: Abstract interface, implementations (simulator, Massive client), price cache, SSE streaming endpoint
- Depends on: numpy (GBM math), Massive SDK (optional), threading (thread-safe cache)
- Used by: FastAPI routers, portfolio engine (forthcoming), SSE streaming

**API/Routing Layer:**
- Purpose: HTTP endpoints for clients (portfolio operations, watchlist management, chat, health checks)
- Location: `backend/app/routers/` (not yet populated; placeholder)
- Contains: FastAPI route handlers
- Depends on: Market data layer (price cache), database layer (forthcoming)
- Used by: Frontend clients via REST/SSE

**Database Layer:**
- Purpose: Persistent storage for user profiles, positions, trades, watchlist, chat history
- Location: `backend/db/` (schema definitions, seed logic; not yet implemented)
- Contains: SQLite schema, migration logic, seed data
- Depends on: None
- Used by: Portfolio engine, trade execution, watchlist management

**Frontend Layer:**
- Purpose: Single-page web application for user interaction
- Location: `frontend/` (not yet implemented; Next.js TypeScript)
- Contains: React components, charts, real-time price display, portfolio visualizations, chat interface
- Depends on: SSE streaming, REST API endpoints
- Used by: End users via browser

## Data Flow

**Price Update Flow:**

1. Market data source (Simulator or Massive poller) runs in background task
2. Source calculates/polls new prices, calls `PriceCache.update(ticker, price)`
3. Cache atomically records new price and increments version counter
4. SSE endpoint monitors cache version, sends all prices when version changes (~500ms cadence)
5. Frontend receives SSE events, updates price display with flash animations, accumulates sparkline data

**Trade Execution Flow (forthcoming):**

1. User clicks buy/sell button or LLM sends trade command
2. API endpoint receives trade request: `{ticker, quantity, side}`
3. Portfolio engine validates (sufficient cash for buy, sufficient shares for sell)
4. If valid: execute trade, deduct/add cash, update position in database, record in trades log
5. Calculate new portfolio value, record in portfolio_snapshots table
6. Return updated portfolio state to client

**Chat/LLM Flow (forthcoming):**

1. User sends message via chat panel
2. API endpoint loads portfolio context and recent conversation history
3. Constructs prompt with system message, portfolio state, and conversation history
4. Calls LLM via LiteLLM → OpenRouter (Cerebras), expects structured JSON output
5. Parses response: extracts conversational message and any auto-executable trades/watchlist changes
6. Validates and executes trades/watchlist changes against current portfolio
7. Records message and executed actions in chat_messages table
8. Returns complete JSON (message + actions) to frontend

**State Management:**
- All state centralized in SQLite database (persisted across sessions)
- In-memory price cache is transient (rebuilt on app restart from latest market data)
- Portfolio snapshots recorded every 30 seconds + immediately after trades for P&L charting

## Key Abstractions

**MarketDataSource (Abstract):**
- Purpose: Pluggable interface for price data acquisition
- Examples: `backend/app/market/simulator.py`, `backend/app/market/massive_client.py`
- Pattern: Abstract base class with lifecycle methods (`start`, `stop`, `add_ticker`, `remove_ticker`, `get_tickers`); implementations run background tasks that write to shared PriceCache

**PriceUpdate (Immutable Dataclass):**
- Purpose: Atomic snapshot of a single ticker's price at a point in time
- Examples: `backend/app/market/models.py`
- Pattern: Frozen dataclass with computed properties (change, change_percent, direction); includes `to_dict()` for JSON serialization

**PriceCache (Thread-Safe Store):**
- Purpose: Central in-memory store of latest prices, indexed by ticker
- Examples: `backend/app/market/cache.py`
- Pattern: Locking wrapper around dictionary; version counter bumped on every write for efficient SSE change detection

## Entry Points

**Application Startup (forthcoming):**
- Location: `backend/main.py` (not yet created)
- Triggers: Container startup, Docker ENTRYPOINT
- Responsibilities: Initialize FastAPI app, create PriceCache, create MarketDataSource via factory, start market data source background task, attach SSE router, attach other API routers, start uvicorn server on port 8000

**SSE Streaming Endpoint:**
- Location: `backend/app/market/stream.py::stream_prices()`
- Triggers: Client opens EventSource to `GET /api/stream/prices`
- Responsibilities: Open long-lived connection, monitor cache version, yield SSE-formatted price events every ~500ms, detect client disconnect

**Market Data Update Loop (Simulator):**
- Location: `backend/app/market/simulator.py::SimulatorDataSource._sim_loop()` (internal async task)
- Triggers: `source.start()` called at app initialization
- Responsibilities: Every ~500ms, call GBMSimulator.step() for all active tickers, write prices to PriceCache

**Market Data Poll Loop (Massive API):**
- Location: `backend/app/market/massive_client.py::MassiveDataSource._poll_loop()` (internal async task)
- Triggers: `source.start()` called at app initialization
- Responsibilities: Every N seconds (15s default for free tier), call Massive REST API, parse snapshot response, write prices to PriceCache

## Error Handling

**Strategy:** Graceful degradation with informative logging.

**Patterns:**
- Market data source failures are logged but do not crash the app; last known prices remain available
- SSE client disconnection is expected and handled silently (EventSource built-in retry)
- GBM simulator prices are guaranteed positive (never approach zero due to exponential formulation)
- Massive API parsing errors logged; failed poll does not block next cycle

## Cross-Cutting Concerns

**Logging:** Python logging module with named loggers per module (e.g., `logging.getLogger(__name__)`). Log levels: DEBUG for verbose cycle traces, INFO for lifecycle events, WARNING for unusual conditions, ERROR for failures.

**Validation:** Market data sources validate ticker symbols before adding/removing; GBM simulator bounds prices to avoid negative values. Portfolio engine will validate trades (cash/share sufficiency) at execution time.

**Authentication:** Not yet implemented. Single hardcoded user (`user_id="default"`) for now. Future schema supports multi-user via user_id foreign keys.

---

*Architecture analysis: 2026-03-30*
