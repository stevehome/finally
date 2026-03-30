# Directory Structure

## Top-Level Layout

```
finally/
├── backend/                  # FastAPI uv project (Python 3.12+)
│   ├── app/                  # Application source code
│   │   ├── market/           # Market data subsystem (COMPLETE)
│   │   └── routers/          # API route handlers (EMPTY - not yet implemented)
│   ├── tests/                # Pytest test suite
│   │   └── market/           # Market data tests (73 tests, all passing)
│   ├── pyproject.toml        # uv project config + ruff + pytest config
│   ├── uv.lock               # Locked dependency versions
│   ├── market_data_demo.py   # Standalone demo script (Rich terminal output)
│   └── CLAUDE.md             # Backend agent instructions
├── frontend/                 # Next.js TypeScript project (EMPTY - not yet implemented)
├── planning/                 # Agent reference docs
│   ├── PLAN.md               # Full project specification
│   ├── MARKET_DATA_SUMMARY.md # Completed market data summary
│   └── archive/              # Detailed design docs for completed work
├── test/                     # E2E Playwright tests (node_modules present, no tests yet)
├── .planning/                # GSD workflow artifacts
│   └── codebase/             # This codebase map
├── .env                      # Environment variables (gitignored)
├── .gitignore
├── CLAUDE.md                 # Top-level project instructions
└── README.md
```

## Backend App Structure (`backend/app/`)

```
app/
├── __init__.py
├── market/                   # Market data subsystem (COMPLETE)
│   ├── __init__.py
│   ├── interface.py          # Abstract base class MarketDataSource
│   ├── models.py             # Pydantic models: PriceUpdate, MarketDataConfig
│   ├── cache.py              # PriceCache — thread-safe in-memory price store
│   ├── simulator.py          # GBM-based price simulator (MarketDataSource impl)
│   ├── massive_client.py     # Massive/Polygon.io REST client (MarketDataSource impl)
│   ├── factory.py            # create_market_data_source() factory function
│   ├── seed_prices.py        # Realistic seed prices for 10 default tickers
│   └── stream.py             # SSE streaming logic (reads from PriceCache)
└── routers/                  # API route handlers (EMPTY — to be implemented)
    └── __pycache__/
```

## Backend Tests Structure (`backend/tests/`)

```
tests/
├── __init__.py
├── conftest.py               # Shared fixtures (minimal — event loop policy)
└── market/                   # Market data tests
    ├── __init__.py
    ├── test_cache.py         # PriceCache unit tests
    ├── test_factory.py       # Factory function tests
    ├── test_massive.py       # MassiveClient tests (mocked HTTP)
    ├── test_models.py        # Pydantic model validation tests
    ├── test_simulator.py     # Simulator math/behavior tests
    └── test_simulator_source.py  # SimulatorSource lifecycle tests
```

## Key File Locations

| Purpose | Path |
|---------|------|
| Market data interface | `backend/app/market/interface.py` |
| Price cache | `backend/app/market/cache.py` |
| Simulator | `backend/app/market/simulator.py` |
| Massive API client | `backend/app/market/massive_client.py` |
| Source factory | `backend/app/market/factory.py` |
| SSE stream | `backend/app/market/stream.py` |
| Seed prices | `backend/app/market/seed_prices.py` |
| Data models | `backend/app/market/models.py` |
| Backend config | `backend/pyproject.toml` |
| Project spec | `planning/PLAN.md` |

## What Is Missing (Not Yet Implemented)

- `backend/app/main.py` — FastAPI application entrypoint
- `backend/app/database.py` — SQLite initialization and schema
- `backend/app/routers/portfolio.py` — Portfolio, trade endpoints
- `backend/app/routers/watchlist.py` — Watchlist CRUD endpoints
- `backend/app/routers/chat.py` — LLM chat endpoint
- `frontend/` — Entire Next.js application
- `Dockerfile` — Multi-stage container build
- `docker-compose.yml` — Convenience wrapper
- `scripts/` — Start/stop scripts
- `test/` — Playwright E2E tests (infrastructure present, no tests written)

## Naming Conventions

- **Python files**: `snake_case.py`
- **Python classes**: `PascalCase` (e.g., `PriceCache`, `MarketDataSource`)
- **Python functions/variables**: `snake_case`
- **Test files**: `test_<module>.py` in mirror directory structure
- **Test classes**: `Test<Subject>` (e.g., `TestPriceCache`)
- **Test functions**: `test_<behavior>` (descriptive behavior names)
