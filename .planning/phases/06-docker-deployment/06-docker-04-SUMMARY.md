---
phase: 06-docker-deployment
plan: 04
subsystem: infra
tags: [docker, multi-stage, uv, next.js, scripts, bash, powershell]

requires:
  - phase: 05-charts-portfolio-trade-ui
    provides: Complete frontend static export, all API endpoints working

provides:
  - Single-container Docker deployment of the full FinAlly stack
  - Mac and Windows start/stop scripts

tech-stack:
  added:
    - Docker multi-stage build (node:20-slim + python:3.12-slim)
    - ghcr.io/astral-sh/uv (uv binary via COPY --from)
  patterns:
    - UV_LINK_MODE=copy prevents cross-device hardlink errors in Docker
    - UV_COMPILE_BYTECODE=1 for faster container startup
    - Always-mounted chart container pattern (useEffect timing)
    - distDir '../backend/static' resolves relative to WORKDIR /app/frontend in Docker

key-files:
  created:
    - Dockerfile
    - .dockerignore
    - db/.gitkeep
    - scripts/start_mac.sh
    - scripts/stop_mac.sh
    - scripts/start_windows.ps1
    - scripts/stop_windows.ps1
  modified:
    - frontend/hooks/useWatchlist.ts (added refetch())
    - frontend/hooks/useChat.ts (added onPortfolioChange/onWatchlistChange callbacks)
    - frontend/components/ChatPanel.tsx (accept and forward callbacks)
    - frontend/components/AppShell.tsx (wire refetch callbacks to ChatPanel)
    - backend/README.md (required by hatchling during uv sync)

key-decisions:
  - "Turbopack rejects distDir outside project root — use --webpack flag in npm run build"
  - "python:3.12-slim has no curl — apt-get install curl needed for HEALTHCHECK"
  - "uv installed via COPY --from=ghcr.io/astral-sh/uv (not pip install uv)"
  - "start_mac.sh uses docker rm -f for idempotency — safe to call multiple times"
  - "Volume finally-data:/app/db never removed by stop scripts — data persists across restarts"
  - "AI trades/watchlist changes needed immediate UI refresh — useChat now calls refetch callbacks after response"
  - "useWatchlist fetched only on mount — added refetch() so AI watchlist changes appear immediately"

patterns-established:
  - "ChatPanel accepts onPortfolioChange + onWatchlistChange props — call after AI actions"
  - "useWatchlist returns {tickers, refetch} — same pattern as usePortfolio"
---

## Phase 6 Complete — All DOCK Success Criteria Verified

- **DOCK-01** ✓ Multi-stage Dockerfile builds frontend (Node 20) then backend (Python 3.12 + uv)
- **DOCK-02** ✓ `docker run -v finally-data:/app/db -p 8000:8000 --env-file .env finally` serves full app
- **DOCK-03** ✓ Portfolio data persists across container stop/start via named volume
- **DOCK-04** ✓ `scripts/start_mac.sh` / `scripts/stop_mac.sh` work; volume not deleted on stop
- **DOCK-05** ✓ PowerShell equivalents created (`start_windows.ps1`, `stop_windows.ps1`)
- **DOCK-06** ✓ HEALTHCHECK returns `healthy` via `docker inspect`

### Bugs fixed during verification
1. **Portfolio not updating after AI trade** — `useChat.sendMessage` never called `refetch()`; fixed by adding `onPortfolioChange` callback threaded through `ChatPanel` → `useChat`
2. **Watchlist not updating after AI add** — `useWatchlist` fetched only on mount; fixed by exposing `refetch()` and passing `onWatchlistChange` to `ChatPanel`
