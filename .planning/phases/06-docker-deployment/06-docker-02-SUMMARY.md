---
phase: 06-docker-deployment
plan: 2
status: complete
date: 2026-03-31
---

# Phase 06 Plan 2 Summary — Dockerfile

## What was done

Created `/Users/steve/projects/finally/Dockerfile` as a multi-stage build:

- **Stage 1** (`node:20-slim`, WORKDIR `/app/frontend`): installs npm deps via `npm ci`, builds Next.js static export using `npx next build --webpack`. With WORKDIR `/app/frontend`, `distDir: '../backend/static'` resolves to `/app/backend/static`.
- **Stage 2** (`python:3.12-slim`): installs `curl` for healthcheck, copies `uv` binary from `ghcr.io/astral-sh/uv:latest`, sets `UV_COMPILE_BYTECODE=1` and `UV_LINK_MODE=copy`, runs `uv sync --frozen --no-dev`, copies backend source, copies frontend static export from Stage 1 to `./static/`, configures HEALTHCHECK and CMD.

## Issues encountered and resolved

1. **Turbopack blocks `distDir` outside project root** — Next.js 16 with Turbopack (default) rejects `distDir: '../backend/static'`. Fixed by using `npx next build --webpack` to use webpack instead.
2. **`uv sync` fails: `README.md` not found** — `pyproject.toml` references `README.md` for the hatchling build backend. Fixed by including `backend/README.md` in the deps COPY layer alongside `pyproject.toml` and `uv.lock`.

## Verification results

```
docker image inspect finally --format '{{.RepoTags}}'
→ [finally:latest]

docker run --rm finally ls /app/static/index.html
→ /app/static/index.html

docker run --rm finally ls /app/.venv/bin/uvicorn
→ /app/.venv/bin/uvicorn

docker image inspect finally --format '{{.Config.Healthcheck}}'
→ {[CMD-SHELL curl -f http://localhost:8000/api/health || exit 1] 30s 5s 10s 0s 3}
```

## Files created/modified

- `Dockerfile` — created at project root (committed)
