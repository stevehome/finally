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
  docker build -t "$IMAGE" "$(dirname "$0")/.."
fi

# Stop and remove existing container (idempotent)
docker rm -f "$CONTAINER" &>/dev/null || true

# Run container
docker run -d \
  --name "$CONTAINER" \
  -p "$PORT:$PORT" \
  -v "$VOLUME:/app/db" \
  --env-file "$(dirname "$0")/../.env" \
  "$IMAGE"

echo "FinAlly running at http://localhost:$PORT"
sleep 2
open "http://localhost:$PORT"
