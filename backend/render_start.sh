#!/bin/bash
# Render start script — migrations + seed + uvicorn
set -e

echo "=== GuinéeCare Render Start ==="

# 1. Migrations Alembic (chaîne réparée v1.8.0)
echo ">>> Running Alembic migrations..."
alembic upgrade head
echo ">>> Migrations OK"

# 2. Seed RBAC
echo ">>> Seeding RBAC..."
python -c "
from app.modules.rbac.seed import seed_rbac
from app.db.session import SessionLocal
db = SessionLocal()
seed_rbac(db)
db.close()
print('>>> RBAC OK')
"

# 3. Seed données de démo
if [ "${SEED_DEMO_DATA:-true}" = "true" ] || [ "${SEED_DEMO_DATA}" = "1" ] || [ "${SEED_DEMO_DATA}" = "yes" ]; then
  echo ">>> Seeding demo data..."
  python -c "from app.db.seed import run_seed; run_seed()"
  echo ">>> Seed OK"
else
  echo ">>> SEED_DEMO_DATA=false, skipping seed"
fi

# 4. Démarrer uvicorn
echo ">>> Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
