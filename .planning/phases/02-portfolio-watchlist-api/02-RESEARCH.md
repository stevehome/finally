# Phase 2: Portfolio & Watchlist API - Research

**Researched:** 2026-03-30
**Domain:** FastAPI REST endpoints, SQLite portfolio math, async background tasks
**Confidence:** HIGH

## Summary

Phase 2 builds on the complete Phase 1 foundation: FastAPI app, SQLite database (all 6 tables created and seeded), market data subsystem (PriceCache + MarketDataSource), and SSE streaming. All infrastructure is proven working — 84 tests pass. Phase 2 adds three pure-Python router modules and one background task; no new dependencies are required.

The portfolio router encapsulates trade execution logic: atomic SQLite transactions for buy/sell, weighted-average cost basis updates, and validation errors returned as 422 responses. The watchlist router delegates to the existing `MarketDataSource` interface (`add_ticker` / `remove_ticker`) to keep price streaming in sync. A background task running via `asyncio.create_task` records portfolio snapshots every 30 seconds (same pattern already used by the simulator).

The key design challenge is making the shared `source: MarketDataSource` instance accessible from the watchlist router. The cleanest approach (matching existing patterns in `main.py`) is module-level dependency injection: expose `source` from `main.py` or via FastAPI's `app.state`.

**Primary recommendation:** Add three router files (`portfolio.py`, `watchlist.py`, snapshot background task) under `backend/app/routers/`, inject `price_cache` and `source` via `app.state` set in lifespan, register routers in `main.py`.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PORT-01 | GET /api/portfolio returns cash, positions, total value, unrealized P&L | db.get_connection() → SELECT users_profile + positions; price from PriceCache |
| PORT-02 | POST /api/portfolio/trade (buy) decreases cash, creates/updates position | Atomic SQLite transaction: UPDATE cash, UPSERT positions, INSERT trades |
| PORT-03 | POST /api/portfolio/trade (sell) increases cash, reduces/removes position | Same transaction; DELETE position if quantity reaches 0 |
| PORT-04 | Trade rejected (not 500) for insufficient cash or insufficient shares | Validation before DB write; raise HTTPException(400) |
| PORT-05 | Trade records entry in trades history table | INSERT INTO trades inside same atomic transaction as cash/position update |
| PORT-06 | Portfolio snapshot recorded immediately after each trade | Call snapshot helper at end of trade handler |
| PORT-07 | Background task records portfolio snapshots every 30 seconds | asyncio.create_task() in lifespan; loop with asyncio.sleep(30) |
| PORT-08 | GET /api/portfolio/history returns portfolio value snapshots | SELECT * FROM portfolio_snapshots ORDER BY recorded_at |
| WATCH-01 | GET /api/watchlist returns tickers with current prices | DB tickers + PriceCache.get() per ticker |
| WATCH-02 | POST /api/watchlist adds a ticker | INSERT INTO watchlist + await source.add_ticker() |
| WATCH-03 | DELETE /api/watchlist/{ticker} removes a ticker | DELETE FROM watchlist + await source.remove_ticker() |
| WATCH-04 | Adding ticker starts price streaming | source.add_ticker() is already implemented; just call it |
| WATCH-05 | Removing ticker stops price streaming | source.remove_ticker() removes from cache too; already implemented |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Python tooling:** Always `uv run` / `uv add`, never `python3` / `pip install`
- **Single port 8000:** All routes on the FastAPI app; no separate servers
- **Tech stack fixed:** FastAPI + uv, SQLite, no ORMs
- **LLM provider:** Not applicable this phase
- **No auth:** Single user "default" hardcoded
- **Market orders only:** Instant execution at current cache price
- **Code style:** ruff, 100-char lines, snake_case, type hints, Google-style docstrings
- **Naming:** `snake_case.py` modules, `PascalCase` classes, `_private` prefix for internal
- **Error handling:** Specific exceptions; `logger.exception()` when catching
- **Async patterns:** `asyncio.create_task()` for background; `asyncio.sleep()` not `time.sleep()`
- **DB_PATH test isolation:** `conftest.py` `tmp_db` fixture monkeypatches DB_PATH; new tests must work with it
- **Module-level shared objects:** PriceCache and stream_router created at module level in `main.py` before lifespan (keep this pattern)

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.128.7 (installed) | Router, HTTPException, Depends | Already in use |
| sqlite3 | stdlib | DB access | Already in use; schema complete |
| pydantic | 2.12.5 (installed) | Request/response models | FastAPI's built-in validation |
| asyncio | stdlib | Background snapshot task | Already used in simulator |
| uuid | stdlib | Primary key generation | Already used in db.py |

