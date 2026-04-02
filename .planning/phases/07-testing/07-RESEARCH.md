# Phase 7: Testing — Research

## Summary

The backend already has substantial unit test coverage from Phases 1–3. The focus of Phase 7 is:
1. Identifying and filling any remaining backend unit test gaps (TEST-01)
2. Creating the Playwright E2E suite from scratch (TEST-02 through TEST-05)
3. Wiring everything into a `docker-compose.test.yml` (TEST-06)

**Key finding:** `test/node_modules/` contains `playwright` and `playwright-core` but has no `package.json`, no `playwright.config.ts`, and zero test spec files. The directory is a blank slate beyond the installed packages.

---

## Existing Test Coverage

### What exists

**`backend/tests/` — 6 test modules, all passing**

| File | What is tested |
|---|---|
| `tests/market/test_simulator.py` | GBM price generation, positivity invariant |
| `tests/market/test_cache.py` | PriceCache thread-safe read/write |
| `tests/market/test_factory.py` | Source factory env-var selection |
| `tests/market/test_massive.py` | Massive API response parsing |
| `tests/market/test_simulator_source.py` | SimulatorDataSource lifecycle (async) |
| `tests/market/test_models.py` | PriceUpdate dataclass properties |
| `tests/test_db.py` | Schema init, idempotency, seed data (user profile + 10 watchlist tickers) |
| `tests/test_main.py` | Health endpoint, app startup, lifespan, SSE route registration |
| `tests/test_portfolio.py` | Buy (happy), sell (happy), buy with insufficient cash (400), sell with insufficient shares (400), trade history recorded, snapshot after trade, snapshot background task, portfolio history endpoint |
| `tests/test_watchlist.py` | GET watchlist (10 items), add ticker (201), remove ticker (200), streaming hook on add/remove |
| `tests/test_chat.py` | 7 tests: returns message, portfolio context in LLM call, auto-execute trade, apply watchlist change, history persisted, mock mode (no litellm call), failed trade reported in body (not 400) |

**`conftest.py`:** `tmp_db` autouse fixture redirects `DB_PATH` to a temp file — every test is isolated from the real DB.

### Gaps for TEST-01

After reading the source code, the following cases are **not yet covered**:

**Trade logic (`execute_trade_internal` in `portfolio.py`):**
- Sell exactly all shares — position row should be deleted (not set to 0), then `GET /api/portfolio` shows empty positions
- Buy ticker with no price in cache yet (falls back to `avg_cost=0.0` when position is None) — this path exists in the code but is untested
- Invalid `side` value (e.g., `"hold"`) returns 400 with a meaningful detail string
- Fractional share buy/sell (e.g., quantity=0.5)
- Buying same ticker twice updates `avg_cost` correctly (weighted average calculation)

**LLM module (`app/llm.py`):**
- `build_portfolio_context` with positions in DB returns a string containing ticker, quantity, price, P&L
- `load_history` returns messages in chronological order (newest-first DB query is reversed)
- `call_llm` raises `ValueError` when `OPENROUTER_API_KEY` is unset and `LLM_MOCK` is not true
- `build_system_prompt` formats the template correctly (simple string interpolation, but worth a smoke test)

**API shape validation:**
- `GET /api/portfolio` with positions: verify each position object has `ticker`, `quantity`, `avg_cost`, `current_price`, `unrealized_pnl`, `value` fields
- `POST /api/portfolio/trade` response shape: `{status, ticker, side, quantity, price}` — currently tests only check status code
- `GET /api/portfolio/history` with zero snapshots returns `{"snapshots": []}`

These gaps are minor — the critical happy paths and error paths are already covered.

---

## Backend Unit Test Plan

### Trade logic tests needed

All go in `tests/test_portfolio.py`.

**`test_sell_all_shares_removes_position`**
- Buy 1 AAPL, then sell 1 AAPL
- `GET /api/portfolio` → `positions == []`

**`test_buy_updates_avg_cost`**
- Buy 1 AAPL at price P1, buy 1 more AAPL at price P2
- Verify `avg_cost == (P1 + P2) / 2` via portfolio response

**`test_buy_fractional_shares`**
- `POST /api/portfolio/trade` with `quantity=0.5`
- Portfolio shows `quantity == pytest.approx(0.5)`

**`test_sell_fractional_shares`**
- Buy 1.0, sell 0.5 → quantity == 0.5 remaining

**`test_invalid_trade_side_returns_400`**
- `POST /api/portfolio/trade` with `side="hold"` → HTTP 400

**`test_trade_response_shape`**
- Successful buy → response has keys `status`, `ticker`, `side`, `quantity`, `price`

**`test_portfolio_positions_shape`**
- After buy, `GET /api/portfolio` → each position has `ticker`, `quantity`, `avg_cost`, `current_price`, `unrealized_pnl`, `value`

