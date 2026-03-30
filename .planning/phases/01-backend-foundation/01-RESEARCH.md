# Phase 1: Backend Foundation - Research

**Researched:** 2026-03-30
**Domain:** FastAPI lifespan, SQLite init, market data integration, SSE wiring
**Confidence:** HIGH

## Summary

Phase 1 connects existing pieces into a running backend. The market data subsystem (`backend/app/market/`) is complete and tested (73 tests, 84% coverage). The only new files are `backend/main.py` (entry point), `backend/app/db.py` (SQLite init + helpers), and `backend/app/routers/health.py` (GET /api/health).

The FastAPI lifespan context manager (not deprecated `@app.on_event`) is the correct pattern for startup/shutdown in FastAPI 0.128.7. `StaticFiles` from `fastapi.staticfiles` mounts the Next.js export at `/`; since the frontend is not built yet, this mount can be a conditional stub that only activates when the static directory exists.

The startup sequence is strictly ordered: init DB → read watchlist tickers → create `PriceCache` → create market data source via factory → start source with tickers → attach routers → mount static files. Reversing DB init and ticker read would seed defaults before they are readable, breaking D-07.

**Primary recommendation:** Write `main.py` first (lifespan, app wiring), then `app/db.py` (schema + seed), then `app/routers/health.py` (simple endpoint), then wire together and verify with `uv run pytest`.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Single `backend/app/db.py` module — schema creation, seed data insertion, and connection helpers in one file.
- **D-02:** Lazy initialization on app startup (lifespan event), not per-request. DB file created at `db/finally.db` relative to the project root (volume-mounted path `/app/db/finally.db` in Docker).
- **D-03:** Use Python stdlib `sqlite3` directly — no ORM.
- **D-04:** Idempotent init — `CREATE TABLE IF NOT EXISTS` + insert-or-ignore for seed rows.
- **D-05:** `backend/main.py` is the single entry point. Uses FastAPI lifespan context manager (not deprecated `@app.on_event`). Wires up: DB init, market data source start, SSE router attachment, static file serving stub.
- **D-06:** No separate app factory for Phase 1. Single `app = FastAPI(lifespan=lifespan)` in `main.py`.
- **D-07:** Market data source starts with the 10 default tickers (read from DB after seed). Startup sequence: init DB → read watchlist tickers → create market data source → start with those tickers.
- **D-08:** Phase 1 only creates `GET /api/health`. No stub routers for portfolio/watchlist/chat.
- **D-09:** Health check returns `{"status": "ok", "db": "ok", "market_data": "running"}`.
- **D-10:** SSE router (`/api/stream/prices`) attached at startup using existing `create_stream_router(price_cache)` factory.

### Claude's Discretion

- Exact SQL schema (column types, constraints) — follow the spec in PLAN.md §7
- Logging setup (log level, format) — use Python `logging` with `rich` handler if convenient
- Static file serving placeholder — `app.mount("/", StaticFiles(...))` stub; frontend not built yet

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BACK-01 | Backend FastAPI app starts and serves all API routes on port 8000 | `main.py` with lifespan + uvicorn; FastAPI 0.128.7 confirmed installed |
| BACK-02 | SQLite database lazily initializes (creates schema + seeds data on first start) | `app/db.py` with `CREATE TABLE IF NOT EXISTS`; sqlite3 3.46.0 available |
| BACK-03 | Default user profile created with $10,000 cash balance | `users_profile` table seed in `app/db.py` with INSERT OR IGNORE |
| BACK-04 | Default watchlist seeded with 10 tickers (AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX) | `watchlist` table seed in `app/db.py`; tickers match `seed_prices.py` SEED_PRICES keys |
| BACK-05 | Health check endpoint returns 200 OK | `app/routers/health.py` with `GET /api/health`; returns richer diagnostic per D-09 |
| BACK-06 | Market data subsystem (simulator/Massive) integrated at app startup and shutdown | Existing `create_market_data_source` + `create_stream_router` factories; lifecycle fits lifespan pattern |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.128.7 (installed) | HTTP framework, routing, SSE | Already installed; project constraint |
| uvicorn[standard] | 0.40.0 (installed) | ASGI server | Already installed; project constraint |
| sqlite3 | stdlib (3.46.0) | Database | Project decision D-03 — no ORM |
| rich | 13.x (installed) | Logging handler | Project conventions mention rich for logging |