### No New Dependencies Required
All required libraries are already installed. No `uv add` needed this phase.

## Architecture Patterns

### Recommended Project Structure (additions only)
```
backend/app/
├── routers/
│   ├── __init__.py          # already exists (empty)
│   ├── health.py            # already exists
│   ├── portfolio.py         # NEW: PORT-01 through PORT-08
│   └── watchlist.py         # NEW: WATCH-01 through WATCH-05
├── db.py                    # extend with portfolio/watchlist DB helpers
```

### Pattern 1: app.state for Shared Dependencies

`main.py` stores `price_cache` and `source` on `app.state` in lifespan; routers access via `request.app.state` or a `Depends` helper. This matches FastAPI idiom and avoids circular imports.

**Existing pattern in main.py (module-level):**
```python
# Already in main.py — keep as-is
price_cache = PriceCache()
stream_router = create_stream_router(price_cache)
```

**Add to lifespan in main.py:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    tickers = get_watchlist_tickers()
    source = create_market_data_source(price_cache)
    await source.start(tickers)
    app.state.price_cache = price_cache   # expose for routers
    app.state.source = source             # expose for watchlist router
    # Start snapshot background task
    snapshot_task = asyncio.create_task(_snapshot_loop(app))
    yield
    snapshot_task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await snapshot_task
    await source.stop()
```

### Pattern 2: Atomic Trade Transaction

All trade mutations (cash update, position upsert, trade insert) must execute in a single SQLite transaction to prevent partial writes on error.

```python
# Conceptual — actual code in portfolio.py
def execute_trade(ticker: str, side: str, quantity: float, price: float) -> None:
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        # 1. Validate cash / shares
        # 2. UPDATE users_profile cash
        # 3. INSERT OR REPLACE INTO positions (upsert with weighted avg)
        # 4. INSERT INTO trades
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

### Pattern 3: Weighted Average Cost Basis

On a buy, the new avg_cost = (old_qty * old_avg + new_qty * price) / (old_qty + new_qty). On a sell, avg_cost does not change (only quantity decreases). Remove the position row when quantity reaches 0.

```python
# Buy upsert (SQLite does not support expressions in ON CONFLICT SET easily)
# Preferred: read existing row, compute in Python, then upsert
existing = conn.execute("SELECT quantity, avg_cost FROM positions WHERE user_id=? AND ticker=?", ...)
if existing:
    old_qty, old_avg = existing
    new_qty = old_qty + quantity
    new_avg = (old_qty * old_avg + quantity * price) / new_qty
    conn.execute("UPDATE positions SET quantity=?, avg_cost=?, updated_at=? WHERE user_id=? AND ticker=?", ...)
else:
    conn.execute("INSERT INTO positions ...", ...)
```

### Pattern 4: Portfolio Snapshot Background Task

Same `asyncio.create_task` + `asyncio.CancelledError` pattern as the simulator loop:

```python
async def _snapshot_loop(app: FastAPI) -> None:
    """Record portfolio value every 30 seconds."""
    while True:
        try:
            await asyncio.sleep(30)
            _record_snapshot(app.state.price_cache)
        except asyncio.CancelledError:
            break
```

### Pattern 5: HTTPException for Validation Errors

PORT-04 requires returning an error response (not 500) for insufficient funds/shares. Use `HTTPException(status_code=400, detail="...")` raised before any DB writes.

```python
from fastapi import HTTPException

if side == "buy" and cash_balance < quantity * current_price:
    raise HTTPException(status_code=400, detail="Insufficient cash")
if side == "sell" and current_quantity < quantity:
    raise HTTPException(status_code=400, detail="Insufficient shares")
```

### Pattern 6: Request Body via Pydantic Model

