# Phase 6: Docker & Deployment — Research

**Researched:** 2026-03-31
**Confidence:** HIGH

## Summary

The project has a well-defined architecture that maps cleanly to a multi-stage Docker build. Stage 1 uses Node 20 to build the Next.js static export; the `next.config.ts` already sets `distDir: '../backend/static'`, meaning `npm run build` writes the static export directly into `backend/static/` — so no separate copy step is needed between stages. Stage 2 uses Python 3.12 slim with uv installed via the official `ghcr.io/astral-sh/uv` image copy pattern. The backend's `main.py` mounts `backend/static/` at runtime only if the directory exists, which means the Dockerfile just needs to copy `backend/` (which includes `static/` from Stage 1) into the image.

The database path is driven by the `DB_PATH` environment variable, defaulting to `db/finally.db` (relative to the working directory, i.e., `/app/db/finally.db` when `WORKDIR` is `/app`). The volume mount `finally-data:/app/db` will therefore persist the SQLite file across container restarts without any extra configuration. No Dockerfile or `scripts/` directory exists yet — both are to be created in this phase.

Environment variables at runtime are: `OPENROUTER_API_KEY` (required for LLM chat), `MASSIVE_API_KEY` (optional, enables real market data), `LLM_MOCK` (optional, enables mock LLM responses), and `DB_PATH` (optional override, defaults to `db/finally.db`). Docker will read these from `--env-file .env`.

## Environment Availability

| Dependency | Available | Notes |
|---|---|---|
| Docker | Unknown (Bash denied) | Must be verified at build time; scripts should check |
| `scripts/` directory | No | Must be created |
| `Dockerfile` | No | Must be created |
| `backend/uv.lock` | Yes | Present at `backend/uv.lock` |
| `frontend/package-lock.json` | No | Must be generated (`npm install`) before build, or generated inside Docker |
| `next.config.ts` distDir | `../backend/static` | Static export writes to `backend/static/` |
| DB_PATH env var | Supported | Defaults to `db/finally.db`; resolves to `/app/db/finally.db` at WORKDIR /app |

## Standard Stack

### Dockerfile pattern

The official uv Docker pattern uses `COPY --from=ghcr.io/astral-sh/uv` to bring in the uv binary without a separate install step. This is preferred over `pip install uv` because it is faster, produces no pip-related layer, and tracks a specific uv version.

```dockerfile
# Stage 1: Build frontend static export
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# Output lands at /build/../backend/static → resolves to /backend/static
# But WORKDIR is /build, so distDir '../backend/static' = /backend/static
# We must copy it out explicitly

# Stage 2: Python backend
FROM python:3.12-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Layer cache: deps before source
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

# Copy backend source
COPY backend/ .

# Copy frontend static export from Stage 1
COPY --from=frontend /backend/static ./static/

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Critical distDir path resolution:** When Stage 1 `WORKDIR` is `/build` and `next.config.ts` sets `distDir: '../backend/static'`, the output goes to `/backend/static` (one level up from `/build`, then `backend/static`). The `COPY --from=frontend` must reference this resolved path. An alternative that avoids this confusion: set Stage 1 `WORKDIR` to `/app/frontend`, making distDir resolve to `/app/backend/static`, then copy from `/app/backend/static`.

**Recommended Stage 1 WORKDIR approach (cleaner):**
```dockerfile
FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
# distDir '../backend/static' resolves to /app/backend/static

FROM python:3.12-slim AS backend
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend/ .
COPY --from=frontend /app/backend/static ./static/
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### uv in Docker

The recommended pattern from astral.sh docs for Docker:

```dockerfile
# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Key environment variables for Docker builds
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install deps from lockfile, no dev deps
RUN uv sync --frozen --no-dev
```

