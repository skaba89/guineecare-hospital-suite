#!/usr/bin/env bash
# =============================================================================
# GuinéeCare Hospital Suite — Seed pilot data for CHU Donka
# =============================================================================
#
# Creates the initial set of REAL users / facilities / departments for the
# CHU Donka pilot. NOT demo data — these are production accounts with strong
# passwords. Run ONCE after a fresh deploy, then change passwords immediately.
#
# Usage:
#   bash scripts/seed-pilot.sh
#
# Pre-requisites:
#   - Backend container is running and healthy
#   - .env.production is set up
#   - BOOTSTRAP_TOKEN is set in .env.production
#
# After running:
#   - Distribute the printed passwords to each user via a secure channel
#   - Force password change on first login (TODO: v1.1 feature)
# =============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "ERROR: Missing $ENV_FILE" >&2
    exit 1
fi
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

if [[ -z "${BOOTSTRAP_TOKEN:-}" ]]; then
    echo "ERROR: BOOTSTRAP_TOKEN must be set in $ENV_FILE" >&2
    exit 1
fi

# Generate strong random passwords
gen_pw() {
    # 16 chars, alphanumeric + safe symbols
    openssl rand -base64 24 | tr -d '/+=' | head -c 16
    echo
}

# --- Bootstrap super-admin (idempotent — skips if already exists) ---
SUPERADMIN_EMAIL="${SUPERADMIN_EMAIL:-admin@chu-donka.gn}"
SUPERADMIN_PW="${SUPERADMIN_PW:-$(gen_pw)}"

echo ""
echo "=== GuinéeCare pilot seeding ==="
echo ""

# Check if super-admin already exists
EXISTING=$(docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T postgres \
    psql -U guineecare -d guineecare -tAc \
    "SELECT email FROM users WHERE email = '$SUPERADMIN_EMAIL' LIMIT 1" 2>/dev/null | tr -d '[:space:]')

if [[ -z "$EXISTING" ]]; then
    echo "→ Creating SUPER_ADMIN: $SUPERADMIN_EMAIL"
    docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T backend \
        python -m app.cli create-superuser \
            --email "$SUPERADMIN_EMAIL" \
            --password "$SUPERADMIN_PW" \
            --first-name "Super" \
            --last-name "Admin"
    echo ""
    echo "  ┌──────────────────────────────────────────────────────────┐"
    echo "  │ SUPER_ADMIN credentials (DISTRIBUTE SECURELY):          │"
    echo "  │   email:    $SUPERADMIN_EMAIL"
    echo "  │   password: $SUPERADMIN_PW"
    echo "  └──────────────────────────────────────────────────────────┘"
else
    echo "✓ SUPER_ADMIN already exists: $SUPERADMIN_EMAIL (skipping)"
    SUPERADMIN_PW="(already set — ask the user to use password reset)"
fi

echo ""
echo "✓ Pilot seeding complete."
echo ""
echo "Next steps:"
echo "  1. Distribute the SUPER_ADMIN password via a secure channel (Signal, in-person)."
echo "  2. User logs in at $PUBLIC_URL and changes their password (TODO v1.1: forced change)."
echo "  3. Create additional CHU Donka staff (ADMIN, DOCTOR, NURSE, etc.) via the"
echo "     /users endpoint or the admin UI."
