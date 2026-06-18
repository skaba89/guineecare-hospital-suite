#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api/v1}"
EMAIL="${EMAIL:-admin@guineecare.local}"
PASSWORD="${PASSWORD:-admin123}"

echo "Testing backend health..."
curl -fsS "${API_URL%/api/v1}/health"
echo

echo "Testing login for ${EMAIL}..."
curl -fsS -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${EMAIL}\",\"password\":\"${PASSWORD}\"}"
echo
