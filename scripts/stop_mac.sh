#!/usr/bin/env bash
set -euo pipefail
CONTAINER=finally-app

if docker ps -q -f "name=^/${CONTAINER}$" | grep -q .; then
  echo "Stopping FinAlly..."
  docker stop "$CONTAINER" >/dev/null
  docker rm "$CONTAINER" >/dev/null
  echo "Stopped. Data volume 'finally-data' is preserved."
elif docker ps -aq -f "name=^/${CONTAINER}$" | grep -q .; then
  docker rm "$CONTAINER" >/dev/null
  echo "Removed stopped container."
else
  echo "No FinAlly container found."
fi
