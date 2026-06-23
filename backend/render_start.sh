#!/bin/bash
# Render start script — DB init + seed + uvicorn
# Gère deux cas :
# 1. DB neuve → alembic upgrade head (crée toutes les tables via migrations)
# 2. DB existante (tables déjà créées par init_db) → alembic stamp head (marque comme à jour)
set -e

echo "=== GuinéeCare Render Start ==="

# 1. Détecter si la DB a déjà des tables
TABLE_COUNT=$(python -c "
import os, sqlalchemy
engine = sqlalchemy.create_engine(os.environ['DATABASE_URL'])
inspector = sqlalchemy.inspect(engine)
tables = inspector.get_table_names()
print(len(tables))
engine.dispose()
" 2>/dev/null || echo "0")

echo ">>> Detected $TABLE_COUNT existing tables"

if [ "$TABLE_COUNT" -gt "0" ]; then
    # DB existante — marquer les migrations comme appliquées
    echo ">>> DB already has tables — running alembic stamp head..."
    alembic stamp head 2>/dev/null || echo ">>> stamp head skipped (already stamped)"
    echo ">>> Alembic stamped OK"
else
    # DB neuve — créer toutes les tables
    echo ">>> Fresh DB — running alembic upgrade head..."
    alembic upgrade head
    echo ">>> Migrations OK"
fi

# 2. Seed RBAC (idempotent)
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
  python -c "from app.db.seed import run_seed; run_seed()" 2>/dev/null || echo ">>> Seed skipped (may already exist)"
  echo ">>> Seed OK"
else
  echo ">>> SEED_DEMO_DATA=false, skipping seed"
fi

# 4. Démarrer uvicorn
echo ">>> Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