```python
from pydantic import BaseModel

class TradeRequest(BaseModel):
    ticker: str
    quantity: float
    side: str  # "buy" or "sell"
```

### Anti-Patterns to Avoid

- **Bare `except:` clauses:** Catch `sqlite3.Error` or `Exception` specifically, log with `logger.exception()`
- **Separate transactions per mutation:** All trade mutations must be one atomic transaction
- **Global module-level `source` variable (circular):** Access via `request.app.state` or pass via `Depends` — do not import `source` from `main.py` (circular import)
- **`time.sleep()` in background task:** Must be `await asyncio.sleep(30)`
- **Delete position without checking quantity == 0:** Always check; fractional shares are supported

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Request validation | Manual type checks | Pydantic BaseModel + FastAPI | Handles type coercion, error formatting automatically |
| HTTP error responses | Return dicts with error keys | `raise HTTPException(400, detail=...)` | Standard FastAPI pattern; correct HTTP status codes |
| Background task lifecycle | Manual thread management | `asyncio.create_task()` + cancel in lifespan | Matches existing simulator pattern; clean shutdown |
| Price lookup | Re-query market data | `price_cache.get_price(ticker)` | Cache is always fresh; avoids I/O |

## Common Pitfalls

### Pitfall 1: Circular Import (main.py ↔ routers)
**What goes wrong:** Router imports `source` from `main.py`; `main.py` imports routers → circular import at module load.
**Why it happens:** `source` is created in `main.py` lifespan, but routers need it at request time.
**How to avoid:** Store `source` on `app.state` in lifespan; access in router via `request.app.state.source`.
**Warning signs:** `ImportError: cannot import name 'source' from 'main'` at startup.

### Pitfall 2: Background Task Not Cancelled on Shutdown
**What goes wrong:** Snapshot loop runs after app shutdown; may write to closed DB or cause test hangs.
**Why it happens:** `asyncio.create_task()` tasks continue unless explicitly cancelled.
**How to avoid:** Cancel the task in the lifespan teardown and `await` it, suppressing `CancelledError`.
**Warning signs:** Tests hang or produce `Task was destroyed but pending` warnings.

### Pitfall 3: Race on Cash/Position Read-Then-Write
**What goes wrong:** Two concurrent trades pass the cash check but together overdraw the balance.
**Why it happens:** Validation and mutation are separate operations in different statements.
**How to avoid:** Run validation inside the same SQLite transaction with an explicit `BEGIN`. SQLite's write lock serializes concurrent writes.
**Warning signs:** Cash balance goes negative; positions show impossible quantities.

### Pitfall 4: DB_PATH Module-Level Caching in Router
**What goes wrong:** Router helper function reads `DB_PATH` at import time; test `tmp_db` fixture sets env var after import.
**Why it happens:** `db.py` already handles this correctly by reading `DB_PATH` at call time, not import time. New router functions that duplicate this pattern must do the same.
**How to avoid:** Always use `get_connection()` from `app.db` (reads `DB_PATH` lazily) — never cache the path at import time.
**Warning signs:** Router tests write to the real `db/finally.db` instead of the temp file.

### Pitfall 5: Watchlist Add Without Validation
**What goes wrong:** User adds an invalid or duplicate ticker; DB raises `UNIQUE constraint failed` as an unhandled exception → 500.
**Why it happens:** `UNIQUE(user_id, ticker)` constraint on the watchlist table.
**How to avoid:** Use `INSERT OR IGNORE` for idempotent adds, or catch `sqlite3.IntegrityError` and return 409.
**Warning signs:** `Internal Server Error` when adding a ticker that already exists.

### Pitfall 6: source Not Yet Running When Watchlist Router Calls add_ticker
**What goes wrong:** Watchlist endpoint called before lifespan fully initializes (edge case during startup).
**Why it happens:** `app.state.source` is set inside the lifespan `async with` block.
**How to avoid:** Access `app.state.source` inside the route handler body (at request time), not at module/router instantiation time. FastAPI's `app.state` is set before any requests are processed.
**Warning signs:** `AttributeError: 'State' object has no attribute 'source'` on first request.

## Code Examples

