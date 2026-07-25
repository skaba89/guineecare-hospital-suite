#!/usr/bin/env bash
# =============================================================================
# GuinéeCare — Création d'un super-admin (wrapper CLI)
# =============================================================================
# Usage :
#   ./scripts/create-superadmin.sh
#   ./scripts/create-superadmin.sh --email admin@hopital.gn --first-name "Admin" --last-name "Hôpital"
#
# En mode Docker :
#   docker compose exec backend bash /app/../scripts/create-superadmin.sh
#
# ⚠️ Le mot de passe sera demandé interactivement (jamais en argument).
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Si on est dans Docker (le projet est monté dans /app), utiliser python direct
if [[ -f /app/app/main.py ]]; then
  cd /app
  PYTHON_CMD="python -m app.cli create-superuser"
else
  # Mode local — utiliser le venv backend
  cd "$PROJECT_DIR/backend"
  if [[ -f .venv/bin/activate ]]; then
    source .venv/bin/activate
  fi
  PYTHON_CMD="python -m app.cli create-superuser"
fi

# Parse args
EMAIL=""
FIRST_NAME=""
LAST_NAME=""
FACILITY_ID=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --email) EMAIL="$2"; shift 2 ;;
    --first-name) FIRST_NAME="$2"; shift 2 ;;
    --last-name) LAST_NAME="$2"; shift 2 ;;
    --facility-id) FACILITY_ID="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: $0 [--email admin@hopital.gn] [--first-name Admin] [--last-name Hôpital] [--facility-id <id>]"
      exit 0
      ;;
    *) echo "Argument inconnu: $1"; exit 1 ;;
  esac
done

echo "═══════════════════════════════════════════════════════════════"
echo "  GuinéeCare — Création d'un super-admin"
echo "═══════════════════════════════════════════════════════════════"

# Si args manquants, prompt interactif
if [[ -z "$EMAIL" ]]; then
  read -rp "Email du super-admin : " EMAIL
fi
if [[ -z "$FIRST_NAME" ]]; then
  read -rp "Prénom : " FIRST_NAME
fi
if [[ -z "$LAST_NAME" ]]; then
  read -rp "Nom : " LAST_NAME
fi

# Construction de la commande
CMD="$PYTHON_CMD --email \"$EMAIL\" --first-name \"$FIRST_NAME\" --last-name \"$LAST_NAME\""
if [[ -n "$FACILITY_ID" ]]; then
  CMD="$CMD --facility-id \"$FACILITY_ID\""
fi

echo ""
echo "⚠️  Le mot de passe sera demandé de façon interactive."
echo "    Politique : 12+ caractères, 1 majuscule, 1 minuscule, 1 chiffre, 1 spécial."
echo ""

eval "$CMD"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Super-admin créé : $EMAIL"
echo "  🔒 Connectez-vous et activez 2FA immédiatement"
echo "═══════════════════════════════════════════════════════════════"
