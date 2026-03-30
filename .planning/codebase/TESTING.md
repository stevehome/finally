# Testing

## Framework & Configuration

- **Framework**: pytest 8.3.0+ with pytest-asyncio 0.24.0+
- **Coverage**: pytest-cov 5.0.0+
- **Linting**: ruff 0.7.0+
- **Config**: `backend/pyproject.toml` under `[tool.pytest.ini_options]`
- **Run**: `cd backend && uv run pytest` or `uv run pytest --cov=app`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

## Test Structure

Tests mirror the `app/` directory structure:

```
backend/tests/
├── conftest.py               # Shared fixtures (minimal)
└── market/                   # One subdirectory per app module
    ├── test_cache.py
    ├── test_factory.py
    ├── test_massive.py
    ├── test_models.py
    ├── test_simulator.py
    └── test_simulator_source.py
```

## What Is Tested

### Market Data (73 tests — all passing)

| File | Subject | Key Behaviors |
|------|---------|---------------|
| `test_cache.py` | `PriceCache` | update/get/remove, direction (up/down/flat), version counter, thread safety |
| `test_factory.py` | `create_market_data_source()` | simulator selected when no/empty key, Massive selected when key present |
| `test_massive.py` | `MassiveDataSource` | HTTP response parsing, ticker add/remove, error handling (mocked HTTP) |
| `test_models.py` | Pydantic models | `PriceUpdate` field validation, `MarketDataConfig` defaults |
| `test_simulator.py` | `GBMSimulator` | prices always positive, GBM drift over time, correlation matrix, random events |
| `test_simulator_source.py` | `SimulatorDataSource` | start/stop lifecycle, cache integration, watchlist sync |

## Testing Patterns

### Class-Based Test Organization

```python
class TestPriceCache:
    """Unit tests for the PriceCache."""

    def test_update_and_get(self):
        """Test updating and getting a price."""
        cache = PriceCache()
        update = cache.update("AAPL", 190.50)
        assert update.ticker == "AAPL"
```

### Async Tests (pytest-asyncio auto mode)

```python
class TestSimulatorDataSource:
    async def test_start_stop(self):
        cache = PriceCache()
        source = SimulatorDataSource(cache, ["AAPL"])
        await source.start()
        # ...
        await source.stop()
```

### Mocking External HTTP (unittest.mock)

```python
from unittest.mock import patch, AsyncMock

with patch("app.market.massive_client.httpx.AsyncClient") as mock_client:
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=mock_response
    )
    # test behavior
```

### Environment Variable Mocking

```python
with patch.dict(os.environ, {"MASSIVE_API_KEY": "test-key"}, clear=True):
    source = create_market_data_source(cache)
    assert isinstance(source, MassiveDataSource)
```

### No Shared State Between Tests

Each test creates its own instances — no module-level state, no shared cache.

## What Is NOT Tested Yet

- FastAPI endpoints (not yet implemented)
- Database layer (not yet implemented)
- Portfolio trade execution logic (not yet implemented)
- LLM chat/structured output parsing (not yet implemented)
- Frontend components (not yet implemented)
- E2E Playwright tests (infrastructure present in `test/`, no tests written)

## Coverage Configuration

```toml
[tool.coverage.run]
source = ["app"]
omit = ["tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## Running Tests

```bash
cd backend

# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=app --cov-report=term-missing

# Single file
uv run pytest tests/market/test_cache.py

# Single test
uv run pytest tests/market/test_cache.py::TestPriceCache::test_direction_up

# Lint
uv run ruff check app/ tests/
```
