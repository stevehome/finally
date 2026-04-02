---
phase: 07-testing
plan: 02
subsystem: testing
tags: [playwright, data-testid, e2e, mock]

provides:
  - data-testid attributes on all key frontend components for reliable E2E selectors
  - _MOCK_RESPONSE with a trade action for TEST-05 chat confirmation test

key-files:
  modified:
    - frontend/components/Header.tsx (cash-balance, portfolio-value)
    - frontend/components/WatchlistRow.tsx (watchlist-row-{ticker})
    - frontend/components/TradeBar.tsx (trade-ticker, trade-qty, buy-btn, sell-btn, trade-error)
    - frontend/components/ChatPanel.tsx (chat-messages)
    - frontend/components/ChatMessage.tsx (chat-message)
    - backend/app/llm.py (_MOCK_RESPONSE now includes AAPL buy trade)

key-decisions:
  - "_MOCK_RESPONSE includes TradeAction(ticker=AAPL, side=buy, quantity=1) — enables TEST-05 inline confirmation assertion"
  - "data-testid on WatchlistRow root div uses template literal watchlist-row-{ticker} for per-ticker targeting"
---

All data-testid attributes added and frontend build passes.