**`test_portfolio_history_empty`**
- Fresh DB, no trades → `GET /api/portfolio/history` returns `{"snapshots": []}`

### LLM/chat tests needed

All go in `tests/test_chat.py` or a new `tests/test_llm.py`.

**`test_build_portfolio_context_with_positions`**
- Init DB, create a position row, call `build_portfolio_context(cache, "default")`
- Assert the returned string contains the ticker symbol and "cash"

**`test_load_history_chronological_order`**
- Insert two chat messages (user then assistant) with different `created_at` values
- Call `load_history("default")` → verify order is user then assistant (oldest first)

**`test_call_llm_raises_without_api_key`**
- `LLM_MOCK` not set, `OPENROUTER_API_KEY` not set → `call_llm([])` raises `ValueError`

**`test_build_system_prompt_contains_context`**
- `build_system_prompt("my context")` returns a string containing "my context"

### API shape tests needed

All go in existing test files.

**`test_get_portfolio_positions_fields`** — in `test_portfolio.py`

**`test_trade_response_fields`** — in `test_portfolio.py`

**`test_portfolio_history_empty_list`** — in `test_portfolio.py`

---

## E2E Test Plan

### Playwright setup

**Current state of `test/`:**
- `test/node_modules/playwright` and `test/node_modules/playwright-core` are installed (version unknown from file inspection — no `package.json` present)
- No `package.json`, no `playwright.config.ts`, no test spec files exist yet
- The directory has only `node_modules/` — everything else must be created

**What must be created in `test/`:**
- `package.json` — declares playwright as a dependency, sets `"type": "module"` or keeps CommonJS
- `playwright.config.ts` — sets `baseURL`, timeout, `webServer` (omitted since we use Docker), single `chromium` project
- `e2e/` subdirectory for test specs (or flat at `test/*.spec.ts`)
- `docker-compose.test.yml` — orchestrates the app + playwright containers

### docker-compose.test.yml structure

```yaml
version: "3.9"
services:
  app:
    image: finally          # must be pre-built: docker build -t finally .
    environment:
      - LLM_MOCK=true
      - DB_PATH=/app/db/finally.db
    volumes:
      - test-db:/app/db
    ports: []               # no host port needed; playwright reaches via service name
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 10s
      timeout: 5s
      retries: 6
      start_period: 15s

  playwright:
    image: mcr.microsoft.com/playwright:v1.51-jammy   # match installed version
    working_dir: /tests
    volumes:
      - ./:/tests           # mounts test/ dir (package.json, config, specs) into /tests
    depends_on:
      app:
        condition: service_healthy
    environment:
      - BASE_URL=http://app:8000
    command: npx playwright test --reporter=list
    network_mode: service:app  # simplest way to share network; or use a named network

volumes:
  test-db:

networks: {}               # if not using network_mode: service:app, declare a bridge network
```

**Alternative network approach (named network):**
```yaml
networks:
  testnet:
    driver: bridge

services:
  app:
    networks: [testnet]
  playwright:
    networks: [testnet]
    # then page.goto('http://app:8000') works because both share testnet
```

**Note on Playwright Docker image tag:** The `test/node_modules` has playwright installed but no `package.json` to show the version. The Microsoft Playwright Docker image tag must exactly match the installed version (e.g., `v1.51-jammy`). The implementation plan should read the installed version from `test/node_modules/playwright-core` before writing the compose file.

### Test scenarios (TEST-02 through TEST-05)

**TEST-02: Fresh container — default state visible**
File: `test/e2e/01-initial-state.spec.ts`
```
- page.goto('http://app:8000') (or process.env.BASE_URL)
- expect page title or header text 'FINALLY' to be visible
- wait for cash balance to show '$10,000.00' in header
- wait for at least one watchlist row containing 'AAPL'
- wait for a price element to appear (prices streaming)
```

**TEST-03: Add and remove a ticker**
File: `test/e2e/02-watchlist.spec.ts`
```
- The UI has no "add ticker" input in WatchlistPanel — add/remove goes through the chat or direct API
- The TradeBar handles trades, not watchlist management
- Best approach: call API directly in test setup (page.request.post('/api/watchlist', ...))
  then verify GET /api/watchlist contains the ticker, then DELETE and verify absence
- Alternatively: if the UI exposes watchlist management via chat (LLM_MOCK=true returns a
  WatchlistAction), test via chat flow
- Pragmatic: test the REST API directly from Playwright (api.spec.ts), not via UI
```

**Important finding:** The frontend has no manual watchlist add/remove UI element — only the chat panel can trigger watchlist changes via LLM. This means TEST-03 either:
1. Tests the API endpoints directly using `page.request` (simpler, more reliable), OR
2. Tests the chat flow with `LLM_MOCK=true` returning a `WatchlistAction` (more complex, tests the full path)

