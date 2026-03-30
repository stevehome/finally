# Phase 1: Backend Foundation - Context

**Gathered:** 2026-03-30 (assumptions mode — user skipped discussion)
**Status:** Ready for planning

<domain>
## Phase Boundary

FastAPI backend starts, initializes SQLite with schema + seed data, integrates the market data subsystem, and passes a health check. No business logic endpoints — those are Phase 2 (portfolio/watchlist) and Phase 3 (chat). Phase 1 delivers a running, seeded, streaming backend.

</domain>

<decisions>
## Implementation Decisions

### Database Layer
- **D-01:** Single `backend/app/db.py` module — schema creation, seed data insertion, and connection helpers in one file. Keeps it readable for a course demo; no `db/` package needed at this scale.
- **D-02:** Lazy initialization on app startup (lifespan event), not per-request. DB file created at `db/finally.db` relative to the project root (volume-mounted path `/app/db/finally.db` in Docker).
- **D-03:** Use Python stdlib `sqlite3` directly — no ORM. The schema is simple and fixed; SQLAlchemy would be overkill.
- **D-04:** Idempotent init — `CREATE TABLE IF NOT EXISTS` + insert-or-ignore for seed rows. Safe to call on every startup.

### App Entry Point
- **D-05:** `backend/main.py` is the single entry point. Uses FastAPI lifespan context manager (not deprecated `@app.on_event`). Wires up: DB init, market data source start, SSE router attachment, static file serving stub.
- **D-06:** No separate app factory for Phase 1. Single `app = FastAPI(lifespan=lifespan)` in `main.py` — keep it simple. Phases 2+ attach their own routers to the same app instance.
- **D-07:** Market data source starts with the 10 default tickers (read from DB after seed). Startup sequence: init DB → read watchlist tickers → create market data source → start with those tickers.

### Router Scope
- **D-08:** Phase 1 only creates `GET /api/health`. No stub routers for portfolio/watchlist/chat — those phases create their own routers and attach them. Keeps Phase 1 minimal.
- **D-09:** Health check returns a richer diagnostic: `{"status": "ok", "db": "ok", "market_data": "running"}`. Useful for debugging; trivial to implement.

### SSE Integration
- **D-10:** SSE router (`/api/stream/prices`) attached at startup using the existing `create_stream_router(price_cache)` factory from `backend/app/market/stream.py`. No changes to the market module.

### Claude's Discretion
- Exact SQL schema (column types, constraints) — follow the spec in PLAN.md §7
- Logging setup (log level, format) — use Python `logging` with `rich` handler if convenient
- Static file serving placeholder — `app.mount("/", StaticFiles(...))` stub; frontend not built yet

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Database Schema & Seed
- `planning/PLAN.md` §7 — Full SQLite schema (6 tables), default seed data (users_profile, watchlist), lazy init strategy

### API Endpoints
- `planning/PLAN.md` §8 — API endpoint table (health check in System section)

### Market Data Integration
- `planning/MARKET_DATA_SUMMARY.md` — Complete market subsystem summary; public API, module list, startup pattern
- `backend/app/market/__init__.py` — Public exports: `PriceCache`, `create_market_data_source`, `create_stream_router`
- `backend/app/market/factory.py` — How to create the market data source (env-driven)
- `backend/app/market/stream.py` — SSE router factory; requires a `PriceCache` instance

### Architecture
- `planning/PLAN.md` §3 — Single container, single port architecture; FastAPI serves static + API
- `planning/PLAN.md` §11 — Docker structure; `db/` directory as volume mount target

### Existing Backend
- `backend/pyproject.toml` — Dependencies (fastapi, uvicorn, numpy, massive, rich); uv project config
- `backend/app/market/seed_prices.py` — Default tickers (AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/market/` — Complete, tested market data subsystem. Phase 1 only imports and wires it up; no changes needed.
- `PriceCache` — Thread-safe in-memory price store; create one instance, pass to both market source and SSE router.
- `create_market_data_source(price_cache)` — Returns unstarted `MarketDataSource`; call `await source.start(tickers)` in lifespan.
- `create_stream_router(price_cache)` — Returns FastAPI `APIRouter`; attach with `app.include_router(...)`.

### Established Patterns
- Factory injection pattern: both `create_market_data_source` and `create_stream_router` take `PriceCache` as argument — no globals needed.
- Async lifecycle: market data source uses `await source.start(tickers)` / `await source.stop()` — fits cleanly in FastAPI lifespan `async with`.
- `uv run` for all Python execution; never `python3` directly.

### Integration Points
- `main.py` is the new entry point. It will create `PriceCache`, call the factories, init the DB, and expose the app.
- `backend/app/routers/` directory exists but is empty — Phase 1 adds `health.py` here; later phases add more.
- Static file serving goes last (mounted at `/`); FastAPI matches API routes before falling through to static files.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches within the decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-backend-foundation*
*Context gathered: 2026-03-30*
