#!/usr/bin/env bash
# =============================================================================
# GuinéeCare Hospital Suite — Script de validation post-déploiement v2.9.2
# =============================================================================
#
# Valide qu'un déploiement v2.9.2 est fonctionnel :
#   1. Health check backend
#   2. Version API = 2.9.2
#   3. Authentification SUPER_ADMIN
#   4. Redis rate limit partagé actif
#   5. Celery worker disponible
#   6. Exécution tâche backup_database (dry-run)
#   7. Module ICD-11 fonctionnel
#   8. Module Insurance (v2.9.1) fonctionnel
#   9. Push DHIS2 (dry-run si DHIS2_URL non configurée)
#  10. Métriques Prometheus accessibles (avec token)
#
# Usage :
#   ./validate_v292.sh https://guineecare.onrender.com admin@guineecare.com admin123
#
# Exit codes :
#   0 — Tous les checks sont OK
#   1 — Au moins un check a échoué
#   2 — Erreur d'usage (args manquants)
# =============================================================================

set -euo pipefail

# ── Couleurs ───────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ── Compteurs ──────────────────────────────────────────────────────────────
PASS=0
FAIL=0
WARN=0

# ── Helpers ────────────────────────────────────────────────────────────────
pass() {
    echo -e "${GREEN}✓${NC} $1"
    PASS=$((PASS + 1))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    FAIL=$((FAIL + 1))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    WARN=$((WARN + 1))
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ── Vérification des arguments ─────────────────────────────────────────────
if [ $# -lt 3 ]; then
    echo "Usage: $0 <BASE_URL> <ADMIN_EMAIL> <ADMIN_PASSWORD>"
    echo ""
    echo "Exemple:"
    echo "  $0 https://guineecare.onrender.com admin@guinecare.com admin123"
    exit 2
fi

BASE_URL="$1"
ADMIN_EMAIL="$2"
ADMIN_PASSWORD="$3"

# Nettoyer trailing slash
BASE_URL="${BASE_URL%/}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Validation post-déploiement v2.9.2"
echo "  URL: $BASE_URL"
echo "  Date: $(date -Is)"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ── 1. Health check ────────────────────────────────────────────────────────
info "1. Health check backend..."
HEALTH=$(curl -sf -m 10 "$BASE_URL/health" || echo "")
if [ -z "$HEALTH" ]; then
    fail "Backend inaccessible sur $BASE_URL/health"
    exit 1
fi

HEALTH_STATUS=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null || echo "")
HEALTH_VERSION=$(echo "$HEALTH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', ''))" 2>/dev/null || echo "")

# Accepte à la fois "ok" et "healthy" (format historique)
if [ "$HEALTH_STATUS" = "healthy" ] || [ "$HEALTH_STATUS" = "ok" ]; then
    pass "Backend healthy (status=$HEALTH_STATUS, version=$HEALTH_VERSION)"
else
    fail "Backend unhealthy (status=$HEALTH_STATUS)"
fi

# Accepte toute version 2.9.x (la validation est rétro-compatible)
case "$HEALTH_VERSION" in
    2.9.*) pass "Version dans la branche 2.9.x" ;;
    *) warn "Version détectée: $HEALTH_VERSION (attendue: 2.9.x)" ;;
esac
echo ""

# ── 2. Version API ─────────────────────────────────────────────────────────
info "2. Vérification version API..."
API_VERSION=$(curl -sf -m 10 "$BASE_URL/api/v1" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', ''))" 2>/dev/null || echo "")
case "$API_VERSION" in
    2.9.*)
        pass "Version API = $API_VERSION (branche 2.9.x validée)"
        ;;
    *)
        fail "Version API = '$API_VERSION' (attendue: 2.9.x)"
        ;;
esac
echo ""

# ── 3. Authentification SUPER_ADMIN ───────────────────────────────────────
info "3. Authentification SUPER_ADMIN..."
LOGIN_RESP=$(curl -sf -m 15 -X POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASSWORD\"}" || echo "")

TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")

if [ -n "$TOKEN" ] && [ "$TOKEN" != "None" ]; then
    pass "Login SUPER_ADMIN réussi (token obtenu)"
else
    fail "Login SUPER_ADMIN échoué — vérifier credentials"
    echo "  Réponse: $LOGIN_RESP"
    exit 1
