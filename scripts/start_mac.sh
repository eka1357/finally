#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BUILD=0
NO_BROWSER=0
for arg in "$@"; do
  case "$arg" in
    --build) BUILD=1 ;;
    --no-browser) NO_BROWSER=1 ;;
  esac
done

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — add your API keys."
fi

IMAGE=finally
CONTAINER=finally-app

if [[ $BUILD -eq 1 ]] || ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "Building Docker image..."
  docker build -t "$IMAGE" .
fi

if docker ps -q -f "name=^/${CONTAINER}$" | grep -q .; then
  echo "Container already running."
else
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
  echo "Starting FinAlly..."
  docker run -d \
    --name "$CONTAINER" \
    -p 8000:8000 \
    -v finally-data:/app/db \
    --env-file .env \
    "$IMAGE" >/dev/null
fi

echo ""
echo "FinAlly is available at http://localhost:8000"
if [[ $NO_BROWSER -eq 0 ]]; then
  if command -v open >/dev/null 2>&1; then open "http://localhost:8000"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "http://localhost:8000"
  fi
fi