### Route: GET /api/portfolio
```python
# Source: FastAPI patterns + project db.py conventions
@router.get("/portfolio")
async def get_portfolio(request: Request) -> dict:
    """Return cash, positions with unrealized P&L, and total portfolio value."""
    price_cache: PriceCache = request.app.state.price_cache
    conn = get_connection()
    try:
        profile = conn.execute(
            "SELECT cash_balance FROM users_profile WHERE id = 'default'"
        ).fetchone()
        positions = conn.execute(
            "SELECT ticker, quantity, avg_cost FROM positions WHERE user_id = 'default'"
        ).fetchall()
    finally:
        conn.close()

    cash = profile["cash_balance"]
    positions_out = []
    positions_value = 0.0
    for row in positions:
        price = price_cache.get_price(row["ticker"]) or row["avg_cost"]
        unrealized = (price - row["avg_cost"]) * row["quantity"]
        value = price * row["quantity"]
        positions_value += value
        positions_out.append({
            "ticker": row["ticker"],
            "quantity": row["quantity"],
            "avg_cost": row["avg_cost"],
            "current_price": price,
            "unrealized_pnl": round(unrealized, 2),
            "value": round(value, 2),
        })
    return {
        "cash_balance": cash,
        "positions": positions_out,
        "total_value": round(cash + positions_value, 2),
    }
```

### Route: POST /api/watchlist
```python
# Source: project patterns; watchlist table schema in db.py
@router.post("/watchlist", status_code=201)
async def add_to_watchlist(body: WatchlistAddRequest, request: Request) -> dict:
    source: MarketDataSource = request.app.state.source
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) VALUES (?,?,?,?)",
            (str(uuid.uuid4()), "default", body.ticker.upper(), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    await source.add_ticker(body.ticker.upper())
    return {"ticker": body.ticker.upper()}
```

