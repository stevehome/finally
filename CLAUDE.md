# FinAlly Project - the Finance Ally

All project documentation is in the `planning` directory.

The key document is PLAN.md included in full below; the market data component has been completed and is summarized in the file `planning/MARKET_DATA_SUMMARY.md` with more details in the `planning/archive` folder. Consult these docs only when required. The remainder of the platform is still to be developed.

@planning/PLAN.md

<!-- GSD:project-start source:PROJECT.md -->
## Project

**FinAlly — AI Trading Workstation**

FinAlly is a visually stunning, single-container AI-powered trading workstation that streams live market data, lets users trade a simulated $10k portfolio, and integrates an LLM chat assistant that can analyze positions and execute trades on the user's behalf. It is a capstone project for an agentic AI coding course, built entirely by coding agents, and runs via a single Docker command with no login required.

**Core Value:** A Bloomberg-terminal-aesthetic trading workstation where users watch live prices stream, trade a simulated portfolio, and converse with an AI that can execute trades on their behalf — all from one browser tab, zero setup.

### Constraints

- **Tech Stack**: FastAPI + uv, Next.js static export, SQLite, Docker single container — architecture is fixed per spec
- **Python tooling**: Always `uv run` / `uv add`, never `python3` / `pip install`
- **Single port**: Everything served on port 8000 — no CORS, no separate dev servers in production
- **LLM provider**: LiteLLM → OpenRouter → Cerebras (`openrouter/openai/gpt-oss-120b`) — structured outputs required
- **Market orders only**: No limit orders, no partial fills, instant execution at current price
- **No auth**: Single user "default", no login/signup
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.12 - Backend API, market data simulation, LLM integration
- TypeScript - Frontend application (Next.js, not yet developed)
- SQL - SQLite database schema
- JavaScript/Node.js - Frontend build tooling (Next.js)
- Bash/PowerShell - Deployment scripts
## Runtime
- Python 3.12 runtime (backend via Docker)
- Node 20 (frontend build via Docker multi-stage)
- `uv` - Python package manager for backend (`backend/pyproject.toml`)
- npm - Node package manager for frontend (configured but not yet populated)
- `backend/uv.lock` - Python dependency pinning
- Frontend: `package-lock.json` expected (not yet created)
## Frameworks
- FastAPI 0.115+ - REST API and server framework, Python backend
- Next.js - Frontend framework (static export configured per plan)
- Uvicorn 0.32+ - ASGI application server, runs FastAPI
- pytest 8.3+ - Python unit testing
- pytest-asyncio 0.24+ - Async test support
- pytest-cov 5.0+ - Code coverage reporting
- Playwright - E2E testing (configured, tests in `test/` directory)
- Ruff 0.7+ - Python linting and code formatting
- Hatchling - Python package builder
## Key Dependencies
- `fastapi>=0.115.0` - API framework, request handling, SSE streaming support
- `uvicorn[standard]>=0.32.0` - ASGI server with WebSocket/SSE support
- `numpy>=2.0.0` - Numeric computation for GBM market simulator
- `massive>=1.0.0` - Polygon.io market data SDK (optional integration)
- `rich>=13.0.0` - Terminal UI utilities and logging enhancements
- Standard library: `sqlite3` (for SQLite database)
- Standard library: `asyncio` (async task management for streaming)
- Standard library: `dataclasses` (model definitions)
## Configuration
- `.env` file (gitignored) - Runtime configuration
- Environment variables control data source selection and LLM integration
- `Dockerfile` (multi-stage)
- `docker-compose.yml` - Optional convenience wrapper
- `pyproject.toml` - Backend Python project configuration, dependencies, tool settings
## Platform Requirements
- Python 3.12+
- Docker (for containerized development and deployment)
- Node 20+ (for frontend builds)
- uv package manager
- Git
- Docker container deployment (single port 8000)
- Volume mount for SQLite persistence: `db/` directory
- Network access to OpenRouter API (LLM) if OPENROUTER_API_KEY provided
- Network access to Massive API (optional, if MASSIVE_API_KEY provided)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- `snake_case.py` for module files: `models.py`, `cache.py`, `interface.py`, `factory.py`
- `test_*.py` for test files: `test_simulator.py`, `test_cache.py`, `test_factory.py`
- `snake_case` for all functions: `create_market_data_source()`, `get_price()`, `update()`
- Async functions prefix with understanding from context: `async def start()`, `async def stop()`, `async def _run_loop()`
- Private/internal functions prefixed with underscore: `_add_ticker_internal()`, `_rebuild_cholesky()`, `_generate_events()`, `_poll_once()`, `_poll_loop()`
- `snake_case` for all variable names: `price_cache`, `api_key`, `ticker_params`, `previous_price`
- Class attributes prefixed with underscore: `self._prices`, `self._cache`, `self._interval`, `self._task`
- Constants in `UPPER_SNAKE_CASE`: `SEED_PRICES`, `TICKER_PARAMS`, `DEFAULT_PARAMS`, `INTRA_TECH_CORR`, `TRADING_SECONDS_PER_YEAR`
- Classes in `PascalCase`: `PriceUpdate`, `PriceCache`, `MarketDataSource`, `GBMSimulator`, `SimulatorDataSource`, `MassiveDataSource`
- Type hints using modern Python 3.12 syntax: `dict[str, float]`, `list[str]`, `float | None`, not `Optional[float]` or `Dict`
## Code Style
- Tool: ruff (both linter and formatter)
- Line length: 100 characters (see `pyproject.toml` line 39)
- Format command: `uv run ruff format .`
- Tool: ruff with config in `pyproject.toml`
- Rules enabled: `E` (pycodestyle), `F` (Pyflakes), `I` (isort), `N` (pep8-naming), `W` (pycodestyle warnings)
- Rules ignored: `E501` (line too long - handled by formatter)
- Lint command: `uv run ruff check app/ tests/`
- Config location: `/Users/steve/projects/finally/backend/pyproject.toml` lines 38-44
## Import Organization
- No path aliases configured; all imports are explicit relative or absolute
- Module imports use full paths: `from app.market.cache import PriceCache`
## Error Handling
- Catch specific exceptions, not bare `except:`. Examples:
- Log exceptions using `logger.exception()` when catching, not printing stack traces
- Don't re-raise caught exceptions if the system can recover; instead log and continue (see `massive_client.py` line 119-121: "Don't re-raise — the loop will retry")
- For async tasks, handle cancellation gracefully without logging exceptions
## Logging
- Module-level logger: `logger = logging.getLogger(__name__)` at top of file (see all Python files)
- Log levels used:
- Log on component lifecycle: start/stop of services
- Log on errors with context
- Log in main event loops (debug level) for performance tracing
- Do NOT log every single function call or assignment
## Comments
- Explain the "why", not the "what" — code is self-documenting through good names
- Comment non-obvious algorithms or mathematical operations. Example: `simulator.py` lines 31-42 explain the GBM formula
- Comment configuration and constants: `seed_prices.py` explains volatility and drift
- Mark sections of code with `# --- Public API ---` or `# --- Internals ---` for readability
- Use module docstrings at the top of every `.py` file (3 lines): `"""Brief description of module purpose."""`
- Use class docstrings immediately after class definition with full description of purpose and lifecycle
- Use function/method docstrings for all public methods; optional for internal/private functions
- Style: Google-style docstrings (simple format, no `Args:` sections unless needed)
## Function Design
- Use type hints on all parameters: `def update(self, ticker: str, price: float, timestamp: float | None = None) -> PriceUpdate:`
- Use keyword-only arguments when a function has many parameters; use `*` separator if needed
- Default parameters are explicit and clear: `timestamp: float | None = None`
- All functions have explicit return type hints: `-> PriceUpdate`, `-> dict[str, float]`, `-> None`
- Return early if possible (guard clauses). Example from `simulator.py` line 80-81:
- Never use implicit `return None` in functions that return nothing; be explicit or use `-> None`
## Module Design
- Use `__all__` in `__init__.py` files to explicitly declare public API. Example from `market/__init__.py`:
- Module `__init__.py` re-exports core types for simpler imports
- Users import from package: `from app.market import PriceCache` not `from app.market.cache import PriceCache`
- Encourages encapsulation; implementation can change without breaking imports
- Public: Classes, functions, and constants in `__all__`
- Private: Functions/attributes prefixed with `_` are internal; not re-exported
- Example: `_add_ticker_internal()` is private, used only within `GBMSimulator`
## Abstract Interfaces
- Use `ABC` (Abstract Base Class) from `abc` module for defining contracts
- Location: `app/market/interface.py`
- Example: `MarketDataSource` defines lifecycle (`start()`, `stop()`, `add_ticker()`, `remove_ticker()`, `get_tickers()`)
- Implementations provide concrete behavior: `SimulatorDataSource` and `MassiveDataSource` both inherit and implement all abstract methods
- Downstream code depends on the interface, not the implementation (enabled by factory pattern)
## Dataclasses
- Use `@dataclass` for simple data containers with no complex logic
- Example: `PriceUpdate` (line 9 in `models.py`) is a dataclass with immutability via `frozen=True` and `slots=True`
- Properties on dataclasses for computed values: `change`, `change_percent`, `direction`, `to_dict()`
- Never modify frozen dataclass fields; they're immutable by design
## Async Patterns
- Use `async def` for functions that need to be awaited or call other async functions
- Background tasks created with `asyncio.create_task()` (line 229 in `simulator.py`)
- Task cancellation via `task.cancel()` and catching `asyncio.CancelledError` (lines 234-237 in `simulator.py`)
- Sleep in event loops with `await asyncio.sleep()` not `time.sleep()`
- Run blocking code in threads: `await asyncio.to_thread(blocking_func)` (line 97 in `massive_client.py`)
## Testing Integration
- Mark async test methods with `@pytest.mark.asyncio` (see `test_simulator_source.py`)
- Fixtures defined in `conftest.py` for reuse (minimal fixtures in this codebase)
- Import directly from module under test: `from app.market.cache import PriceCache`
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Abstraction-driven market data layer supporting multiple implementations (simulator, Massive API)
- Thread-safe shared cache pattern for price data
- Async/await throughout for I/O and background tasks
- Factory pattern for environment-driven selection of market data source
- Stateless API endpoints that read/write to shared cache
## Layers
- Purpose: Unified interface for price data acquisition and streaming
- Location: `backend/app/market/`
- Contains: Abstract interface, implementations (simulator, Massive client), price cache, SSE streaming endpoint
- Depends on: numpy (GBM math), Massive SDK (optional), threading (thread-safe cache)
- Used by: FastAPI routers, portfolio engine (forthcoming), SSE streaming
- Purpose: HTTP endpoints for clients (portfolio operations, watchlist management, chat, health checks)
- Location: `backend/app/routers/` (not yet populated; placeholder)
- Contains: FastAPI route handlers
- Depends on: Market data layer (price cache), database layer (forthcoming)
- Used by: Frontend clients via REST/SSE
- Purpose: Persistent storage for user profiles, positions, trades, watchlist, chat history
- Location: `backend/db/` (schema definitions, seed logic; not yet implemented)
- Contains: SQLite schema, migration logic, seed data
- Depends on: None
- Used by: Portfolio engine, trade execution, watchlist management
- Purpose: Single-page web application for user interaction
- Location: `frontend/` (not yet implemented; Next.js TypeScript)
- Contains: React components, charts, real-time price display, portfolio visualizations, chat interface
- Depends on: SSE streaming, REST API endpoints
- Used by: End users via browser
## Data Flow
- All state centralized in SQLite database (persisted across sessions)
- In-memory price cache is transient (rebuilt on app restart from latest market data)
- Portfolio snapshots recorded every 30 seconds + immediately after trades for P&L charting
## Key Abstractions
- Purpose: Pluggable interface for price data acquisition
- Examples: `backend/app/market/simulator.py`, `backend/app/market/massive_client.py`
- Pattern: Abstract base class with lifecycle methods (`start`, `stop`, `add_ticker`, `remove_ticker`, `get_tickers`); implementations run background tasks that write to shared PriceCache
- Purpose: Atomic snapshot of a single ticker's price at a point in time
- Examples: `backend/app/market/models.py`
- Pattern: Frozen dataclass with computed properties (change, change_percent, direction); includes `to_dict()` for JSON serialization
- Purpose: Central in-memory store of latest prices, indexed by ticker
- Examples: `backend/app/market/cache.py`
- Pattern: Locking wrapper around dictionary; version counter bumped on every write for efficient SSE change detection
## Entry Points
- Location: `backend/main.py` (not yet created)
- Triggers: Container startup, Docker ENTRYPOINT
- Responsibilities: Initialize FastAPI app, create PriceCache, create MarketDataSource via factory, start market data source background task, attach SSE router, attach other API routers, start uvicorn server on port 8000
- Location: `backend/app/market/stream.py::stream_prices()`
- Triggers: Client opens EventSource to `GET /api/stream/prices`
- Responsibilities: Open long-lived connection, monitor cache version, yield SSE-formatted price events every ~500ms, detect client disconnect
- Location: `backend/app/market/simulator.py::SimulatorDataSource._sim_loop()` (internal async task)
- Triggers: `source.start()` called at app initialization
- Responsibilities: Every ~500ms, call GBMSimulator.step() for all active tickers, write prices to PriceCache
- Location: `backend/app/market/massive_client.py::MassiveDataSource._poll_loop()` (internal async task)
- Triggers: `source.start()` called at app initialization
- Responsibilities: Every N seconds (15s default for free tier), call Massive REST API, parse snapshot response, write prices to PriceCache
## Error Handling
- Market data source failures are logged but do not crash the app; last known prices remain available
- SSE client disconnection is expected and handled silently (EventSource built-in retry)
- GBM simulator prices are guaranteed positive (never approach zero due to exponential formulation)
- Massive API parsing errors logged; failed poll does not block next cycle
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
