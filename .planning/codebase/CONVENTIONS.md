# Coding Conventions

**Analysis Date:** 2026-03-30

## Naming Patterns

**Files:**
- `snake_case.py` for module files: `models.py`, `cache.py`, `interface.py`, `factory.py`
- `test_*.py` for test files: `test_simulator.py`, `test_cache.py`, `test_factory.py`

**Functions:**
- `snake_case` for all functions: `create_market_data_source()`, `get_price()`, `update()`
- Async functions prefix with understanding from context: `async def start()`, `async def stop()`, `async def _run_loop()`
- Private/internal functions prefixed with underscore: `_add_ticker_internal()`, `_rebuild_cholesky()`, `_generate_events()`, `_poll_once()`, `_poll_loop()`

**Variables:**
- `snake_case` for all variable names: `price_cache`, `api_key`, `ticker_params`, `previous_price`
- Class attributes prefixed with underscore: `self._prices`, `self._cache`, `self._interval`, `self._task`
- Constants in `UPPER_SNAKE_CASE`: `SEED_PRICES`, `TICKER_PARAMS`, `DEFAULT_PARAMS`, `INTRA_TECH_CORR`, `TRADING_SECONDS_PER_YEAR`

**Types:**
- Classes in `PascalCase`: `PriceUpdate`, `PriceCache`, `MarketDataSource`, `GBMSimulator`, `SimulatorDataSource`, `MassiveDataSource`
- Type hints using modern Python 3.12 syntax: `dict[str, float]`, `list[str]`, `float | None`, not `Optional[float]` or `Dict`

## Code Style

**Formatting:**
- Tool: ruff (both linter and formatter)
- Line length: 100 characters (see `pyproject.toml` line 39)
- Format command: `uv run ruff format .`

**Linting:**
- Tool: ruff with config in `pyproject.toml`
- Rules enabled: `E` (pycodestyle), `F` (Pyflakes), `I` (isort), `N` (pep8-naming), `W` (pycodestyle warnings)
- Rules ignored: `E501` (line too long - handled by formatter)
- Lint command: `uv run ruff check app/ tests/`
- Config location: `/Users/steve/projects/finally/backend/pyproject.toml` lines 38-44

## Import Organization

**Order (as seen in actual code):**
1. Standard library imports: `asyncio`, `json`, `logging`, `math`, `random`, `os`, `time`, `dataclasses`
2. Third-party imports: `numpy`, `fastapi`, `massive`
3. Relative imports from this package: `from .cache import`, `from .interface import`, `from .models import`

**Example (from `simulator.py`):**
```python
from __future__ import annotations

import asyncio
import logging
import math
import random

import numpy as np

from .cache import PriceCache
from .interface import MarketDataSource
from .seed_prices import SEED_PRICES, TICKER_PARAMS
```

**Path Aliases:**
- No path aliases configured; all imports are explicit relative or absolute
- Module imports use full paths: `from app.market.cache import PriceCache`

## Error Handling

**Patterns:**
- Catch specific exceptions, not bare `except:`. Examples:
  - `except AttributeError, TypeError:` for missing attributes (line 110 in `massive_client.py`)
  - `except asyncio.CancelledError:` for async task cancellation (line 236 in `simulator.py`)
  - `except Exception:` only when intentionally catching all and logging (line 118 in `massive_client.py`, line 268 in `simulator.py`)
- Log exceptions using `logger.exception()` when catching, not printing stack traces
- Don't re-raise caught exceptions if the system can recover; instead log and continue (see `massive_client.py` line 119-121: "Don't re-raise — the loop will retry")
- For async tasks, handle cancellation gracefully without logging exceptions

**Example from `stream.py` (lines 86-87):**
```python
except asyncio.CancelledError:
    logger.info("SSE stream cancelled for: %s", client_ip)
```

**Example from `massive_client.py` (lines 118-121):**
```python
except Exception as e:
    logger.error("Massive poll failed: %s", e)
    # Don't re-raise — the loop will retry on the next interval.
```

## Logging

**Framework:** Standard `logging` module from Python stdlib

**Pattern:**
- Module-level logger: `logger = logging.getLogger(__name__)` at top of file (see all Python files)
- Log levels used:
  - `logger.info()` for startup/shutdown events: `"Simulator started with %d tickers"` (line 230 in `simulator.py`)
  - `logger.debug()` for detailed flow: `"Random event on %s: %.1f%% %s"` (line 109-113 in `simulator.py`)
  - `logger.warning()` for recoverable errors: `"Skipping snapshot for %s: %s"` (line 111 in `massive_client.py`)
  - `logger.error()` for unrecoverable errors: `"Massive poll failed: %s"` (line 119 in `massive_client.py`)

**When to Log:**
- Log on component lifecycle: start/stop of services
- Log on errors with context
- Log in main event loops (debug level) for performance tracing
- Do NOT log every single function call or assignment

## Comments