### Snapshot Helper
```python
def record_snapshot(price_cache: PriceCache) -> None:
    """Insert a portfolio_snapshots row with the current total value."""
    conn = get_connection()
    try:
        profile = conn.execute("SELECT cash_balance FROM users_profile WHERE id='default'").fetchone()
        positions = conn.execute("SELECT ticker, quantity FROM positions WHERE user_id='default'").fetchall()
        total = profile["cash_balance"]
        for row in positions:
            price = price_cache.get_price(row["ticker"]) or 0.0
            total += row["quantity"] * price
        conn.execute(
            "INSERT INTO portfolio_snapshots (id, user_id, total_value, recorded_at) VALUES (?,?,?,?)",
            (str(uuid.uuid4()), "default", round(total, 2), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.24+ |
| Config file | `backend/pyproject.toml` (asyncio_mode = "auto") |
| Quick run command | `cd backend && uv run --extra dev pytest tests/ -q` |
| Full suite command | `cd backend && uv run --extra dev pytest tests/ --cov=app -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PORT-01 | GET /api/portfolio returns cash + positions + total | unit | `pytest tests/test_portfolio.py::test_get_portfolio -x` | ❌ Wave 0 |
| PORT-02 | Buy trade decreases cash, upserts position | unit | `pytest tests/test_portfolio.py::test_buy_trade -x` | ❌ Wave 0 |
| PORT-03 | Sell trade increases cash, reduces position | unit | `pytest tests/test_portfolio.py::test_sell_trade -x` | ❌ Wave 0 |
| PORT-04 | Insufficient cash → 400, not 500 | unit | `pytest tests/test_portfolio.py::test_buy_insufficient_cash -x` | ❌ Wave 0 |
| PORT-04 | Insufficient shares → 400, not 500 | unit | `pytest tests/test_portfolio.py::test_sell_insufficient_shares -x` | ❌ Wave 0 |
| PORT-05 | Trade inserts into trades table | unit | `pytest tests/test_portfolio.py::test_trade_history_recorded -x` | ❌ Wave 0 |
| PORT-06 | Snapshot recorded after trade | unit | `pytest tests/test_portfolio.py::test_snapshot_after_trade -x` | ❌ Wave 0 |
| PORT-07 | Background task records snapshots every 30s | unit (mocked sleep) | `pytest tests/test_portfolio.py::test_snapshot_background_task -x` | ❌ Wave 0 |
| PORT-08 | GET /api/portfolio/history returns snapshots | unit | `pytest tests/test_portfolio.py::test_portfolio_history -x` | ❌ Wave 0 |
| WATCH-01 | GET /api/watchlist returns tickers + prices | unit | `pytest tests/test_watchlist.py::test_get_watchlist -x` | ❌ Wave 0 |
| WATCH-02 | POST /api/watchlist adds ticker | unit | `pytest tests/test_watchlist.py::test_add_ticker -x` | ❌ Wave 0 |
| WATCH-03 | DELETE /api/watchlist/{ticker} removes ticker | unit | `pytest tests/test_watchlist.py::test_remove_ticker -x` | ❌ Wave 0 |
| WATCH-04 | Add ticker calls source.add_ticker | unit (mock source) | `pytest tests/test_watchlist.py::test_add_ticker_starts_streaming -x` | ❌ Wave 0 |
| WATCH-05 | Remove ticker calls source.remove_ticker | unit (mock source) | `pytest tests/test_watchlist.py::test_remove_ticker_stops_streaming -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `cd backend && uv run --extra dev pytest tests/ -q`
- **Per wave merge:** `cd backend && uv run --extra dev pytest tests/ --cov=app -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_portfolio.py` — covers PORT-01 through PORT-08
- [ ] `tests/test_watchlist.py` — covers WATCH-01 through WATCH-05
- [ ] Existing `tests/conftest.py` is sufficient (tmp_db autouse fixture already handles DB isolation)

## Environment Availability

Step 2.6: No new external dependencies identified. All required tools and libraries are already installed and verified.

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.12 | Backend runtime | ✓ | 3.12 (via uv) | — |
| fastapi | HTTP routing | ✓ | 0.128.7 | — |
| pydantic | Request models | ✓ | 2.12.5 | — |
| pytest | Testing | ✓ | 8.3+ | — |
| SQLite | Data persistence | ✓ | stdlib | — |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pydantic v1 `.dict()` | Pydantic v2 `.model_dump()` | Pydantic v2 (2023) | Use `.model_dump()` not `.dict()` |
| FastAPI `@app.on_event("startup")` | `@asynccontextmanager lifespan` | FastAPI 0.93+ | Already used in main.py — keep |
| Manual background threads | `asyncio.create_task()` | — | Already used in simulator — keep |

## Open Questions

1. **Fractional shares rounding**
   - What we know: Schema allows `REAL` (float) for quantity; spec says "fractional shares supported"
   - What's unclear: Should API round to N decimal places, or accept arbitrary float?
   - Recommendation: Accept any positive float; no rounding enforced at API layer. Let frontend control precision.

2. **Portfolio history time range**
   - What we know: GET /api/portfolio/history returns all snapshots
   - What's unclear: Does the frontend need pagination or filtering by time range?
   - Recommendation: Return all rows for now (Phase 2 scope); add `?limit=N` in a later phase if needed.

3. **Current price for positions with no cache entry**
   - What we know: `PriceCache.get_price()` returns `None` if ticker not yet priced
   - What's unclear: What to return in portfolio if a ticker has no live price yet?
   - Recommendation: Fall back to `avg_cost` as the current_price (conservative); mark with a flag if needed.

## Sources

### Primary (HIGH confidence)
- Project codebase (`backend/app/db.py`, `backend/main.py`, `backend/app/market/`) — verified by direct read
- Project `backend/pyproject.toml` — version numbers confirmed
- FastAPI `app.state` pattern — standard FastAPI documentation, verified against installed version 0.128.7
- `asyncio.create_task` + `CancelledError` pattern — identical to existing `simulator.py` background task

### Secondary (MEDIUM confidence)
- Pydantic v2 `.model_dump()` (not `.dict()`) — confirmed by installed version 2.12.5

### Tertiary (LOW confidence)
- None — all critical claims verified against codebase or stdlib docs

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, versions confirmed
- Architecture: HIGH — patterns established in Phase 1 codebase; app.state is standard FastAPI
- Pitfalls: HIGH — derived from actual code inspection + known FastAPI/SQLite patterns

**Research date:** 2026-03-30
**Valid until:** 2026-06-30 (stable stack; only risk is FastAPI patch releases)
