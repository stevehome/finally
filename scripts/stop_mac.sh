#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="finally"

if docker rm -f "$CONTAINER_NAME" 2>/dev/null; then
    echo "FinAlly stopped."
else
    echo "FinAlly is not running."
fi
