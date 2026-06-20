#!/usr/bin/env bash
# =============================================================================
# GuinéeCare Hospital Suite — Restore from backup
# =============================================================================
#
# Usage:
#   bash scripts/restore.sh <backup-file>     # restore specific file
#   bash scripts/restore.sh --latest          # restore latest from db-backup container
#   bash scripts/restore.sh --host <file>     # restore from host file (will copy in)
#
# ⚠️  This script DROPS the existing database and recreates it from backup.
#     Use only for disaster recovery or staging restores.
#
# Pre-requisites:
#   - .env.production exists
#   - postgres container is running
#   - You have confirmed the backup file is valid (bash scripts/backup.sh --verify)
# =============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

ENV_FILE="${ENV_FILE:-.env.production}"
COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn() { echo -e "${YELLOW}[$(date +%H:%M:%S)] WARN:${NC} $*"; }
err()  { echo -e "${RED}[$(date +%H:%M:%S)] ERROR:${NC} $*" >&2; }

if [[ ! -f "$ENV_FILE" ]]; then
    err "Missing $ENV_FILE"
    exit 1
fi
# shellcheck disable=SC1090
set -a; source "$ENV_FILE"; set +a

# Determine backup file
BACKUP_FILE="${2:-}"
if [[ "${1:-}" == "--latest" ]]; then
    BACKUP_FILE=$(docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T db-backup \
        sh -c 'ls -t /backups/*.dump 2>/dev/null | head -1' 2>/dev/null | tr -d '[:space:]')
    if [[ -z "$BACKUP_FILE" ]]; then
        err "No backup found in db-backup container."
        exit 1
    fi
    INSIDE_CONTAINER=true
elif [[ "${1:-}" == "--host" ]]; then
    BACKUP_FILE="${2:-}"
    if [[ -z "$BACKUP_FILE" ]] || [[ ! -f "$BACKUP_FILE" ]]; then
        err "Host file not found: ${BACKUP_FILE:-<missing>}"
        exit 1
    fi
    INSIDE_CONTAINER=false
elif [[ -n "${1:-}" ]]; then
    BACKUP_FILE="$1"
    INSIDE_CONTAINER=true   # assume path inside container
else
    err "Usage: bash scripts/restore.sh <backup-file> | --latest | --host <file>"
    exit 2
fi

# Confirmation prompt (interactive shells only)
if [[ -t 0 ]]; then
    warn "About to DROP and RESTORE database from: $BACKUP_FILE"
    warn "This will permanently delete the current database contents."
    read -rp "Type 'CONFIRM' to proceed: " ans
    if [[ "$ans" != "CONFIRM" ]]; then
        log "Aborted."
        exit 0
    fi
fi

log "Stopping backend (avoid writes during restore)…"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" stop backend

log "Dropping and recreating guineecare database…"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T postgres \
    psql -U guineecare -d postgres <<EOF
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='guineecare' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS guineecare;
CREATE DATABASE guineecare OWNER guineecare;
EOF

if [[ "$INSIDE_CONTAINER" == true ]]; then
    log "Restoring from container path: $BACKUP_FILE"
    docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T db-backup \
        pg_restore --clean --if-exists --no-owner --no-privileges \
        -d guineecare -U guineecare -h postgres "$BACKUP_FILE"
else
    log "Restoring from host file: $BACKUP_FILE"
    cat "$BACKUP_FILE" | docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T \
        postgres pg_restore --clean --if-exists --no-owner --no-privileges \
        -d guineecare -U guineecare
fi

log "Running Alembic migrations to reconcile schema…"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" run --rm --no-deps backend \
    alembic upgrade head

log "Restarting backend…"
docker compose $COMPOSE_FILES --env-file "$ENV_FILE" up -d backend

log ""
log "✓ Restore complete."
log "  Verify with: curl https://\${PUBLIC_URL}/health"
