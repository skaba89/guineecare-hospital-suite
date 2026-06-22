#!/bin/bash
# Render start script — migrations + seed + uvicorn
# Utilisé par render.yaml pour éviter les problèmes de YAML multi-lignes.

set -e

echo "=== GuinéeCare Render Start ==="

# 1. Migrations Alembic
echo ">>> Running Alembic migrations..."
alembic upgrade head
echo ">>> Migrations OK"

# 2. Seed données de démo (si SEED_DEMO_DATA=true)
if [ "${SEED_DEMO_DATA:-true}" = "true" ] || [ "${SEED_DEMO_DATA}" = "1" ] || [ "${SEED_DEMO_DATA}" = "yes" ]; then
  echo ">>> Seeding demo data..."
  python -c "from app.db.seed import run_seed; run_seed()"
  echo ">>> Seed OK"
else
  echo ">>> SEED_DEMO_DATA=false, skipping seed"
fi

# 3. Démarrer uvicorn
echo ">>> Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
