#!/usr/bin/env bash
set -euo pipefail

echo "Resetting GuineeCare demo stack..."
docker compose down -v
docker compose build --no-cache
docker compose up
