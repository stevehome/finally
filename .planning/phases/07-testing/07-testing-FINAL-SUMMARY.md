---
phase: 07-testing
plan: final
type: summary
status: complete
---

# Phase 07 Summary: Testing

## What was done

1. **Backend unit tests** — 117 tests covering trade logic (buy/sell/edge cases), LLM structured output parsing, chat API route shapes, portfolio snapshot recording, and watchlist management. All pass with `uv run pytest`.

2. **data-testid attributes** — Added to all key frontend components for reliable E2E selectors:
   - `cash-balance`, `portfolio-value` (Header)
   - `watchlist-row-{ticker}` (WatchlistRow)
   - `trade-ticker`, `trade-qty`, `buy-btn`, `sell-btn`, `trade-error` (TradeBar)
   - `chat-messages`, `chat-message` (ChatPanel/ChatMessage)

3. **Mock LLM response** — `_MOCK_RESPONSE` updated to include `TradeAction(ticker=AAPL, side=buy, quantity=1)` enabling inline trade confirmation assertion in TEST-05.

4. **E2E test specs** — 15 Playwright tests across 4 files:
   - `01-initial-state.spec.ts` — header, cash balance format, 10 tickers, LIVE status, price streaming
   - `02-watchlist.spec.ts` — add/remove ticker via API, default 10 tickers
   - `03-trading.spec.ts` — buy decreases cash (relative), sell increases cash (relative), invalid shows error
   - `04-chat.spec.ts` — assistant response, inline BUY confirmation, user message history, portfolio update (relative)

5. **Playwright infrastructure** — `test/package.json`, `test/playwright.config.ts`, `docker-compose.test.yml` with app + playwright containers on shared `testnet` bridge.

6. **Relative balance assertions** — Fixed 3 tests that were brittle against accumulated DB state:
   - `01-initial-state`: asserts cash matches `$\d+\.\d{2}` format (not exact $10k)
   - `03-trading` buy test: captures API balance before buy, asserts it decreased
   - `04-chat` portfolio test: captures API balance before chat, asserts it decreased

## Verification

All 15 Playwright E2E tests pass against the running container (`LLM_MOCK=true`, port 8000).

## Key decisions

- Relative balance assertions make tests DB-state-agnostic — mock LLM always buys AAPL, so exact $10k assertions fail on re-runs
- `waitForFunction` polling the API (rather than UI text matching) is more reliable for async trade completion
- `docker-compose.test.yml` uses no volume for app service — each CI run gets a fresh DB