Recommendation: Use `page.request` for watchlist add/remove verification; reserve chat flow for TEST-05.

**TEST-04: Buy decreases cash, sell increases cash**
File: `test/e2e/03-trading.spec.ts`
```
- page.goto(BASE_URL)
- wait for '$10,000.00' in header (cash balance)
- fill ticker input: page.getByPlaceholder('TICKER').fill('AAPL')
- fill qty input: page.getByPlaceholder('Qty').fill('1')
- click Buy button: page.getByRole('button', {name: 'Buy'}).click()
- wait for cash to change (poll or waitForFunction)
- assert cash_balance < 10000 via API: page.request.get('/api/portfolio')
- verify position AAPL appears: page.locator('[data-ticker="AAPL"]') or check API
- fill ticker 'AAPL', qty '1', click Sell
- assert cash increases back
```

**TEST-05: AI chat (mocked) — response and trade confirmation**
File: `test/e2e/04-chat.spec.ts`
```
- LLM_MOCK=true returns deterministic response: "FinAlly here (mock mode). Portfolio looks good..."
- page.goto(BASE_URL)
- page.getByPlaceholder('Ask about portfolio or trade…').fill('Hello')
- page.getByRole('button', {name: 'Send'}).click()
- await page.waitForSelector('text=FinAlly here')  // assistant message appears
- For trade confirmation: need a mock that returns a trade action
  — but _MOCK_RESPONSE in llm.py has no trades by default
  — TEST-05 may need to configure LLM_MOCK differently, or accept that mock mode
    only tests the message display, not inline trade confirmation
  — trade confirmation display was already tested in test_chat.py (CHAT-03, CHAT-07)
  — for E2E purposes: verify message appears + actions section renders
```

**Critical finding on TEST-05 trade confirmation:** `_MOCK_RESPONSE` in `app/llm.py` returns `trades=[]` and `watchlist_changes=[]`. The inline "Executed: BUY..." confirmation in `ChatMessage.tsx` will never appear with the default mock. Options:
1. Add a second mock mode (e.g., `LLM_MOCK=trade`) that returns a buy trade — requires code change
2. Accept TEST-05 as only verifying message display, not trade inline confirmation
3. Pre-buy a position via API, then mock returns a sell — still needs a mock that returns trades

The implementation plan should extend mock mode or add a `LLM_MOCK_WITH_TRADE=true` env var.

### Page selectors strategy (what CSS/data attributes to target)

The frontend uses **inline styles and Tailwind utility classes**, not `data-testid` attributes. This makes selector strategy critical.

**Available stable selectors:**

| Target | Recommended selector |
|---|---|
| App header "FINALLY" text | `page.getByText('FINALLY')` |
| Cash balance in header | `page.getByText(/\$10,000\.00/)` (initial state) |
| "LIVE" connection status | `page.getByText('LIVE')` |
| Watchlist ticker (e.g. AAPL) | `page.getByText('AAPL').first()` — appears in watchlist row |
| Trade ticker input | `page.getByPlaceholder('TICKER')` |
| Trade quantity input | `page.getByPlaceholder('Qty')` |
| Buy button | `page.getByRole('button', { name: 'Buy' })` |
| Sell button | `page.getByRole('button', { name: 'Sell' })` |
| Chat textarea | `page.getByPlaceholder('Ask about portfolio or trade…')` |
| Chat send button | `page.getByRole('button', { name: 'Send' })` |
| Chat assistant message | `page.locator('text=FinAlly here')` |
| Trade error message | listens for red text containing the error |
| "AI Assistant" panel header | `page.getByText('AI Assistant')` |

**Note:** No `data-testid` attributes exist in the frontend. The implementation plan should add them to critical elements (cash display in header, watchlist rows, chat messages) to make E2E tests more robust. This is a small frontend change but dramatically improves selector stability.

Suggested additions:
- `data-testid="cash-balance"` on the cash `<span>` in `Header.tsx`
- `data-testid="portfolio-value"` on the portfolio total `<span>` in `Header.tsx`
- `data-testid="watchlist-row"` on each `WatchlistRow` div
- `data-testid="chat-message"` on each `ChatMessage` div
- `data-testid="trade-error"` on the error span in `TradeBar.tsx`

---

## Environment Availability