**When to Comment:**
- Explain the "why", not the "what" — code is self-documenting through good names
- Comment non-obvious algorithms or mathematical operations. Example: `simulator.py` lines 31-42 explain the GBM formula
- Comment configuration and constants: `seed_prices.py` explains volatility and drift
- Mark sections of code with `# --- Public API ---` or `# --- Internals ---` for readability

**JSDoc/TSDoc (Python docstrings):**
- Use module docstrings at the top of every `.py` file (3 lines): `"""Brief description of module purpose."""`
- Use class docstrings immediately after class definition with full description of purpose and lifecycle
- Use function/method docstrings for all public methods; optional for internal/private functions
- Style: Google-style docstrings (simple format, no `Args:` sections unless needed)

**Examples:**

Module docstring (from `models.py`, line 1):
```python
"""Data models for market data."""
```

Class docstring (from `PriceCache`, lines 11-16):
```python
class PriceCache:
    """Thread-safe in-memory cache of the latest price for each ticker.

    Writers: SimulatorDataSource or MassiveDataSource (one at a time).
    Readers: SSE streaming endpoint, portfolio valuation, trade execution.
    """
```

Method docstring (from `PriceUpdate.change`, lines 18-20):
```python
@property
def change(self) -> float:
    """Absolute price change from previous update."""
    return round(self.price - self.previous_price, 4)
```

Lifecycle docstring (from `MarketDataSource`, lines 15-23):
```python
class MarketDataSource(ABC):
    """Contract for market data providers.

    ...

    Lifecycle:
        source = create_market_data_source(cache)
        await source.start(["AAPL", "GOOGL", ...])
        # ... app runs ...
        await source.add_ticker("TSLA")
        ...
    """
```

## Function Design

**Size:** Functions are kept short and focused. Most functions 10-30 lines. Longest is `_rebuild_cholesky()` at ~20 lines (complex math).

**Parameters:**
- Use type hints on all parameters: `def update(self, ticker: str, price: float, timestamp: float | None = None) -> PriceUpdate:`
- Use keyword-only arguments when a function has many parameters; use `*` separator if needed
- Default parameters are explicit and clear: `timestamp: float | None = None`

**Return Values:**
- All functions have explicit return type hints: `-> PriceUpdate`, `-> dict[str, float]`, `-> None`
- Return early if possible (guard clauses). Example from `simulator.py` line 80-81:
```python
n = len(self._tickers)
if n == 0:
    return {}
```
- Never use implicit `return None` in functions that return nothing; be explicit or use `-> None`

## Module Design

**Exports:**
- Use `__all__` in `__init__.py` files to explicitly declare public API. Example from `market/__init__.py`:
```python
__all__ = [
    "PriceUpdate",
    "PriceCache",
    "MarketDataSource",
    "create_market_data_source",
    "create_stream_router",
]
```

**Barrel Files:**
- Module `__init__.py` re-exports core types for simpler imports
- Users import from package: `from app.market import PriceCache` not `from app.market.cache import PriceCache`
- Encourages encapsulation; implementation can change without breaking imports

**Public vs Private:**
- Public: Classes, functions, and constants in `__all__`
- Private: Functions/attributes prefixed with `_` are internal; not re-exported
- Example: `_add_ticker_internal()` is private, used only within `GBMSimulator`

## Abstract Interfaces

**Pattern:**
- Use `ABC` (Abstract Base Class) from `abc` module for defining contracts
- Location: `app/market/interface.py`
- Example: `MarketDataSource` defines lifecycle (`start()`, `stop()`, `add_ticker()`, `remove_ticker()`, `get_tickers()`)
- Implementations provide concrete behavior: `SimulatorDataSource` and `MassiveDataSource` both inherit and implement all abstract methods
- Downstream code depends on the interface, not the implementation (enabled by factory pattern)

## Dataclasses

**Pattern:**
- Use `@dataclass` for simple data containers with no complex logic
- Example: `PriceUpdate` (line 9 in `models.py`) is a dataclass with immutability via `frozen=True` and `slots=True`
- Properties on dataclasses for computed values: `change`, `change_percent`, `direction`, `to_dict()`
- Never modify frozen dataclass fields; they're immutable by design

## Async Patterns

**Pattern:**
- Use `async def` for functions that need to be awaited or call other async functions
- Background tasks created with `asyncio.create_task()` (line 229 in `simulator.py`)
- Task cancellation via `task.cancel()` and catching `asyncio.CancelledError` (lines 234-237 in `simulator.py`)
- Sleep in event loops with `await asyncio.sleep()` not `time.sleep()`
- Run blocking code in threads: `await asyncio.to_thread(blocking_func)` (line 97 in `massive_client.py`)

## Testing Integration

**Pattern:**
- Mark async test methods with `@pytest.mark.asyncio` (see `test_simulator_source.py`)
- Fixtures defined in `conftest.py` for reuse (minimal fixtures in this codebase)
- Import directly from module under test: `from app.market.cache import PriceCache`

---

*Convention analysis: 2026-03-30*
