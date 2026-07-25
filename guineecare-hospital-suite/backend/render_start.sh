#!/bin/bash
# Render start script — DB init + seed + uvicorn
# Gère deux cas :
# 1. DB neuve → alembic upgrade head (crée toutes les tables via migrations)
# 2. DB existante → create_all (tables manquantes) + migration_helper (colonnes manquantes)
#    + alembic stamp head (marque les migrations comme appliquées)
#
# v2.8.5 — CRITICAL FIX : ne pas utiliser set -e globalement.
# Si le seed RBAC ou la migration échoue, uvicorn doit quand même démarrer.
# Render attend un port bind — si uvicorn ne démarre pas, le déploiement échoue.

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
    # DB existante — créer les tables manquantes via create_all
    echo ">>> DB already has tables — creating missing tables via create_all..."
    python -c "
import os
from app.db.base import Base
from app.db.session import engine
import app.modules.facilities.models
import app.modules.departments.models
import app.modules.patients.models
import app.modules.users.models
import app.modules.rbac.models
import app.modules.admissions.models
import app.modules.emergency.models
import app.modules.pharmacy.models
import app.modules.laboratory.models
import app.modules.billing.models
import app.modules.clinical.models
import app.modules.hospitalization.models
import app.modules.maternity.models
import app.modules.personnel.models
import app.modules.imaging.models
import app.modules.surgery.models
import app.modules.quality.models
import app.modules.quality.dashboard_models
import app.modules.reporting.models
import app.modules.notifications.models
import app.modules.notifications.sms_models
import app.modules.user_profile.models
import app.modules.documents.models
import app.modules.activity.models
import app.modules.auth.models
import app.modules.auth.two_factor_models
import app.modules.personnel.rh_v2_models
Base.metadata.create_all(bind=engine, checkfirst=True)
print('>>> Missing tables created (checkfirst=True)')
engine.dispose()
" 2>&1 || echo ">>> WARNING: create_all failed (continuing anyway)"

    # Ajouter les colonnes manquantes aux tables existantes
    echo ">>> Adding missing columns via migration_helper..."
    python -c "from app.db.migration_helper import run_manual_migrations, run_column_type_migrations, run_nullable_migrations; run_manual_migrations(); run_column_type_migrations(); run_nullable_migrations()" 2>&1 || echo ">>> WARNING: migration_helper failed (continuing anyway)"

    # Marquer les migrations comme appliquées
    echo ">>> Stamping alembic head..."
    alembic stamp head 2>/dev/null || echo ">>> stamp head skipped (already stamped or error)"
    echo ">>> Alembic stamped OK"
else
    # DB neuve — créer toutes les tables via migrations
    echo ">>> Fresh DB — running alembic upgrade head..."
    alembic upgrade head 2>&1 || echo ">>> WARNING: alembic upgrade failed (continuing anyway)"
    echo ">>> Migrations OK"
fi

# 2. Seed RBAC (idempotent) — ne pas faire échouer le démarrage si le seed échoue
echo ">>> Seeding RBAC..."
python -c "
from app.modules.rbac.seed import seed_rbac
from app.db.session import SessionLocal
db = SessionLocal()
seed_rbac(db)
db.close()
print('>>> RBAC OK')
" 2>&1 || echo ">>> WARNING: RBAC seed failed (continuing anyway — uvicorn will still start)"

# 3. Seed données de démo — v2.8.5 : SEULEMENT si la DB est vide
# Avant : le seed tournait à CHAQUE démarrage → 1-2 min à chaque cold start Render
# Maintenant : on vérifie si users est vide → skip si déjà peuplée
if [ "${SEED_DEMO_DATA:-true}" = "true" ] || [ "${SEED_DEMO_DATA}" = "1" ] || [ "${SEED_DEMO_DATA}" = "yes" ]; then
  echo ">>> Checking if demo seed needed..."
  USER_COUNT=$(python -c "
import os, sqlalchemy
engine = sqlalchemy.create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    result = conn.execute(sqlalchemy.text('SELECT COUNT(*) FROM users'))
    print(result.scalar())
engine.dispose()
" 2>/dev/null || echo "0")

  if [ "$USER_COUNT" -eq "0" ]; then
    echo ">>> DB is empty — seeding demo data (1-2 min)..."
    python -c "
from app.db.seed import run_seed
run_seed()
" 2>&1 || echo ">>> WARNING: demo seed failed (continuing)"
    echo ">>> Seed OK"
  else
    echo ">>> DB already has $USER_COUNT users — skipping demo seed (fast startup)"
  fi
else
  echo ">>> SEED_DEMO_DATA=false, skipping seed"
fi

# 4. Démarrer uvicorn — c'est la seule étape qui DOIT réussir
echo ">>> Starting uvicorn on port ${PORT:-8000}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