### No New Installations Required

All dependencies are already in `backend/pyproject.toml` and installed in the venv. Phase 1 adds no new packages.

**Verify installed versions:**
```bash
cd backend && uv run python -c "import fastapi, uvicorn; print(fastapi.__version__, uvicorn.__version__)"
# Confirmed: 0.128.7  0.40.0
```

---

## Architecture Patterns

### Recommended File Structure (new files only)

```
backend/
├── main.py                    # NEW — entry point, lifespan, app wiring
├── app/
│   ├── db.py                  # NEW — sqlite3 schema init + seed + connection helpers
│   └── routers/
│       └── health.py          # NEW — GET /api/health
```

Everything else in `backend/app/market/` is unchanged.

### Pattern 1: FastAPI Lifespan Context Manager

**What:** `@asynccontextmanager` function passed to `FastAPI(lifespan=...)`. Code before `yield` runs on startup; code after `yield` runs on shutdown.

**When to use:** Any time you need startup/shutdown hooks in FastAPI 0.95+. The deprecated `@app.on_event("startup")` pattern should NOT be used.

**Example:**
```python
# Source: FastAPI docs, verified against installed 0.128.7
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs before app accepts requests
    init_db()
    tickers = get_watchlist_tickers()
    cache = PriceCache()
    source = create_market_data_source(cache)
    await source.start(tickers)
    stream_router = create_stream_router(cache)
    app.include_router(stream_router)
    yield
    # Shutdown: runs after last request completes
    await source.stop()

app = FastAPI(lifespan=lifespan)
```

### Pattern 2: SQLite Idempotent Init

**What:** `CREATE TABLE IF NOT EXISTS` for schema + `INSERT OR IGNORE` for seed rows. Call once at startup; safe to call on every restart.

**When to use:** Single-file SQLite with no migration framework. Correct for this project scope.

**Example:**
```python
# Source: Python stdlib sqlite3 docs
import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "db/finally.db")

def init_db() -> None:
    """Initialize database schema and seed data. Idempotent."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(_SCHEMA_SQL)
        _seed(conn)

def get_connection() -> sqlite3.Connection:
    """Return a new SQLite connection with row_factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

`sqlite3.Row` as `row_factory` enables dict-style column access (`row["cash_balance"]`) without an ORM.

### Pattern 3: StaticFiles Conditional Mount

**What:** Mount `StaticFiles` at `/` only when the static directory exists. Prevents startup failure when the frontend is not yet built.

**When to use:** Whenever the frontend build output may not exist (e.g., backend-only development, Phase 1).

**Example:**
```python
from fastapi.staticfiles import StaticFiles
import os

STATIC_DIR = "static"  # or wherever Next.js export lands

