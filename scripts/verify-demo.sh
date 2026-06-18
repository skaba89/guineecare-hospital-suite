#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api/v1}"
DEMO_EMAIL="${DEMO_EMAIL:-admin@guineecare.local}"
DEMO_PASSWORD="${DEMO_PASSWORD:-admin123}"

echo "Checking backend health..."
curl -fsS "${API_URL%/api/v1}/health"
echo

echo "Checking demo login..."
curl -fsS -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${DEMO_EMAIL}\",\"password\":\"${DEMO_PASSWORD}\"}"
echo

echo "Demo verification completed."
