#!/bin/bash
# GuinéeCare — Script de sauvegarde automatique PostgreSQL
# Usage : ./backup.sh [DATABASE_URL]
# Cron recommandé : 0 2 * * * /path/to/backup.sh
set -e

DB_URL="${1:-$DATABASE_URL}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
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

echo "[$(date -Is)] Backup OK — $SIZE bytes"

# Rétention : supprimer les backups plus anciens que RETENTION_DAYS
find "$BACKUP_DIR" -name "guineecare_*.dump" -mtime +${RETENTION_DAYS} -delete
echo "[$(date -Is)] Retention: deleted backups older than ${RETENTION_DAYS} days"

# Lister les backups restants
echo "--- Available backups ---"
ls -lh "$BACKUP_DIR"/guineecare_*.dump 2>/dev/null | tail -5
