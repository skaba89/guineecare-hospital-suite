#!/usr/bin/env bash
# =============================================================================
# GuinéeCare Hospital Suite — Backup / restore scripts
# =============================================================================
#
# Backup:
#   bash scripts/backup.sh                  # manual backup now
#   bash scripts/backup.sh --verify         # verify the latest backup file
#   bash scripts/backup.sh --list           # list existing backups
#
# Restore:
#   bash scripts/restore.sh <backup-file>   # restore from file
#   bash scripts/restore.sh --latest        # restore from latest backup
#
# These are wrappers around the db-backup container which already runs nightly
# at 02:00 UTC. Use them for manual point-in-time backups or disaster recovery.
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

BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

TS="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$BACKUP_DIR/guineecare_${TS}.dump"

case "${1:-}" in
    --list)
        log "Existing backups:"
        docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T db-backup \
            ls -lh /backups 2>/dev/null || ls -lh "$BACKUP_DIR"
        ;;

    --verify)
        LATEST=$(docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T db-backup \
            sh -c 'ls -t /backups/*.dump 2>/dev/null | head -1' 2>/dev/null | tr -d '[:space:]')
        if [[ -z "$LATEST" ]]; then
            err "No backup found in db-backup container."
            exit 1
        fi
        log "Verifying: $LATEST"
        docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T db-backup \
            pg_restore --list "$LATEST" >/dev/null \
            && log "✓ Backup file is valid (pg_restore --list succeeded)" \
            || { err "Backup file is corrupted."; exit 1; }
        # Also check size ≥ 1 KB
        SIZE=$(docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T db-backup \
            stat -c%s "$LATEST")
        if [[ "$SIZE" -lt 1024 ]]; then
            err "Backup too small (${SIZE} bytes) — likely empty."
            exit 1
        fi
        log "✓ Backup size: ${SIZE} bytes"
        ;;

    "" | --now)
        log "Manual backup → $BACKUP_FILE"
        # Stream pg_dump from the db-backup container to host file
        docker compose $COMPOSE_FILES --env-file "$ENV_FILE" exec -T db-backup \
            pg_dump -Fc > "$BACKUP_FILE"
        SIZE=$(stat -c%s "$BACKUP_FILE")
        log "✓ Backup complete: $BACKUP_FILE (${SIZE} bytes)"
        log ""
        log "To restore:"
        log "  bash scripts/restore.sh $BACKUP_FILE"
        ;;

    *)
        err "Unknown argument: $1"
        echo "Usage: bash scripts/backup.sh [--list|--verify|--now]"
        exit 2
        ;;
esac
