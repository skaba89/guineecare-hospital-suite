#!/usr/bin/env bash
# =============================================================================
# GuinéeCare — Vérification de santé + login démo
# =============================================================================
# Usage :
#   ./scripts/verify-demo.sh                          # localhost:8000
#   API_URL=https://guineecare.onrender.com/api/v1 ./scripts/verify-demo.sh
#
# ⚠️  DEMO ONLY — les credentials ci-dessous sont issus du seed démo
#     (SEED_DEMO_DATA=true). NE JAMAIS utiliser en production.
#     En production, créer un super-admin via :
#       python -m app.cli create-superuser --email admin@votre-hopital.gn
# =============================================================================
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000/api/v1}"
# v2.3.0 — Phase 8 : aligné sur le seed (admin@guineecare.com, pas .local)
DEMO_EMAIL="${DEMO_EMAIL:-admin@guineecare.com}"
DEMO_PASSWORD="${DEMO_PASSWORD:-admin123}"

echo "═══════════════════════════════════════════════════════════════"
echo "  GuinéeCare — Demo verification"
echo "  API: ${API_URL}"
echo "  ⚠️  DEMO ONLY — ne pas utiliser en production"
echo "═══════════════════════════════════════════════════════════════"

echo ""
echo "1) Backend health check..."
curl -fsS "${API_URL%/api/v1}/health" || {
  echo "❌ Backend health check failed"
  exit 1
}
echo ""

echo ""
echo "2) Demo login (admin@guineecare.com)..."
LOGIN_RESPONSE=$(curl -fsS -X POST "${API_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"${DEMO_EMAIL}\",\"password\":\"${DEMO_PASSWORD}\"}") || {
  echo "❌ Login failed — check API_URL and seed data"
  exit 1
}
echo "${LOGIN_RESPONSE}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if 'access_token' in data:
    print('✅ Login OK — access_token reçu (60 min)')
    print(f'   User: {data.get(\"user\", {}).get(\"email\", \"?\")}')
    print(f'   Role: {data.get(\"user\", {}).get(\"role\", \"?\")}')
else:
    print('⚠️  Réponse inattendue:', data)
"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Demo verification completed successfully"
echo "═══════════════════════════════════════════════════════════════"
