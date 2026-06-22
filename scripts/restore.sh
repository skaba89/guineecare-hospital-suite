#!/bin/bash
# GuinéeCare — Script de restauration PostgreSQL
# Usage : ./restore.sh <backup_file>
set -e

BACKUP_FILE="$1"
DB_URL="${DATABASE_URL:-}"

if [ -z "$BACKUP_FILE" ]; then
  echo "Usage: $0 <backup_file>"
  exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: File not found: $BACKUP_FILE"
  exit 1
fi

if [ -z "$DB_URL" ]; then
  echo "ERROR: DATABASE_URL not set"
  exit 1
fi

echo "[$(date -Is)] Restoring $BACKUP_FILE → $DB_URL"
echo "WARNING: This will DROP existing data. Press Ctrl+C to cancel."
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 0
fi

# Restaurer avec pg_restore (format custom)
pg_restore "$DB_URL" --clean --if-exists --no-owner -d "$DB_URL" < "$BACKUP_FILE"

echo "[$(date -Is)] Restore completed successfully."
