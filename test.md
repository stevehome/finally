# Code Review — FinAlly Market Data Subsystem

**Scope:** `backend/app/market/` — simulator, cache, and SSE streaming

---

## Overall Assessment

The market data subsystem is well-structured and production-quality. The GBM simulator, thread-safe price cache, and SSE streaming layer are cleanly separated with clear responsibilities. Code is well-documented and follows Python best practices.

---

## Strengths

- **Good abstraction**: `MarketDataSource` interface cleanly decouples the simulator from the SSE layer, making it easy to swap in the `MassiveDataSource` without touching downstream code.
- **Thread safety**: `PriceCache` correctly uses a `threading.Lock` to protect all reads and writes, preventing race conditions between the simulator background task and SSE readers.
- **GBM math is correct**: The drift/diffusion formula in `simulator.py:98-101` matches the standard GBM discrete approximation. The `dt` constant (`~8.48e-8`) is correctly derived from real trading calendar seconds.
- **Correlated moves**: Cholesky decomposition of the correlation matrix (`simulator.py:172`) is the right approach for generating correlated normal draws — statistically sound.
- **SSE implementation**: Version-based change detection (`stream.py:75-76`) avoids redundant sends when prices haven't changed. The `retry: 1000` directive and disconnect check are good production touches.

---

## Issues & Suggestions

### 1. `_rebuild_cholesky` can raise on non-positive-definite matrices
**File:** `simulator.py:172`

`np.linalg.cholesky(corr)` will throw `LinAlgError` if the correlation matrix is not positive definite. This can happen if a user adds a custom ticker with a correlation config that produces a near-singular matrix. The exception is not caught, and would crash the simulator task.

**Suggestion:** Wrap in a try/except and fall back to the identity matrix (no correlation) with a warning log.

---

### 2. Version counter races in SSE
**File:** `stream.py:75-76`, `cache.py:41`

`price_cache.version` is read outside the lock in the SSE generator. While the property itself is an integer read (atomic on CPython), the pattern of reading version then calling `get_all()` is not atomic — a price update can occur between the two calls, causing the SSE generator to send a snapshot that doesn't match the version it observed.

**Suggestion:** Add a `get_all_with_version()` method to `PriceCache` that returns both atomically under the lock.

---

### 3. Bare `except Exception` swallows errors silently
**File:** `simulator.py:268`

```python
except Exception:
    logger.exception("Simulator step failed")
```

This is fine for resilience, but if `step()` fails repeatedly (e.g., due to a numpy issue), the loop continues producing no prices and the user sees stale data. There's no circuit-breaker or max-failure counter.

**Suggestion:** Add a consecutive-failure counter; stop the loop and emit a clear error after N failures.

---

### 4. `PriceCache.version` is not thread-safe on all interpreters
**File:** `cache.py:41`

`self._version += 1` is inside the lock — good. However, the property `version` reads `self._version` outside the lock (`cache.py:66`). On CPython this is safe due to the GIL, but it's not a documented guarantee and would fail on non-CPython runtimes.

**Suggestion:** Acquire the lock in the `version` property getter for correctness across all runtimes.

---

### 5. Minor: `create_stream_router` mutates a module-level `router`
**File:** `stream.py:17, 26`

The `router` is defined at module scope and then decorated inside `create_stream_router`. Calling `create_stream_router` twice would register the route twice on the same router object, which FastAPI silently allows but can cause duplicate route warnings.

**Suggestion:** Move `router = APIRouter(...)` inside the factory function so each call gets a fresh instance.

---

## Summary

| Area | Rating |
|---|---|
| Architecture | Excellent |
| GBM implementation | Excellent |
| Thread safety | Good (minor gap noted) |
| Error handling | Adequate (improvement opportunity) |
| SSE streaming | Good |
