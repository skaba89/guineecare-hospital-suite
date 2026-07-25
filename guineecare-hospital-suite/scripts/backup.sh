#!/bin/bash
# GuinéeCare — Script de sauvegarde automatique PostgreSQL
# Usage :
#   ./backup.sh [DATABASE_URL]            # créer un backup
#   ./backup.sh --verify <backup_file>    # vérifier un backup (pg_restore --list)
#   ./backup.sh --list <backup_file>      # lister le contenu d'un backup
#
# Cron recommandé : 0 2 * * * /path/to/backup.sh
set -e

DB_URL="${DATABASE_URL:-}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# ─── Mode --verify / --list ─────────────────────────────────────────────────
# Ces modes ne créent pas de backup : ils inspectent un fichier existant.
# Le test test_backup_script_has_verify_mode vérifie leur présence.
if [[ "${1:-}" == "--verify" || "${1:-}" == "--list" ]]; then
  MODE="$1"
  BACKUP_FILE="${2:-}"
  if [[ -z "$BACKUP_FILE" ]]; then
    echo "Usage: $0 $MODE <backup_file>"
    exit 1
  fi
  if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "ERROR: File not found: $BACKUP_FILE"
    exit 1
  fi
  echo "[$(date -Is)] $MODE → $BACKUP_FILE"
  # pg_restore --list affiche le catalogue du dump sans toucher à la DB.
  # --verify utilise --list en mode verbeux pour valider l'intégrité du fichier.
  if [[ "$MODE" == "--verify" ]]; then
    pg_restore --list "$BACKUP_FILE" >/dev/null && echo "OK: backup valide"
  else
    pg_restore --list "$BACKUP_FILE"
  fi
  exit $?
fi

# ─── Mode backup (par défaut) ───────────────────────────────────────────────
DB_URL="${1:-$DB_URL}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/guineecare_$TIMESTAMP.dump"

mkdir -p "$BACKUP_DIR"

echo "[$(date -Is)] Starting backup → $BACKUP_FILE"

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL not set"
  exit 1
fi

# Backup avec pg_dump format custom (compression native)
pg_dump "$DB_URL" -Fc -f "$BACKUP_FILE"

# Vérifier que le fichier n'est pas vide
SIZE=$(stat -f%z "$BACKUP_FILE" 2>/dev/null || stat -c%s "$BACKUP_FILE" 2>/dev/null || echo 0)
if [ "$SIZE" -lt 100 ]; then
  echo "ERROR: Backup file too small ($SIZE bytes) — likely failed"
  rm -f "$BACKUP_FILE"
  exit 1
fi

# Validation post-backup : pg_restore --list doit réussir à lire le dump.
if ! pg_restore --list "$BACKUP_FILE" >/dev/null 2>&1; then
  echo "ERROR: Backup file appears corrupted (pg_restore --list failed)"
  rm -f "$BACKUP_FILE"
  exit 1
fi

echo "[$(date -Is)] Backup OK — $SIZE bytes (verified)"

# Rétention : supprimer les backups plus anciens que RETENTION_DAYS
find "$BACKUP_DIR" -name "guineecare_*.dump" -mtime +${RETENTION_DAYS} -delete
echo "[$(date -Is)] Retention: deleted backups older than ${RETENTION_DAYS} days"

# Lister les backups restants
echo "--- Available backups ---"
ls -lh "$BACKUP_DIR"/guineecare_*.dump 2>/dev/null | tail -5
