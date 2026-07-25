#!/bin/bash
# GuinéeCare — Script de restauration PostgreSQL
# Usage : ./restore.sh <backup_file>
#
# SECURITY: la restauration est destructive (DROP + recreate).
# Une confirmation explicite est exigée — le test
# test_restore_script_has_confirm_prompt vérifie la présence du marqueur
# "CONFIRM" pour empêcher tout contournement accidentel.
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
echo "CONFIRM required to proceed."

read -p "Type CONFIRM to continue: " user_confirm
if [ "$user_confirm" != "CONFIRM" ]; then
  echo "Aborted (no CONFIRM)."
  exit 0
fi

echo "[$(date -Is)] CONFIRM received — starting restore."

# v2.8.0 — Fix : pg_restore syntaxe correcte.
# pg_restore prend le backup en stdin (ou fichier) et -d prend le nom de DB.
# Avec une URL de connexion, on utilise --dbname="$DB_URL" (psql-compatible).
pg_restore --clean --if-exists --no-owner --dbname="$DB_URL" < "$BACKUP_FILE"

echo "[$(date -Is)] Restore completed successfully."
