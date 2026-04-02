# Stage 1: Build Next.js static export
FROM node:20-slim AS frontend
WORKDIR /app/frontend

# Cache npm deps separately from source
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy all frontend source and build
# distDir '../backend/static' with WORKDIR /app/frontend resolves to /app/backend/static
COPY frontend/ ./
RUN npx next build --webpack


# Stage 2: Python backend
FROM python:3.12-slim AS backend

# Install curl (needed for HEALTHCHECK) and uv
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv --no-cache-dir

WORKDIR /app

# uv Docker best-practices
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Cache Python deps separately from source
COPY backend/pyproject.toml backend/uv.lock backend/README.md ./
RUN uv sync --frozen --no-dev

# Copy backend source
COPY backend/ .

# Copy frontend static export from Stage 1
# /app/backend/static (Stage 1) -> /app/static/ (Stage 2)
COPY --from=frontend /app/backend/static ./static/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