# Mount AFTER all API routers so API routes are matched first
if os.path.isdir(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
```

`html=True` enables SPA fallback — requests for unknown paths serve `index.html`, which Next.js static export requires.

### Pattern 4: Router Registration

**What:** All API routes live in separate router modules; `main.py` calls `app.include_router(...)`.

**Example:**
```python
from app.routers import health
app.include_router(health.router, prefix="/api")
```

The health router itself uses `prefix=""` or no prefix (since `/api` is applied at include time).

### Anti-Patterns to Avoid

- **Using `@app.on_event("startup")`:** Deprecated since FastAPI 0.95; use lifespan instead.
- **Per-request DB connections without closing:** Always use context managers (`with sqlite3.connect(...) as conn`) or explicitly call `conn.close()`.
- **Global `sqlite3.Connection` object:** sqlite3 connections are not thread-safe by default. Create connections per-request or use `check_same_thread=False` with a lock. For Phase 1, per-operation connections are simpler and correct.
- **Mounting StaticFiles before API routers:** FastAPI matches routes top-to-bottom; StaticFiles at `/` would intercept `/api/*` requests. Always mount static files last.
- **Hardcoding DB path without `os.makedirs`:** The `db/` directory may not exist in a fresh checkout. Create it with `exist_ok=True`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SSE endpoint | Custom streaming response generator | `create_stream_router(cache)` from `app.market` | Already built, tested, handles disconnect, version detection |
| Market data source | New simulator or polling client | `create_market_data_source(cache)` from `app.market` | Complete, 73 tests, env-driven selection |
| Price cache | Custom dict with locking | `PriceCache` from `app.market` | Thread-safe, has version counter for SSE, already in use |
| HTTP testing | Custom test server | `fastapi.testclient.TestClient` | Synchronous in-process testing; no network needed |

**Key insight:** The market data subsystem is the hard part. Phase 1's job is wiring, not building.

---

## Common Pitfalls

### Pitfall 1: Lifespan Router Registration Timing

**What goes wrong:** Attaching the SSE router inside the lifespan `yield` block doesn't work — FastAPI finalizes its route table before the lifespan starts.

**Why it happens:** `include_router` modifies the app's route table, which FastAPI builds at startup. By lifespan time, the route table is already compiled.

**How to avoid:** Call `app.include_router(...)` at module level (before the app starts), OR structure so routers are registered before lifespan runs. For the SSE router, create the `PriceCache` and router at module level or register them in a pre-lifespan setup.

**Concrete solution for this project:**
```python
# Create shared objects at module level
price_cache = PriceCache()
stream_router = create_stream_router(price_cache)
app.include_router(stream_router)  # Register BEFORE lifespan

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    tickers = get_watchlist_tickers()
    source = create_market_data_source(price_cache)  # Uses the same cache
    await source.start(tickers)
    yield
    await source.stop()
```

### Pitfall 2: DB Path Resolution

**What goes wrong:** `sqlite3.connect("db/finally.db")` fails if the working directory is not the project root. In Docker, the working directory is `/app/`.

**Why it happens:** Relative paths resolve from CWD, not from the script location.

**How to avoid:** Use an absolute path derived from an env var or from `__file__`:
```python
import os
# Option A: env var (preferred for Docker)
DB_PATH = os.environ.get("DB_PATH", "/app/db/finally.db")
# Option B: relative to project root via __file__
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT, "db", "finally.db")
```

For local dev (`uv run uvicorn main:app` from `backend/`), the CWD is `backend/`, so `db/finally.db` would create the file inside `backend/db/` not the project root `db/`. Use env var or absolute resolution.

### Pitfall 3: StaticFiles Startup Error

**What goes wrong:** `StaticFiles(directory="static")` raises `RuntimeError: Directory 'static' does not exist` at startup if the directory is missing.

**Why it happens:** FastAPI validates the directory exists when the app is created.

**How to avoid:** Guard the mount with `os.path.isdir(STATIC_DIR)`. The app starts normally without the static mount; API routes work. Frontend phases will add the directory.

### Pitfall 4: INSERT OR IGNORE Requires UNIQUE Constraint

**What goes wrong:** `INSERT OR IGNORE` silently does nothing if there is no UNIQUE constraint on the target column(s). Seed data may appear to insert but actually duplicates.

**Why it happens:** `OR IGNORE` suppresses constraint violations — if there is no constraint, it never fires.

**How to avoid:** The PLAN.md §7 schema includes `UNIQUE (user_id, ticker)` on `watchlist` and `PRIMARY KEY` on `users_profile`. Verify these constraints are present in the schema DDL before relying on INSERT OR IGNORE.

### Pitfall 5: `asyncio_mode = "auto"` Already Set

**What goes wrong:** Adding `@pytest.mark.asyncio` to tests is unnecessary and generates warnings.

**Why it happens:** `pyproject.toml` already has `asyncio_mode = "auto"` — all async test functions are auto-detected.

**How to avoid:** Write `async def test_foo():` without the mark decorator. This matches the pattern in the existing test suite.

---

## Code Examples

### Health Router

```python
# backend/app/routers/health.py
"""Health check endpoint."""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)
router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict:
    """Return service health status."""
    return {"status": "ok", "db": "ok", "market_data": "running"}
```

Note: D-09 specifies this exact response shape. The `db` and `market_data` values can be hardcoded for Phase 1 since both are always initialized at startup; later phases can make them dynamic if needed.

### DB Module Skeleton

```python
# backend/app/db.py
"""SQLite database initialization and connection helpers."""
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "db/finally.db")

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users_profile (
    id TEXT PRIMARY KEY,
    cash_balance REAL NOT NULL DEFAULT 10000.0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS watchlist (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL DEFAULT 'default',
    ticker TEXT NOT NULL,
    added_at TEXT NOT NULL,
    UNIQUE (user_id, ticker)
);
-- ... remaining tables from PLAN.md §7
"""

_DEFAULT_TICKERS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NVDA", "META", "JPM", "V", "NFLX"]

def init_db() -> None:
    """Initialize schema and seed data. Idempotent — safe to call on every startup."""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(_SCHEMA_SQL)
        _seed(conn)

def _seed(conn: sqlite3.Connection) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT OR IGNORE INTO users_profile (id, cash_balance, created_at) VALUES (?, ?, ?)",
        ("default", 10000.0, now),
    )
    import uuid
    for ticker in _DEFAULT_TICKERS:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (id, user_id, ticker, added_at) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), "default", ticker, now),
        )

def get_watchlist_tickers(user_id: str = "default") -> list[str]:
    """Return ticker symbols for the given user's watchlist."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT ticker FROM watchlist WHERE user_id = ? ORDER BY added_at",
            (user_id,),
        ).fetchall()
    return [row[0] for row in rows]

def get_connection() -> sqlite3.Connection:
    """Return a new connection with Row factory. Caller must close."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

### main.py Skeleton

```python
# backend/main.py
"""FinAlly backend entry point."""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.db import init_db, get_watchlist_tickers
from app.market import PriceCache, create_market_data_source, create_stream_router
from app.routers import health

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create shared objects before lifespan so routers can be registered
price_cache = PriceCache()
stream_router = create_stream_router(price_cache)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting FinAlly backend")
    init_db()
    tickers = get_watchlist_tickers()
    source = create_market_data_source(price_cache)
    await source.start(tickers)
    logger.info("Market data started with %d tickers", len(tickers))
    yield
    logger.info("Shutting down")
    await source.stop()

app = FastAPI(title="FinAlly API", lifespan=lifespan)

# API routers — registered before static mount
app.include_router(health.router, prefix="/api")
app.include_router(stream_router)

# Static files — mount last; conditional on directory existing
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | Backend runtime | Yes | 3.12.x (via uv) | — |
| fastapi | API framework | Yes | 0.128.7 | — |
| uvicorn[standard] | ASGI server | Yes | 0.40.0 | — |
| sqlite3 | Database | Yes | 3.46.0 (stdlib) | — |
| rich | Logging | Yes | 13.x | stdlib logging (no handler) |
| uv | Package manager | Yes | confirmed in use | — |

No missing dependencies. All required packages are already installed in `backend/.venv`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.24+ |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `cd backend && uv run --extra dev pytest tests/ -x -q` |
| Full suite command | `cd backend && uv run --extra dev pytest tests/ --cov=app` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BACK-01 | FastAPI app starts, health route responds | integration | `cd backend && uv run --extra dev pytest tests/test_main.py -x` | No — Wave 0 |
| BACK-02 | DB init creates all tables on fresh start | unit | `cd backend && uv run --extra dev pytest tests/test_db.py::test_init_creates_tables -x` | No — Wave 0 |
| BACK-03 | Default user profile seeded with $10k | unit | `cd backend && uv run --extra dev pytest tests/test_db.py::test_seed_user_profile -x` | No — Wave 0 |
| BACK-04 | Default watchlist has 10 tickers | unit | `cd backend && uv run --extra dev pytest tests/test_db.py::test_seed_watchlist -x` | No — Wave 0 |
| BACK-05 | GET /api/health returns 200 with correct body | integration | `cd backend && uv run --extra dev pytest tests/test_main.py::test_health -x` | No — Wave 0 |
| BACK-06 | Market data source starts/stops via lifespan | integration | `cd backend && uv run --extra dev pytest tests/test_main.py::test_market_data_integration -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `cd backend && uv run --extra dev pytest tests/ -x -q`
- **Per wave merge:** `cd backend && uv run --extra dev pytest tests/ --cov=app`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `backend/tests/test_db.py` — covers BACK-02, BACK-03, BACK-04
- [ ] `backend/tests/test_main.py` — covers BACK-01, BACK-05, BACK-06

*(Existing `backend/tests/market/` tests are untouched; new tests go in `backend/tests/` directly.)*

---

## Project Constraints (from CLAUDE.md)

| Directive | Source |
|-----------|--------|
| Use `uv run xxx` never `python3 xxx` | global CLAUDE.md |
| Use `uv add xxx` never `pip install xxx` | global CLAUDE.md |
| Module-level logger: `logger = logging.getLogger(__name__)` | project CLAUDE.md |
| snake_case for all functions and variables | project CLAUDE.md |
| Type hints on all function parameters | project CLAUDE.md |
| `CREATE TABLE IF NOT EXISTS` for idempotent init | CONTEXT.md D-04 |
| No ORM — use stdlib `sqlite3` directly | CONTEXT.md D-03 |
| Single entry point `backend/main.py` | CONTEXT.md D-05 |
| FastAPI lifespan context manager (not `@app.on_event`) | CONTEXT.md D-05 |
| No stub routers for phases 2+; only health in phase 1 | CONTEXT.md D-08 |
| ruff format: `uv run ruff format .` | project CLAUDE.md |
| ruff lint: `uv run ruff check app/ tests/` | project CLAUDE.md |
| Line length 100 chars | project CLAUDE.md |

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` | `FastAPI(lifespan=...)` with `@asynccontextmanager` | FastAPI 0.95 (2023) | Lifespan is the only non-deprecated approach; use it |
| `Optional[str]` type hints | `str \| None` | Python 3.10+ | Project already uses modern syntax; follow it |

---

## Open Questions

1. **DB_PATH env var for tests**
   - What we know: Tests need a temporary/in-memory DB to avoid touching the real `db/finally.db`
   - What's unclear: Whether to use `:memory:` (fast, but no file creation) or a `tmp_path` fixture
   - Recommendation: Use pytest `tmp_path` fixture to set `DB_PATH` env var to a temp file path. This tests file creation behavior (for BACK-02) which `:memory:` skips.

2. **Logging setup with rich**
   - What we know: CONTEXT.md says "use `rich` handler if convenient"; `rich` is installed
   - What's unclear: Whether to configure at module level in `main.py` or via a dedicated `logging_config.py`
   - Recommendation: `logging.basicConfig` in `main.py` is sufficient for Phase 1; rich handler is a nice-to-have, not required.

---

## Sources

### Primary (HIGH confidence)

- Existing codebase — `backend/app/market/` — Public API verified by reading source; confirmed working (73 passing tests)
- Installed packages — verified `fastapi==0.128.7`, `uvicorn==0.40.0`, `sqlite3==3.46.0` by running in venv
- `planning/PLAN.md` §7 — Schema definition (6 tables, seed data, lazy init strategy)
- `planning/MARKET_DATA_SUMMARY.md` — Complete market subsystem API
- `backend/CLAUDE.md` — Usage patterns for PriceCache, create_market_data_source, create_stream_router

### Secondary (MEDIUM confidence)

- FastAPI lifespan pattern — consistent with known FastAPI 0.95+ docs; confirmed not deprecated

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages installed and version-verified
- Architecture: HIGH — patterns derived from existing codebase and confirmed working abstractions
- Pitfalls: HIGH — derived from reading actual source and known FastAPI behavior

**Research date:** 2026-03-30
**Valid until:** 2026-06-30 (stable stack; FastAPI/uvicorn rarely break between minor versions)
