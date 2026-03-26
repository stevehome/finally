#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="finally"
IMAGE_NAME="finally"
PORT=8000

# Build if image doesn't exist or --build flag passed
if [[ "${1:-}" == "--build" ]] || ! docker image inspect "$IMAGE_NAME" &>/dev/null; then
    echo "Building Docker image..."
    docker build -t "$IMAGE_NAME" .
fi

# Stop existing container if running
docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

# Run container
echo "Starting FinAlly..."
ENV_FILE_ARG=""
if [[ -f .env ]]; then
    ENV_FILE_ARG="--env-file .env"
fi

docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$PORT:8000" \
    -v finally-data:/app/db \
    $ENV_FILE_ARG \
    "$IMAGE_NAME"

echo ""
echo "FinAlly is running at http://localhost:$PORT"
echo ""

# Open browser on macOS
if command -v open &>/dev/null; then
    open "http://localhost:$PORT"
fi