- `UV_COMPILE_BYTECODE=1`: Pre-compiles `.py` to `.pyc` at install time so startup is faster.
- `UV_LINK_MODE=copy`: Prevents hardlinks (which don't work across Docker layer boundaries); forces file copy. Required in Docker.
- `--frozen`: Fails if `uv.lock` is out of sync with `pyproject.toml`. Enforces reproducibility.
- `--no-dev`: Excludes dev dependencies (pytest, ruff, etc.) from the production image.

**Running uvicorn:** Two valid options:
1. `CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]` — uses uv to invoke uvicorn within the project's virtual environment. Simple, no venv activation needed.
2. `CMD ["/app/.venv/bin/uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]` — invokes uvicorn directly from the venv. Slightly faster (no uv overhead), but couples to venv path.

Option 1 (`uv run`) is preferred for consistency with how the rest of the project uses uv.

### Layer caching strategy

Optimal order for maximum cache reuse:

**Stage 1 (Node):**
1. `COPY frontend/package.json frontend/package-lock.json ./` — cache npm deps separately
2. `RUN npm ci` — cached unless package-lock.json changes
3. `COPY frontend/ ./` — all other frontend source
4. `RUN npm run build`

**Stage 2 (Python):**
1. `COPY backend/pyproject.toml backend/uv.lock ./` — cache Python deps separately
2. `RUN uv sync --frozen --no-dev` — cached unless pyproject.toml or uv.lock changes
3. `COPY backend/ .` — all other backend source
4. `COPY --from=frontend ...` — frontend build artifacts

This means changing backend Python source (the common case) only invalidates layers 3-4 of Stage 2, not the `uv sync` layer.

**Note on package-lock.json:** The frontend currently has no `package-lock.json`. It must be generated (`npm install` locally, or the Dockerfile must use `npm install` instead of `npm ci` for the first build). For reproducible builds, the lock file should be committed. The Dockerfile should use `npm ci` (faster, strict) once the lock file exists.

## Architecture

### File layout

```
finally/
├── frontend/                    # Next.js source (Stage 1 input)
│   ├── package.json
│   ├── package-lock.json        # Must exist for npm ci
│   └── ...
├── backend/                     # FastAPI source (Stage 2 input)
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── main.py
│   ├── app/
│   └── static/                  # Created by Stage 1; NOT in git
├── db/                          # Volume mount target (gitkeep only)
│   └── .gitkeep
├── scripts/
│   ├── start_mac.sh
│   ├── stop_mac.sh
│   ├── start_windows.ps1
│   └── stop_windows.ps1
├── Dockerfile
├── .dockerignore
└── .env                         # gitignored; passed via --env-file
```

### Static files path

- **Build time:** `npm run build` in Stage 1 writes static export to `distDir: '../backend/static'`. With `WORKDIR /app/frontend`, this resolves to `/app/backend/static` inside the Stage 1 container.
- **Copy to Stage 2:** `COPY --from=frontend /app/backend/static ./static/` places output at `/app/static/` in the final image.
- **Runtime:** `main.py` computes `_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")`. With `main.py` at `/app/main.py`, this resolves to `/app/static/`. FastAPI mounts this directory at `/` if it exists.
- **Result:** Static files are served by FastAPI at `http://localhost:8000/` with `html=True` (index.html fallback for SPA routing).

### Database path

- `DB_PATH` defaults to `db/finally.db` (relative to cwd, which is `/app`).
- At runtime in the container: `/app/db/finally.db`.
- Volume mount: `finally-data:/app/db` — the entire `db/` directory is on the volume.
- `init_db()` calls `os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)`, so it creates `/app/db/` on first run if the volume is empty.

## Scripts

### start_mac.sh logic

```bash
#!/usr/bin/env bash
set -euo pipefail

IMAGE=finally
CONTAINER=finally
VOLUME=finally-data
PORT=8000

# Parse --build flag
BUILD=false
for arg in "$@"; do
  [[ "$arg" == "--build" ]] && BUILD=true
done

# Build if image doesn't exist or --build flag passed
if [[ "$BUILD" == "true" ]] || ! docker image inspect "$IMAGE" &>/dev/null; then
  echo "Building image..."
  docker build -t "$IMAGE" .
fi

# Stop existing container if running
docker rm -f "$CONTAINER" &>/dev/null || true

# Run container
docker run -d \
  --name "$CONTAINER" \
  -p "$PORT:$PORT" \
  -v "$VOLUME:/app/db" \
  --env-file .env \
  "$IMAGE"

echo "FinAlly running at http://localhost:$PORT"
sleep 1
open "http://localhost:$PORT"
```

### stop_mac.sh logic

```bash
#!/usr/bin/env bash
set -euo pipefail

CONTAINER=finally

docker stop "$CONTAINER" && docker rm "$CONTAINER"
echo "Container stopped. Volume (data) preserved."
# Do NOT run: docker volume rm finally-data
```

### start_windows.ps1 logic

```powershell
param([switch]$Build)

$Image = "finally"
$Container = "finally"
$Volume = "finally-data"
$Port = 8000

# Build if image missing or --Build flag
$imageExists = docker image inspect $Image 2>$null
if ($Build -or -not $imageExists) {
    Write-Host "Building image..."
    docker build -t $Image .
}

# Remove existing container (ignore errors)
docker rm -f $Container 2>$null

# Run
docker run -d `
    --name $Container `
    -p "${Port}:${Port}" `
    -v "${Volume}:/app/db" `
    --env-file .env `
    $Image

Write-Host "FinAlly running at http://localhost:$Port"
Start-Sleep 1
Start-Process "http://localhost:$Port"
```

### stop_windows.ps1 logic

```powershell
$Container = "finally"
docker stop $Container
docker rm $Container
Write-Host "Container stopped. Volume (data) preserved."
# Do NOT remove volume: docker volume rm finally-data
```

## .dockerignore

```
# Node
frontend/node_modules/
frontend/.next/
frontend/.next/cache/

# Python
backend/.venv/
backend/__pycache__/
backend/**/__pycache__/
backend/**/*.pyc

# Database (don't bake db into image; it lives on a volume)
db/*.db

# Secrets and env
.env

# Planning docs (not needed in image)
.planning/
planning/

# Git
.git/
.gitignore

# Scripts (not needed inside container)
scripts/

# Test artifacts
test/
```

## Common Pitfalls

### uv in Docker

- **`UV_LINK_MODE=copy` is required.** Without it, uv defaults to hardlinks which fail across Docker layers with "invalid cross-device link" errors.
- **Version pinning:** `COPY --from=ghcr.io/astral-sh/uv:latest` uses the latest release at build time. For reproducibility, pin a specific version: `ghcr.io/astral-sh/uv:0.5.x`. The project does not pin this yet.
- **`--frozen` will fail** if `uv.lock` is stale relative to `pyproject.toml`. Always commit `uv.lock` and regenerate it when adding dependencies.
- **`uv run` vs direct venv path:** `uv run` adds a small startup cost (~50ms). For production, calling `.venv/bin/uvicorn` directly is marginally faster but requires knowing the venv path.
- **No `VIRTUAL_ENV` activation needed.** `uv run` handles venv selection automatically.

### Next.js static export

- **`distDir: '../backend/static'`** writes outside the Next.js project directory. Docker COPY instructions in Stage 1 are relative to the build container's filesystem, not the host. Verify the resolved absolute path from the WORKDIR chosen in Stage 1.
- **`output: 'export'` disables image optimization by default.** The config already sets `images: { unoptimized: true }` to handle this.
- **`package-lock.json` does not currently exist.** Using `npm ci` requires it. Either commit it (recommended) or use `npm install` in the Dockerfile (slower, non-reproducible). Best practice: run `npm install` locally to generate it, commit it, then use `npm ci` in Docker.
- **`npm run build` errors** will abort the Docker build. The Next.js build must succeed locally before Dockerizing.

### Volume mount

- **Named volume vs bind mount:** `docker run -v finally-data:/app/db` creates a named Docker volume managed by Docker. This survives `docker rm` but is deleted by `docker volume rm finally-data`. The stop scripts must not include a `docker volume rm` call.
- **First run on empty volume:** `init_db()` in `app/db.py` calls `os.makedirs(..., exist_ok=True)`, so the `/app/db/` directory is created automatically on first startup. No manual setup needed.
- **DB_PATH must be relative to WORKDIR or absolute.** Default `db/finally.db` with WORKDIR `/app` resolves to `/app/db/finally.db` — this matches the volume mount target exactly.
- **Permissions:** Python 3.12-slim runs as root by default, so SQLite writes will succeed. If a non-root USER is added in future, the volume mount directory needs `chown`.

### Health check

- **`curl` must be installed** in the Python slim image. `python:3.12-slim` does not include curl by default. Add `RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*` before the HEALTHCHECK.
- **`--start-period`** gives the app time to initialize (DB init, market data start) before health checks begin failing. 10 seconds is a reasonable minimum.

### General

- **`.env` contains real API keys** (OPENROUTER_API_KEY, CEREBRAS_API_KEY). It must remain in `.dockerignore` and `.gitignore`. The `--env-file .env` flag passes values at runtime without baking them into the image.
- **Port conflicts:** If something else is running on 8000, `docker run -p 8000:8000` will fail. The start script could check for port availability.
- **`docker rm -f` in start script:** The start script does `docker rm -f $CONTAINER || true` before running a new container, making it idempotent (safe to run when the container is already running or stopped).

## Sources

Files read:
- `/Users/steve/projects/finally/backend/main.py` — FastAPI app, static mount path (`os.path.dirname(__file__) + "/static"`), lifespan
- `/Users/steve/projects/finally/backend/app/db.py` — `DB_PATH` default (`db/finally.db`), `os.makedirs` on init
- `/Users/steve/projects/finally/backend/pyproject.toml` — Python deps, hatchling build, uv project config
- `/Users/steve/projects/finally/frontend/package.json` — Next.js 16.2.1, build script `next build`
- `/Users/steve/projects/finally/frontend/next.config.ts` — `output: 'export'`, `distDir: '../backend/static'`
- `/Users/steve/projects/finally/.env` — env var names: `OPENROUTER_API_KEY`, `CEREBRAS_API_KEY`, `LLM_MOCK`
- `/Users/steve/projects/finally/.planning/ROADMAP.md` — Phase 6 success criteria

Structure checks:
- `scripts/` directory: does not exist (must be created)
- `Dockerfile`: does not exist (must be created)
- `backend/uv.lock`: exists
- `frontend/package-lock.json`: does not exist (must be generated)
- `db/` directory: does not exist in repo (must add `.gitkeep`)

Reference: astral.sh uv Docker documentation (pattern: `COPY --from=ghcr.io/astral-sh/uv`, `UV_LINK_MODE=copy`, `UV_COMPILE_BYTECODE=1`, `--frozen --no-dev`)