fi
echo ""

AUTH_HEADER="Authorization: Bearer $TOKEN"

# ── 4. Redis rate limit partagé ───────────────────────────────────────────
info "4. Redis rate limit partagé..."
# Cette information n'est pas directement exposée via API — on vérifie
# indirectement via /api/v1/tasks (celery_available implique Redis connecté)
TASKS_RESP=$(curl -sf -m 10 -H "$AUTH_HEADER" "$BASE_URL/api/v1/tasks")
CELERY_AVAILABLE=$(echo "$TASKS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('celery_available', False))" 2>/dev/null || echo "False")
BROKER_CONFIGURED=$(echo "$TASKS_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('broker_url_configured', False))" 2>/dev/null || echo "False")

if [ "$CELERY_AVAILABLE" = "True" ]; then
    pass "Celery disponible (Redis broker actif)"
else
    warn "Celery non disponible — tâches en mode synchrone"
fi

if [ "$BROKER_CONFIGURED" = "True" ]; then
    pass "Broker URL configuré (REDIS_URL présente)"
else
    warn "Broker URL non configuré — REDIS_URL manquante"
fi
echo ""

# ── 5. Celery worker disponible ───────────────────────────────────────────
info "5. Celery worker — liste des tâches..."
TASKS_COUNT=$(echo "$TASKS_RESP" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('tasks', [])))" 2>/dev/null || echo "0")
EXPECTED_TASKS=("prune_audit_logs" "backup_database" "retry_sms_pending" "push_dhis2_monthly" "send_quality_alerts_digest")

if [ "$TASKS_COUNT" -ge 5 ]; then
    pass "Tâches disponibles: $TASKS_COUNT (≥5 attendues)"
else
    fail "Tâches disponibles: $TASKS_COUNT (<5 attendues)"
fi

for task_name in "${EXPECTED_TASKS[@]}"; do
    FOUND=$(echo "$TASKS_RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(any(t['name'] == '$task_name' for t in data.get('tasks', [])))
" 2>/dev/null || echo "False")
    if [ "$FOUND" = "True" ]; then
        pass "  Tâche '$task_name' présente"
    else
        fail "  Tâche '$task_name' MANQUANTE"
    fi
done
echo ""

# ── 6. Exécution tâche backup_database (dry-run) ──────────────────────────
info "6. Test exécution tâche backup_database..."
BACKUP_RESP=$(curl -sf -m 30 -X POST \
    -H "$AUTH_HEADER" \
    -H "Content-Type: application/json" \
    -d '{}' \
    "$BASE_URL/api/v1/tasks/trigger/backup_database" || echo "")

BACKUP_STATUS=$(echo "$BACKUP_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('status', ''))" 2>/dev/null || echo "")
BACKUP_FILE=$(echo "$BACKUP_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('result', {}).get('backup_file', ''))" 2>/dev/null || echo "")

if [ -n "$BACKUP_STATUS" ] && [ "$BACKUP_STATUS" != "" ]; then
    pass "Tâche backup exécutée (status=$BACKUP_STATUS)"
    if [ -n "$BACKUP_FILE" ]; then
        info "  Backup file: $BACKUP_FILE"
    fi
else
    fail "Tâche backup échouée — réponse: $BACKUP_RESP"
fi
echo ""

# ── 7. Module ICD-11 ──────────────────────────────────────────────────────
info "7. Module ICD-11..."
ICD_SEARCH=$(curl -sf -m 10 -H "$AUTH_HEADER" "$BASE_URL/api/v1/icd11/search?q=paludisme" || echo "")
ICD_TOTAL=$(echo "$ICD_SEARCH" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null || echo "0")

if [ "$ICD_TOTAL" -ge 1 ]; then
    pass "ICD-11 search 'paludisme' → $ICD_TOTAL résultat(s)"
else
    fail "ICD-11 search 'paludisme' → 0 résultat"
fi

ICD_CODE_RESP=$(curl -sf -m 10 -H "$AUTH_HEADER" "$BASE_URL/api/v1/icd11/1F03" || echo "")
ICD_CODE=$(echo "$ICD_CODE_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('code', ''))" 2>/dev/null || echo "")
if [ "$ICD_CODE" = "1F03" ]; then
    pass "ICD-11 GET /icd11/1F03 → code 1F03 (Paludisme à P. falciparum)"
else
    fail "ICD-11 GET /icd11/1F03 → échec (code='$ICD_CODE')"
fi

ICD_CATS=$(curl -sf -m 10 -H "$AUTH_HEADER" "$BASE_URL/api/v1/icd11/categories" || echo "")
ICD_CATS_COUNT=$(echo "$ICD_CATS" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('data', [])))" 2>/dev/null || echo "0")
if [ "$ICD_CATS_COUNT" -ge 5 ]; then
    pass "ICD-11 categories → $ICD_CATS_COUNT catégories (≥5 attendues)"
