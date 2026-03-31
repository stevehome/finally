---
status: complete
phase: 02-portfolio-watchlist-api
source: [02-02-SUMMARY.md, 02-03-SUMMARY.md]
started: 2026-03-31T07:20:00Z
updated: 2026-03-31T09:30:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Kill any running server. From the backend/ directory, start the app fresh with `uv run uvicorn main:app --reload`. Server boots without errors, DB initializes with seed data, and GET http://localhost:8000/api/health returns {"status": "ok"}.
result: pass

### 2. Get Portfolio State
expected: GET http://localhost:8000/api/portfolio returns JSON with cash_balance (~10000.0), positions (empty list on fresh start), and total_value (~10000.0).
result: pass

### 3. Buy Shares
expected: POST http://localhost:8000/api/portfolio/trade with body {"ticker": "AAPL", "side": "buy", "quantity": 5} returns 200 with the executed trade details. A subsequent GET /api/portfolio shows cash_balance decreased and a position for AAPL appears with quantity 5.
result: pass

### 4. Sell Shares
expected: POST /api/portfolio/trade with {"ticker": "AAPL", "side": "sell", "quantity": 2} returns 200. GET /api/portfolio shows AAPL position quantity reduced to 3.
result: pass

### 5. Trade Validation — Insufficient Cash
expected: POST /api/portfolio/trade with {"ticker": "NVDA", "side": "buy", "quantity": 100000} (far more than cash allows) returns HTTP 400 with an error message about insufficient cash.
result: pass

### 6. Trade Validation — Insufficient Shares
expected: POST /api/portfolio/trade with {"ticker": "AAPL", "side": "sell", "quantity": 9999} (more than owned) returns HTTP 400 with an error about insufficient shares.
result: pass

### 7. Portfolio History
expected: GET http://localhost:8000/api/portfolio/history returns a list of portfolio snapshot objects, each with a total_value and recorded_at timestamp. Should have at least one entry (recorded after the trades above).
result: pass

### 8. Get Watchlist
expected: GET http://localhost:8000/api/watchlist returns a list of 10 default tickers (AAPL, GOOGL, MSFT, AMZN, TSLA, NVDA, META, JPM, V, NFLX), each with a ticker field and a price (may be null if simulator hasn't seeded yet, or a number).
result: pass

### 9. Add Ticker to Watchlist
expected: POST http://localhost:8000/api/watchlist with {"ticker": "AMD"} returns 200/201. A subsequent GET /api/watchlist shows AMD in the list.
result: pass

### 10. Add Duplicate Ticker (Idempotent)
expected: POST /api/watchlist with {"ticker": "AMD"} a second time returns 200 (not 500 or 400). Watchlist still shows AMD exactly once.
result: pass

### 11. Remove Ticker from Watchlist
expected: DELETE http://localhost:8000/api/watchlist/AMD returns 200. GET /api/watchlist no longer includes AMD.
result: pass

### 12. Remove Non-Existent Ticker
expected: DELETE http://localhost:8000/api/watchlist/FAKEXYZ returns HTTP 404.
result: pass

## Summary

total: 12
passed: 12
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