| Item | Status |
|---|---|
| `uv run pytest` (backend) | Available — `pyproject.toml` has pytest configured, `asyncio_mode = "auto"` |
| pytest dev deps | `pytest>=8.3`, `pytest-asyncio>=0.24`, `pytest-cov>=5.0`, `ruff>=0.7` |
| `httpx` (TestClient dep) | Included transitively via FastAPI |
| Playwright in `test/node_modules` | Installed (`playwright` + `playwright-core` packages present) |
| `test/package.json` | Missing — must be created |
| `test/playwright.config.ts` | Missing — must be created |
| `test/e2e/*.spec.ts` | Missing — must be created |
| `docker-compose.test.yml` | Missing — must be created |
| `finally` Docker image | Unknown — must be built before running E2E tests |
| `LLM_MOCK=true` support | Implemented in `app/llm.py` line 70 |
| `docker-compose.yml` | Missing from repo root (checked: no compose file exists) |

---

## Common Pitfalls

**1. Playwright Docker image version mismatch**
The `mcr.microsoft.com/playwright` image tag must match the installed `playwright` npm package version exactly. A mismatch causes browser binary not found errors. Check installed version before writing `docker-compose.test.yml`.

**2. App startup time in Docker**
The `finally` image starts the GBM simulator and initializes SQLite on boot. The `playwright` service must `depends_on: app: condition: service_healthy`. The HEALTHCHECK in the Dockerfile polls `/api/health` every 30s with a 10s start period — too slow for tests. The compose file should use a tighter interval (e.g., 5s interval, 3s timeout, 5 retries, 10s start_period).

**3. SSE stream in TestClient**
The existing `test_sse_stream_returns_event_stream` deliberately avoids connecting to the SSE endpoint because `TestClient` deadlocks on infinite generators. E2E tests can use `page.waitForFunction` to wait for live prices to appear in the DOM instead.

**4. No manual watchlist UI**
The frontend has no text input for adding watchlist tickers manually. TEST-03 must use `page.request` to call the REST API directly, or drive it through the chat panel (complex with mock mode). Using the API directly is more reliable.

**5. Mock mode returns no trades by default**
`_MOCK_RESPONSE` in `app/llm.py` has `trades=[]`. TEST-05 ("shows inline trade confirmation") cannot be tested with the current mock. Requires either: (a) a new environment variable for a richer mock response, or (b) accepting that the E2E test only validates message display.

**6. `time.sleep(0.1)` in existing backend tests**
Several existing tests call `time.sleep(0.1)` to let the market simulator seed prices before trading. This pattern is fine but brittle. New tests should follow the same pattern or mock the price cache directly (as `conftest.py` supports via `tmp_db` + manual `PriceCache.update()` calls).

**7. No `docker-compose.yml` at root**
The project has a `Dockerfile` but no `docker-compose.yml`. The test infrastructure must build the image separately (`docker build -t finally .`) or the `docker-compose.test.yml` must use a `build:` directive rather than `image: finally`.

**8. Frontend `data-testid` absence**
Without `data-testid` attributes, selectors rely on placeholder text, button labels, and visible content. These are reasonably stable for this app but worth adding for robustness.

---

## Sources

- `/Users/steve/projects/finally/backend/pyproject.toml` — pytest config, dev deps
- `/Users/steve/projects/finally/backend/tests/conftest.py` — `tmp_db` autouse fixture
- `/Users/steve/projects/finally/backend/tests/test_portfolio.py` — existing portfolio tests
- `/Users/steve/projects/finally/backend/tests/test_chat.py` — existing chat tests (CHAT-01 through CHAT-07)
- `/Users/steve/projects/finally/backend/tests/test_main.py` — app integration tests
- `/Users/steve/projects/finally/backend/tests/test_watchlist.py` — watchlist tests
- `/Users/steve/projects/finally/backend/tests/test_db.py` — DB schema and seed tests
- `/Users/steve/projects/finally/backend/app/routers/portfolio.py` — trade logic (`execute_trade_internal`, `record_snapshot`)
- `/Users/steve/projects/finally/backend/app/routers/chat.py` — chat endpoint auto-execute flow
- `/Users/steve/projects/finally/backend/app/llm.py` — `call_llm`, `_MOCK_RESPONSE`, `build_portfolio_context`, `load_history`
- `/Users/steve/projects/finally/frontend/components/TradeBar.tsx` — trade UI selectors (placeholder text)
- `/Users/steve/projects/finally/frontend/components/Header.tsx` — cash balance and connection status display
- `/Users/steve/projects/finally/frontend/components/ChatPanel.tsx` — chat UI selectors
- `/Users/steve/projects/finally/frontend/components/ChatMessage.tsx` — inline trade confirmation rendering
- `/Users/steve/projects/finally/frontend/components/WatchlistRow.tsx` — watchlist row structure
- `/Users/steve/projects/finally/frontend/components/WatchlistPanel.tsx` — no add/remove UI confirmed
- `/Users/steve/projects/finally/Dockerfile` — image build steps, HEALTHCHECK definition
- `/Users/steve/projects/finally/.planning/ROADMAP.md` — Phase 7 success criteria
- `test/node_modules/playwright`, `test/node_modules/playwright-core` — installed but unconfigured
