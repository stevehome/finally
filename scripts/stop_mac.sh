#!/usr/bin/env bash
set -euo pipefail

CONTAINER=finally

docker stop "$CONTAINER" && docker rm "$CONTAINER"
echo "Container stopped. Volume (data) preserved."
# Do NOT run: docker volume rm finally-data