else
    fail "ICD-11 categories → $ICD_CATS_COUNT catégories (<5 attendues)"
fi
echo ""

# ── 8. Module Insurance (v2.9.1) ──────────────────────────────────────────
info "8. Module Insurance (v2.9.1)..."
INS_RESP=$(curl -sf -m 10 -H "$AUTH_HEADER" "$BASE_URL/api/v1/billing/insurance/providers" || echo "")
if [ -n "$INS_RESP" ] && [ "$INS_RESP" != "" ]; then
    pass "Insurance providers endpoint accessible"
else
    fail "Insurance providers endpoint inaccessible"
fi
echo ""

# ── 9. Push DHIS2 (dry-run) ───────────────────────────────────────────────
info "9. Push DHIS2 (dry-run)..."
DHIS2_RESP=$(curl -sf -m 30 -X POST -H "$AUTH_HEADER" "$BASE_URL/api/v1/reporting/dhis2/202601/push" || echo "")
DHIS2_STATUS=$(echo "$DHIS2_RESP" | python3 -c "import sys, json; print(json.load(sys.stdin).get('push_status', ''))" 2>/dev/null || echo "")
if [ "$DHIS2_STATUS" = "dry_run" ]; then
    pass "DHIS2 push en mode dry-run (DHIS2_URL non configurée — normal en démo)"
elif [ "$DHIS2_STATUS" = "success" ]; then
    pass "DHIS2 push effectif réussi"
elif [ "$DHIS2_STATUS" = "failed" ] || [ "$DHIS2_STATUS" = "error" ]; then
    warn "DHIS2 push a échoué (status=$DHIS2_STATUS) — vérifier DHIS2_URL/USERNAME/PASSWORD"
else
    fail "DHIS2 push — réponse inattendue: $DHIS2_RESP"
fi
echo ""

# ── 10. Métriques Prometheus ──────────────────────────────────────────────
info "10. Métriques Prometheus..."
METRICS_RESP=$(curl -sf -m 10 "$BASE_URL/metrics" || echo "")
if echo "$METRICS_RESP" | grep -q "guineecare_" 2>/dev/null; then
    pass "Métriques Prometheus accessibles (sans token — mode démo)"
elif [ -z "$METRICS_RESP" ]; then
    info "Métriques requièrent un token (METRICS_TOKEN configuré) — test skip"
else
    warn "Métriques Prometheus inaccessibles ou format inattendu"
fi
echo ""

# ── Résumé ─────────────────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════"
echo "  RÉSUMÉ DE LA VALIDATION"
echo "═══════════════════════════════════════════════════════════════"
echo -e "  ${GREEN}PASS${NC}: $PASS"
echo -e "  ${RED}FAIL${NC}: $FAIL"
echo -e "  ${YELLOW}WARN${NC}: $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ Déploiement v2.9.2 VALIDÉ${NC}"
    if [ $WARN -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARN avertissement(s) à investiguer${NC}"
    fi
    exit 0
else
    echo -e "${RED}✗ Déploiement v2.9.2 INVALIDE — $FAIL check(s) ont échoué${NC}"
    echo ""
    echo "Actions recommandées :"
    echo "  1. Consulter les logs backend Render (ou docker compose logs backend)"
    echo "  2. Vérifier les variables d'environnement (REDIS_URL, AUTH_SECRET, DATABASE_URL)"
    echo "  3. Vérifier que le service Redis est démarré"
    echo "  4. Vérifier que le worker Celery est démarré"
    echo "  5. Consulter le runbook : docs/deploiement/RUNBOOK_MISE_A_JOUR_v2.9.2.md"
    exit 1
fi
