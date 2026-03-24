# Code Review: FinAlly Market Data Module

**Scope:** `backend/app/market/` — GBM simulator, price cache, and SSE streaming

---

## Overall Assessment

The market data module is well-structured with clean separation of concerns. The interface-based design (`MarketDataSource` abstract class) makes swapping between the simulator and real API transparent to the rest of the system. Code quality is high overall.

---

## Strengths

- **GBM math is correct** (`simulator.py:98-101`): The drift and diffusion terms are properly computed using the Itô correction (`mu - 0.5*sigma²`), avoiding a common mistake of omitting the variance adjustment.
- **Cholesky correlation** (`simulator.py:172`): Correlated moves via Cholesky decomposition is the right approach for realistic multi-asset simulation.
- **Thread-safe cache** (`cache.py:29`): `Lock` is used consistently around all read and write operations in `PriceCache`.
- **SSE change detection** (`stream.py:76`): The `version` counter avoids redundant pushes when no prices have changed — efficient.

---

## Issues

### Minor

1. **Silent catch-all in simulator loop** (`simulator.py:268`): `except Exception` swallows all errors with only a log. A repeated failure (e.g., numpy issue) will silently spin forever. Consider a backoff or a maximum consecutive failure count before raising.

2. **`request.client` can be `None`** (`stream.py:65`): `client_ip` is correctly guarded, but the pattern `request.client.host if request.client else "unknown"` repeats across the codebase — worth extracting to a small helper.

3. **`version` property not locked** (`cache.py:65-66`): The `version` property reads `self._version` without acquiring `self._lock`. On CPython this is safe due to the GIL, but it's inconsistent with the rest of the class and could be a footgun if the implementation ever changes.

---

## Suggestions

- **Add a heartbeat to the SSE stream**: If no price changes occur for several seconds (e.g., market closed), the SSE connection may appear stalled to proxies or load balancers. Sending a periodic `: keepalive` comment line would prevent premature disconnects.
- **Consider a `dt` override for tests**: `GBMSimulator.DEFAULT_DT` is computed at class-definition time from constants. Passing `dt` in tests is already supported, which is good — just ensure tests don't accidentally use the production dt.

---

## Summary

Solid implementation. The two actionable items are the unguarded `version` read in `PriceCache` and the infinite retry on simulator failure. Both are low-risk in the current single-user context but worth addressing before production hardening.
