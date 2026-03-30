# Technology Stack

**Analysis Date:** 2026-03-30

## Languages

**Primary:**
- Python 3.12 - Backend API, market data simulation, LLM integration
- TypeScript - Frontend application (Next.js, not yet developed)
- SQL - SQLite database schema

**Secondary:**
- JavaScript/Node.js - Frontend build tooling (Next.js)
- Bash/PowerShell - Deployment scripts

## Runtime

**Environment:**
- Python 3.12 runtime (backend via Docker)
- Node 20 (frontend build via Docker multi-stage)

**Package Manager:**
- `uv` - Python package manager for backend (`backend/pyproject.toml`)
- npm - Node package manager for frontend (configured but not yet populated)

**Lock Files:**
- `backend/uv.lock` - Python dependency pinning
- Frontend: `package-lock.json` expected (not yet created)

## Frameworks

**Core:**
- FastAPI 0.115+ - REST API and server framework, Python backend
- Next.js - Frontend framework (static export configured per plan)
- Uvicorn 0.32+ - ASGI application server, runs FastAPI

**Testing:**
- pytest 8.3+ - Python unit testing
- pytest-asyncio 0.24+ - Async test support
- pytest-cov 5.0+ - Code coverage reporting
- Playwright - E2E testing (configured, tests in `test/` directory)

**Build/Dev:**
- Ruff 0.7+ - Python linting and code formatting
- Hatchling - Python package builder

## Key Dependencies

**Critical:**
- `fastapi>=0.115.0` - API framework, request handling, SSE streaming support
- `uvicorn[standard]>=0.32.0` - ASGI server with WebSocket/SSE support
- `numpy>=2.0.0` - Numeric computation for GBM market simulator
- `massive>=1.0.0` - Polygon.io market data SDK (optional integration)
- `rich>=13.0.0` - Terminal UI utilities and logging enhancements

**Infrastructure:**
- Standard library: `sqlite3` (for SQLite database)
- Standard library: `asyncio` (async task management for streaming)
- Standard library: `dataclasses` (model definitions)

## Configuration

**Environment:**
- `.env` file (gitignored) - Runtime configuration
- Environment variables control data source selection and LLM integration

**Build:**
- `Dockerfile` (multi-stage)
  - Stage 1: Node 20 slim - builds Next.js frontend static export
  - Stage 2: Python 3.12 slim - installs backend via `uv sync`, serves everything
- `docker-compose.yml` - Optional convenience wrapper
- `pyproject.toml` - Backend Python project configuration, dependencies, tool settings

## Platform Requirements

**Development:**
- Python 3.12+
- Docker (for containerized development and deployment)
- Node 20+ (for frontend builds)
- uv package manager
- Git

**Production:**
- Docker container deployment (single port 8000)
- Volume mount for SQLite persistence: `db/` directory
- Network access to OpenRouter API (LLM) if OPENROUTER_API_KEY provided
- Network access to Massive API (optional, if MASSIVE_API_KEY provided)

---

*Stack analysis: 2026-03-30*
