# FinAlly — AI Trading Workstation

## What This Is

FinAlly is a visually stunning, single-container AI-powered trading workstation that streams live market data, lets users trade a simulated $10k portfolio, and integrates an LLM chat assistant that can analyze positions and execute trades on the user's behalf. It is a capstone project for an agentic AI coding course, built entirely by coding agents, and runs via a single Docker command with no login required.

## Core Value

A Bloomberg-terminal-aesthetic trading workstation where users watch live prices stream, trade a simulated portfolio, and converse with an AI that can execute trades on their behalf — all from one browser tab, zero setup.

## Requirements

### Validated

- ✓ Market data subsystem (GBM simulator + Massive/Polygon.io client, PriceCache, SSE stream endpoint) — Phase 0 / pre-GSD
- ✓ FastAPI backend with SQLite database (schema, seed data, lazy init) — Validated in Phase 1: backend-foundation
- ✓ FastAPI app entry point with lifespan, health endpoint, SSE stream router — Validated in Phase 1: backend-foundation

### Active

- [ ] REST API endpoints (portfolio, watchlist, trades, chat, health)
- [ ] REST API endpoints (portfolio, watchlist, trades, chat, health)
- [ ] Frontend: dark-theme trading terminal UI (Next.js static export)
- [ ] Watchlist panel with live price updates and sparklines
- [ ] Main chart area for selected ticker
- [ ] Portfolio heatmap (treemap) and P&L chart
- [ ] Positions table with unrealized P&L
- [ ] Trade bar (buy/sell market orders)
- [ ] AI chat panel with LLM integration (LiteLLM → OpenRouter/Cerebras)
- [ ] LLM auto-executes trades and watchlist changes from chat
- [ ] Docker multi-stage build (Node → Python, single port 8000)
- [ ] Start/stop scripts for Mac and Windows
- [ ] End-to-end Playwright test suite
- [ ] Unit tests for backend (portfolio logic, LLM parsing, API routes)

### Out of Scope

- Multi-user / authentication — single hardcoded "default" user; schema has user_id for future-proofing only
- Limit orders / order book — market orders only, dramatically simpler
- Real-money trading or brokerage integration — simulated portfolio only
- Mobile-first design — desktop-first, functional on tablet
- Cloud deployment Terraform — stretch goal, not in core build
- WebSockets — SSE is sufficient for one-way price push

## Context

- **Already built**: `backend/app/market/` — complete market data subsystem (8 modules, ~500 lines, 73 tests passing, 84% coverage). GBM simulator + Massive REST client, PriceCache, SSE endpoint at `/api/stream/prices`. `backend/app/db.py` — SQLite schema (6 tables), seed data, connection helpers. `backend/main.py` — FastAPI app with lifespan, health router, SSE router, static file stub. 84 tests passing.
- **Tech stack**: FastAPI + uv (Python), Next.js static export (TypeScript), SQLite, SSE, LiteLLM → OpenRouter (`openrouter/openai/gpt-oss-120b` via Cerebras), Docker single container port 8000.
- **LLM**: Structured outputs, returns `{message, trades[], watchlist_changes[]}`. Auto-executes trades — no confirmation dialog. Mock mode via `LLM_MOCK=true`.
- **Course context**: Built by AI coding agents demonstrating orchestrated agentic development. Code clarity and demo-ability matter.

## Constraints

- **Tech Stack**: FastAPI + uv, Next.js static export, SQLite, Docker single container — architecture is fixed per spec
- **Python tooling**: Always `uv run` / `uv add`, never `python3` / `pip install`
- **Single port**: Everything served on port 8000 — no CORS, no separate dev servers in production
- **LLM provider**: LiteLLM → OpenRouter → Cerebras (`openrouter/openai/gpt-oss-120b`) — structured outputs required
- **Market orders only**: No limit orders, no partial fills, instant execution at current price
- **No auth**: Single user "default", no login/signup

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SSE over WebSockets | One-way push sufficient; simpler, universal browser support | ✓ Good |
| Static Next.js export | Single origin, no CORS, one port, one container | — Pending |
| SQLite over Postgres | No auth = no multi-user = no DB server needed | — Pending |
| GBM simulator default | No API key required; realistic-looking price action | ✓ Good |
| LiteLLM → OpenRouter | Fast Cerebras inference; structured output support | — Pending |
| No confirmation on AI trades | Simulated money, fluid demo experience, shows agentic capability | — Pending |

---
*Last updated: 2026-03-30 after Phase 1: backend-foundation complete*
