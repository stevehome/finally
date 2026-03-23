# Market Data Backend — Design & Implementation Guide

**Status:** Complete. All code lives in `backend/app/market/` (8 modules, ~500 lines). 73 tests passing.

This document describes the architecture, all public APIs, and integration patterns for the market data subsystem. Downstream agents building the portfolio, watchlist, trade, and chat features should read this document.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [File Structure](#2-file-structure)
3. [Data Model — `PriceUpdate`](#3-data-model--priceupdate)
4. [Price Cache — `PriceCache`](#4-price-cache--pricecache)
5. [Abstract Interface — `MarketDataSource`](#5-abstract-interface--marketdatasource)
6. [GBM Simulator — `SimulatorDataSource`](#6-gbm-simulator--simulatordatasource)
7. [Massive API Client — `MassiveDataSource`](#7-massive-api-client--massivedatasource)
8. [Factory — `create_market_data_source()`](#8-factory--create_market_data_source)
9. [SSE Streaming Endpoint](#9-sse-streaming-endpoint)
10. [FastAPI Lifecycle Integration](#10-fastapi-lifecycle-integration)
11. [Watchlist Coordination](#11-watchlist-coordination)
12. [Using Prices in Portfolio & Trade Logic](#12-using-prices-in-portfolio--trade-logic)
13. [Configuration](#13-configuration)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│  Market Data Subsystem (backend/app/market/)            │
│                                                         │
│  MarketDataSource (ABC)                                 │
│  ├── SimulatorDataSource  ─── GBMSimulator              │
│  │   (default, no key needed)  (Cholesky-correlated GBM)│
│  └── MassiveDataSource                                  │
│      (when MASSIVE_API_KEY set)  Polygon.io REST poller │
│               │                                         │
│               ▼  writes every ~500ms                    │
│         PriceCache  (thread-safe, in-memory)            │
│               │                                         │
│    ┌──────────┼──────────────┐                          │
│    ▼          ▼              ▼                          │
│  SSE stream  Portfolio    Trade execution               │
│  /api/stream/prices  valuation   (current price lookup) │
└─────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- **Strategy pattern** — both data sources implement the same ABC; all downstream code is source-agnostic
- **PriceCache as single point of truth** — producers write, consumers read; no direct coupling between source and consumers
- **SSE over WebSockets** — one-way push is all we need; simpler, universal browser support
- **Version counter** — `PriceCache.version` increments on every update; SSE endpoint uses this for change detection to avoid sending duplicate payloads

---

## 2. File Structure

```
backend/
  app/
    market/
      __init__.py         # Re-exports public API (import from here)
      models.py           # PriceUpdate dataclass
      cache.py            # PriceCache — thread-safe in-memory store
      interface.py        # MarketDataSource ABC
      seed_prices.py      # SEED_PRICES, TICKER_PARAMS, CORRELATION_GROUPS
      simulator.py        # GBMSimulator + SimulatorDataSource
      massive_client.py   # MassiveDataSource (Polygon.io)
      factory.py          # create_market_data_source()
      stream.py           # FastAPI SSE router factory
  tests/
    market/
      test_models.py          # 11 tests — 100% coverage
      test_cache.py           # 13 tests — 100% coverage
      test_simulator.py       # 17 tests — 98% coverage
      test_simulator_source.py # 10 integration tests
      test_factory.py         # 7 tests — 100% coverage
      test_massive.py         # 13 tests — 56% coverage (API mocked)
```

**Always import from `app.market`, not from submodules:**

```python
from app.market import PriceUpdate, PriceCache, MarketDataSource, create_market_data_source, create_stream_router
```

---

## 3. Data Model — `PriceUpdate`

**File:** `backend/app/market/models.py`

`PriceUpdate` is the only data structure that leaves the market data layer. It is immutable (`frozen=True, slots=True`).

```python
@dataclass(frozen=True, slots=True)
class PriceUpdate:
    ticker: str
    price: float           # Current price, rounded to 2 decimal places
    previous_price: float  # Price from the previous update
    timestamp: float       # Unix seconds (default: time.time())

    # Computed properties (no stored state):
    @property
    def change(self) -> float:          # price - previous_price, rounded to 4dp
    @property
    def change_percent(self) -> float:  # % change from previous, rounded to 4dp
    @property
    def direction(self) -> str:         # "up", "down", or "flat"

    def to_dict(self) -> dict:          # JSON-serializable dict for SSE / API responses
```

**`to_dict()` output** (what the SSE stream and API responses send):

```json
{
  "ticker": "AAPL",
  "price": 191.45,
  "previous_price": 191.20,
  "timestamp": 1711234567.123,
  "change": 0.25,
  "change_percent": 0.1307,
  "direction": "up"
}
```

**On first update for a ticker**, `previous_price == price`, so `change == 0` and `direction == "flat"`. This is expected — the next update will show a real direction.

---

## 4. Price Cache — `PriceCache`

**File:** `backend/app/market/cache.py`

Thread-safe in-memory store. The data source (simulator or Massive) writes to it; the SSE endpoint, portfolio valuation, and trade execution read from it.

```python
class PriceCache:
    def update(self, ticker: str, price: float, timestamp: float | None = None) -> PriceUpdate:
        """Write a new price. Returns the PriceUpdate created.
        Automatically computes previous_price, change, direction from last stored value.
        """

    def get(self, ticker: str) -> PriceUpdate | None:
        """Latest PriceUpdate for a ticker, or None if not yet seen."""

    def get_price(self, ticker: str) -> float | None:
        """Convenience: just the price float, or None."""

    def get_all(self) -> dict[str, PriceUpdate]:
        """Snapshot of all current prices. Returns a shallow copy — safe to iterate."""

    def remove(self, ticker: str) -> None:
        """Remove a ticker (called when removed from watchlist)."""

    @property
    def version(self) -> int:
        """Monotonically increasing counter. Incremented on every update().
        Use for change detection — if version hasn't changed, no new data."""

    def __len__(self) -> int:     # Number of tracked tickers
    def __contains__(self, ticker: str) -> bool
```

**Usage examples:**

```python
cache = PriceCache()

# Check if a ticker has data
if "AAPL" in cache:
    price = cache.get_price("AAPL")   # float

# Get full update with direction info
update = cache.get("AAPL")
if update:
    print(f"{update.ticker}: ${update.price} ({update.direction})")

# Get all prices for SSE payload or portfolio snapshot
all_prices = cache.get_all()  # dict[str, PriceUpdate]
for ticker, update in all_prices.items():
    print(update.to_dict())

# Version-based polling (used by SSE endpoint)
last_version = -1
while True:
    if cache.version != last_version:
        last_version = cache.version
        snapshot = cache.get_all()
        # ... process snapshot ...
```

---

## 5. Abstract Interface — `MarketDataSource`

**File:** `backend/app/market/interface.py`

```python
class MarketDataSource(ABC):
    async def start(self, tickers: list[str]) -> None:
        """Begin producing price updates. Starts background task.
        Call exactly once at app startup."""

    async def stop(self) -> None:
        """Stop background task. Safe to call multiple times."""

    async def add_ticker(self, ticker: str) -> None:
        """Add a ticker to the active set. No-op if already present."""

    async def remove_ticker(self, ticker: str) -> None:
        """Remove a ticker. Also removes it from PriceCache."""

    def get_tickers(self) -> list[str]:
        """Current list of actively tracked tickers."""
```

**Lifecycle contract:**
1. Create via `create_market_data_source(cache)` — returns an unstarted source
2. Call `await source.start(initial_tickers)` — seeds cache immediately, starts background task
3. Call `add_ticker` / `remove_ticker` as the user manages their watchlist
4. Call `await source.stop()` in the FastAPI shutdown handler

---

## 6. GBM Simulator — `SimulatorDataSource`

**File:** `backend/app/market/simulator.py`

The default data source. No API key required. Runs entirely in-process.

### How it works

Uses **Geometric Brownian Motion (GBM)** — the standard model underlying Black-Scholes:

```
S(t+dt) = S(t) * exp((mu - 0.5*sigma²) * dt + sigma * sqrt(dt) * Z)
```

Where:
- `mu` = annualized drift (e.g. 0.05 = 5% expected annual return)
- `sigma` = annualized volatility (e.g. 0.22 for AAPL, 0.50 for TSLA)
- `dt` = 500ms expressed as a fraction of a trading year ≈ `8.48e-8`
- `Z` = correlated standard normal drawn via Cholesky decomposition

The tiny `dt` produces sub-cent moves per tick that accumulate naturally.

### Correlated moves

Real stocks don't move independently. The simulator uses Cholesky decomposition of a sector correlation matrix:

```
Tech group (AAPL, GOOGL, MSFT, AMZN, META, NVDA, NFLX): intra-group corr = 0.60
Finance group (JPM, V):                                   intra-group corr = 0.50
TSLA:                                                     corr with all   = 0.30
Cross-sector / unknown:                                   corr             = 0.30
```

### Random shock events

~0.1% chance per tick per ticker of a sudden 2–5% move (up or down). With 10 tickers at 2 ticks/sec, expect a shock event roughly every 50 seconds.

### Seed prices and parameters

**File:** `backend/app/market/seed_prices.py`

```python
SEED_PRICES = {
    "AAPL": 190.00, "GOOGL": 175.00, "MSFT": 420.00,
    "AMZN": 185.00, "TSLA": 250.00,  "NVDA": 800.00,
    "META": 500.00, "JPM":  195.00,  "V":    280.00,
    "NFLX": 600.00,
}

TICKER_PARAMS = {
    "AAPL":  {"sigma": 0.22, "mu": 0.05},
    "GOOGL": {"sigma": 0.25, "mu": 0.05},
    "MSFT":  {"sigma": 0.20, "mu": 0.05},
    "AMZN":  {"sigma": 0.28, "mu": 0.05},
    "TSLA":  {"sigma": 0.50, "mu": 0.03},  # High volatility
    "NVDA":  {"sigma": 0.40, "mu": 0.08},  # High vol, strong drift
    "META":  {"sigma": 0.30, "mu": 0.05},
    "JPM":   {"sigma": 0.18, "mu": 0.04},  # Low vol (bank)
    "V":     {"sigma": 0.17, "mu": 0.04},  # Low vol (payments)
    "NFLX":  {"sigma": 0.35, "mu": 0.05},
}

DEFAULT_PARAMS = {"sigma": 0.25, "mu": 0.05}  # For dynamically added tickers
```

Tickers not in `SEED_PRICES` (added dynamically by the user) start at a random price between $50–$300.

### `GBMSimulator` — internal class

`SimulatorDataSource` wraps `GBMSimulator`. Direct use is not normally needed, but here is the API if you need it:

```python
from app.market.simulator import GBMSimulator

sim = GBMSimulator(tickers=["AAPL", "GOOGL"])
prices = sim.step()       # → {"AAPL": 190.23, "GOOGL": 175.11}
sim.add_ticker("TSLA")    # Rebuilds Cholesky matrix
sim.remove_ticker("GOOGL")
sim.get_price("AAPL")     # → float | None
sim.get_tickers()         # → ["AAPL", "TSLA"]
```

---

## 7. Massive API Client — `MassiveDataSource`

**File:** `backend/app/market/massive_client.py`

Used when `MASSIVE_API_KEY` is set. Polls the Polygon.io REST API (`GET /v2/snapshot/locale/us/markets/stocks/tickers`) for all watched tickers in a single API call per poll cycle.

```python
class MassiveDataSource(MarketDataSource):
    def __init__(
        self,
        api_key: str,
        price_cache: PriceCache,
        poll_interval: float = 15.0,   # 15s = safe for free tier (5 req/min)
    )
```

### Poll cycle

```
start() called
    → immediate first poll (cache has data right away, no blank state)
    → background task starts: sleep(interval) → poll → sleep(interval) → ...

Each poll:
    → asyncio.to_thread(client.get_snapshot_all(...))   # sync client → thread pool
    → for each snapshot: cache.update(ticker, last_trade.price, last_trade.timestamp/1000)
    → errors logged but not re-raised (loop continues)
```

### Rate limits

| Tier | Limit | Safe poll interval |
|------|-------|--------------------|
| Free | 5 req/min | 15s (default) |
| Paid | Unlimited | 2–5s |

Change the interval by passing `poll_interval` to `MassiveDataSource`, or configure via env var in the factory if needed.

### What fields are extracted

From each ticker's snapshot:
- `snap.last_trade.price` → stored as current price
- `snap.last_trade.timestamp` → divided by 1000 (ms → seconds) and stored as timestamp

`day.previous_close` and `day.change_percent` are available on the snapshot but not currently stored — the `PriceCache` computes its own `previous_price` / `change` from successive updates.

### Error handling

The poller catches all exceptions in `_poll_once()` and logs them without crashing. Common failure modes:
- `401` — bad API key
- `403` — plan doesn't include the endpoint
- `429` — rate limit exceeded (back off or increase `poll_interval`)
- Network errors — transient, will retry on next interval

---

## 8. Factory — `create_market_data_source()`

**File:** `backend/app/market/factory.py`

```python
from app.market import create_market_data_source, PriceCache

cache = PriceCache()
source = create_market_data_source(cache)
# Returns SimulatorDataSource if MASSIVE_API_KEY is unset/empty
# Returns MassiveDataSource  if MASSIVE_API_KEY is set and non-empty
```

The factory reads `MASSIVE_API_KEY` from the environment at call time. It logs which source was selected at `INFO` level.

Both implementations are always imported (not lazy) — the `massive` package is a required dependency in `pyproject.toml` whether or not a key is configured.

---

## 9. SSE Streaming Endpoint

**File:** `backend/app/market/stream.py`

**Endpoint:** `GET /api/stream/prices`

### Registering the router

```python
from app.market import create_stream_router, PriceCache

cache = PriceCache()
stream_router = create_stream_router(cache)
app.include_router(stream_router)
```

`create_stream_router(cache)` is a factory that binds the `PriceCache` instance to the route handler via closure and returns the `APIRouter`. The router is already configured with `prefix="/api/stream"`.

### What the client receives

The SSE stream sends one event every ~500ms whenever `PriceCache.version` has changed (i.e., at least one price updated since the last event). A version-based check prevents sending duplicate payloads when nothing has changed.

**Event format:**

```
retry: 1000

data: {"AAPL": {"ticker": "AAPL", "price": 191.45, "previous_price": 191.20, "timestamp": 1711234567.123, "change": 0.25, "change_percent": 0.1307, "direction": "up"}, "GOOGL": {...}, ...}

data: {"AAPL": {...}, "GOOGL": {...}, ...}
```

- The first event is always `retry: 1000` — tells the browser to wait 1 second before reconnecting on disconnect
- Each subsequent event contains **all** tracked tickers, not just changed ones
- The `data:` payload is a single JSON object keyed by ticker symbol

### Frontend consumption

```typescript
const source = new EventSource('/api/stream/prices');

source.onmessage = (event) => {
  const prices: Record<string, PriceUpdate> = JSON.parse(event.data);
  // prices["AAPL"].price, prices["AAPL"].direction, etc.
};

source.onerror = () => {
  // EventSource automatically reconnects after 1s (retry directive)
  // Update connection status indicator to "reconnecting"
};
```

### Response headers

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no   ← disables nginx buffering if running behind a proxy
```

### Disconnect handling

The generator checks `await request.is_disconnected()` on each iteration and stops cleanly. This prevents memory leaks from accumulated dead connections.

---

## 10. FastAPI Lifecycle Integration

The market data source must be started on app startup and stopped on shutdown. Use FastAPI's `lifespan` context manager.

**`backend/app/main.py`** — recommended integration pattern:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.market import PriceCache, create_market_data_source, create_stream_router
from app.database import init_db, get_default_watchlist  # to be built

# Module-level singletons accessed by route handlers
price_cache: PriceCache | None = None
market_source = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global price_cache, market_source

    # Initialize database (creates tables + seeds default data if needed)
    await init_db()

    # Load initial watchlist from DB
    tickers = await get_default_watchlist()  # e.g. ["AAPL", "GOOGL", ...]

    # Start market data
    price_cache = PriceCache()
    market_source = create_market_data_source(price_cache)
    await market_source.start(tickers)

    yield  # Application runs here

    # Shutdown
    if market_source:
        await market_source.stop()


app = FastAPI(lifespan=lifespan)

# Register SSE stream route
# (must happen after price_cache is created — use a dependency instead if preferred)
stream_router = create_stream_router(price_cache)
app.include_router(stream_router)

# Serve static Next.js frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

### Dependency injection pattern (preferred for routes)

Rather than using module-level globals, expose `price_cache` and `market_source` via FastAPI dependencies:

```python
from fastapi import Depends

def get_price_cache() -> PriceCache:
    return price_cache  # module-level singleton set in lifespan

def get_market_source() -> MarketDataSource:
    return market_source

# In a route:
@app.get("/api/watchlist")
async def get_watchlist(
    cache: PriceCache = Depends(get_price_cache),
    db: AsyncConnection = Depends(get_db),
):
    tickers = await db_get_watchlist(db)
    return [
        {"ticker": t, "price": cache.get_price(t), "update": cache.get(t)}
        for t in tickers
    ]
```

---

## 11. Watchlist Coordination

When the user adds or removes a ticker via the watchlist API, **three things must happen together**:

1. Update the database (persist the change)
2. Call `source.add_ticker(ticker)` or `source.remove_ticker(ticker)` — updates the data source's active set
3. `remove_ticker` also removes the ticker from `PriceCache` automatically

```python
@app.post("/api/watchlist")
async def add_to_watchlist(
    body: AddTickerRequest,
    source: MarketDataSource = Depends(get_market_source),
    db: AsyncConnection = Depends(get_db),
):
    ticker = body.ticker.upper().strip()

    # 1. Persist to DB
    await db_add_watchlist_entry(db, ticker)

    # 2. Tell the data source to start tracking it
    await source.add_ticker(ticker)

    # The simulator seeds the cache immediately in add_ticker().
    # The Massive poller will include it in the next poll cycle.
    return {"ticker": ticker, "status": "added"}


@app.delete("/api/watchlist/{ticker}")
async def remove_from_watchlist(
    ticker: str,
    source: MarketDataSource = Depends(get_market_source),
    db: AsyncConnection = Depends(get_db),
):
    ticker = ticker.upper().strip()
    await db_remove_watchlist_entry(db, ticker)
    await source.remove_ticker(ticker)  # also removes from PriceCache
    return {"ticker": ticker, "status": "removed"}
```

**Simulator behavior on `add_ticker`:** seeds the cache immediately with the starting price, so the frontend gets a price on the very next SSE event (no blank state).

**Massive behavior on `add_ticker`:** the ticker is added to the internal list; it will appear in cache on the next poll cycle (up to 15 seconds later on free tier).

---

## 12. Using Prices in Portfolio & Trade Logic

### Getting the current price for a trade

```python
from app.market import PriceCache

async def execute_trade(ticker: str, quantity: float, side: str, cache: PriceCache, db):
    price = cache.get_price(ticker)
    if price is None:
        raise HTTPException(400, f"No price data available for {ticker}")

    cost = price * quantity

    if side == "buy":
        # Deduct cash, create/update position
        ...
    elif side == "sell":
        # Check sufficient shares, add cash, update/remove position
        ...

    # Record trade in DB
    await db_insert_trade(db, ticker=ticker, side=side, quantity=quantity, price=price)
```

### Valuing the portfolio

```python
async def get_portfolio_value(positions: list[Position], cache: PriceCache) -> float:
    total = 0.0
    for pos in positions:
        current_price = cache.get_price(pos.ticker)
        if current_price is not None:
            total += current_price * pos.quantity
    return total


async def get_portfolio_response(cash: float, positions: list[Position], cache: PriceCache):
    enriched = []
    for pos in positions:
        update = cache.get(pos.ticker)
        current_price = update.price if update else pos.avg_cost
        unrealized_pnl = (current_price - pos.avg_cost) * pos.quantity
        pnl_percent = ((current_price - pos.avg_cost) / pos.avg_cost * 100) if pos.avg_cost else 0

        enriched.append({
            "ticker": pos.ticker,
            "quantity": pos.quantity,
            "avg_cost": pos.avg_cost,
            "current_price": current_price,
            "unrealized_pnl": round(unrealized_pnl, 2),
            "pnl_percent": round(pnl_percent, 2),
            "direction": update.direction if update else "flat",
        })

    positions_value = sum(p["current_price"] * p["quantity"] for p in enriched)
    return {
        "cash": cash,
        "positions": enriched,
        "positions_value": round(positions_value, 2),
        "total_value": round(cash + positions_value, 2),
    }
```

### Providing context to the LLM chat

When the LLM needs portfolio context, enrich it with live prices from the cache:

```python
async def build_llm_context(cache: PriceCache, cash: float, positions, watchlist_tickers):
    watchlist_with_prices = [
        {
            "ticker": t,
            "price": cache.get_price(t),
            "direction": cache.get(t).direction if cache.get(t) else "flat",
        }
        for t in watchlist_tickers
    ]
    portfolio = await get_portfolio_response(cash, positions, cache)
    return {
        "cash": cash,
        "total_value": portfolio["total_value"],
        "positions": portfolio["positions"],
        "watchlist": watchlist_with_prices,
    }
```

---

## 13. Configuration

| Environment Variable | Default | Effect |
|---------------------|---------|--------|
| `MASSIVE_API_KEY` | _(unset)_ | If set and non-empty, use Massive/Polygon.io REST API. Otherwise use GBM simulator. |
| `LLM_MOCK` | `false` | Set to `true` to return deterministic mock LLM responses (for E2E tests). Does not affect market data. |

The `.env` file in the project root is read by Docker at runtime. A `.env.example` is committed; `.env` is gitignored.

### Simulator tuning (not env-configurable — change in code if needed)

| Parameter | Default | Location |
|-----------|---------|----------|
| Update interval | 500ms | `SimulatorDataSource.__init__(update_interval=0.5)` |
| Shock event probability | 0.1% per tick | `SimulatorDataSource.__init__(event_probability=0.001)` |
| Shock magnitude | 2–5% | `GBMSimulator.step()` |
| `dt` (time step) | `8.48e-8` | `GBMSimulator.DEFAULT_DT` |

### Massive tuning

| Parameter | Default | How to change |
|-----------|---------|---------------|
| Poll interval | 15s | Pass `poll_interval=` to `MassiveDataSource`, or add a `MASSIVE_POLL_INTERVAL` env var to the factory |

---

## Demo

A Rich terminal demo runs the simulator standalone:

```bash
cd backend
uv run market_data_demo.py
```

Shows a live-updating table of all 10 tickers with prices, change %, direction arrows, sparklines, and an event log for notable moves (>1% change). Runs for 60 seconds or until Ctrl+C, then prints a session summary.
