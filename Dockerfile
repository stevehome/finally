# Stage 1: Build frontend static export
FROM node:20-slim AS frontend-build

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with static frontend
FROM python:3.12-slim

# Install curl for Docker healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install Python dependencies (cached layer)
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --frozen --no-dev

# Copy backend source AFTER uv sync so .venv is not overwritten
# (.venv is excluded via .dockerignore, but this ordering is also a safeguard)
COPY backend/app/ ./app/
COPY backend/tests/ ./tests/

# Copy frontend static export
COPY --from=frontend-build /build/out/ /app/static/

# Create db directory for volume mount
RUN mkdir -p /app/db

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
