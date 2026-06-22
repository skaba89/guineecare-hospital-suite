#!/bin/bash
# Render start script — init DB + seed + uvicorn
# Utilisé par render.yaml pour éviter les problèmes de YAML multi-lignes.

set -e

echo "=== GuinéeCare Render Start ==="

# 1. Initialiser la DB (create_all + seed RBAC)
# On utilise init_db() au lieu de alembic upgrade head car la chaîne
# de migrations Alembic a des incohérences de naming entre 0009 et 0010.
# init_db() crée toutes les tables via Base.metadata.create_all() — suffisant
# pour un déploiement fresh. Alembic sera utilisé pour les migrations futures.
echo ">>> Initializing database..."
python -c "
from app.db.init_db import init_db
init_db()
print('>>> DB tables created')
from app.modules.rbac.seed import seed_rbac
from app.db.session import SessionLocal
db = SessionLocal()
seed_rbac(db)
print('>>> RBAC seeded')
db.close()
"
echo ">>> DB init OK"

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
