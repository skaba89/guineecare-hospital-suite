# Installation Locale Développeur — GuinéeCare Hospital Suite

**Version :** v2.3.0 (Phase 8)
**Public :** Développeurs qui veulent contribuer ou tester localement
**Durée :** 15-20 min

## Prérequis

| Outil | Version | Vérifier |
|-------|---------|----------|
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| Git | 2.40+ | `git --version` |
| Docker (optionnel) | 24+ | `docker --version` |

## Option A — Développement sans Docker (recommandé pour dev)

### 1. Cloner le dépôt

```bash
git clone https://github.com/skaba89/guineecare-hospital-suite.git
cd guineecare-hospital-suite
```

### 2. Configuration environnement

```bash
cp .env.example .env
# Éditer .env si besoin (les valeurs par défaut fonctionnent pour le dev local)
```

### 3. Backend

```bash
cd backend

# Créer un venv Python 3.12
python3.12 -m venv .venv
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt -r requirements-dev.txt

# Démarrer la DB SQLite (création automatique au premier démarrage)
# + seed données démo (50 patients, 8 comptes)
DATABASE_URL="sqlite:///./dev_guinecare.db" \
AUTH_SECRET="dev-secret-key-2025" \
ENVIRONMENT=local \
SEED_DEMO_DATA=true \
python -c "
from app.db.base import Base
from app.db.session import engine
# Importer tous les modèles
import app.modules.facilities.models
import app.modules.patients.models
import app.modules.users.models
# ... (voir backend/render_start.sh pour la liste complète)
Base.metadata.create_all(bind=engine, checkfirst=True)
print('✅ Tables créées')
"

# Seed RBAC + données démo
python -c "
from app.modules.rbac.seed import seed_rbac
from app.db.session import SessionLocal
db = SessionLocal()
seed_rbac(db)
db.close()
print('✅ RBAC seedé')
"
python -c "from app.db.seed import run_seed; run_seed()"

# Lancer le serveur de dev (hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend accessible sur : `http://localhost:8000`
- API : `http://localhost:8000/api/v1`
- Swagger UI : `http://localhost:8000/docs`
- Health : `http://localhost:8000/health`

### 4. Frontend

```bash
cd ../frontend

# Installer les dépendances
npm ci

# Lancer le serveur de dev Vite (hot reload)
npm run dev
```

Frontend accessible sur : `http://localhost:5173`

Le proxy Vite redirige `/api/*` vers `http://localhost:8000` (voir `vite.config.ts`).

### 5. Login test

Comptes démo (créés par le seed) :

| Email | Mot de passe | Rôle |
|-------|--------------|------|
| `admin@guineecare.com` | `admin123` | SUPER_ADMIN |
| `dr.diallo@chu-donka.gn` | `doctor123` | DOCTOR |
| `inf.konde@chu-donka.gn` | `nurse123` | NURSE |
| `sf.bah@chu-donka.gn` | `midwife123` | MIDWIFE |
| `ph.cisse@chu-donka.gn` | `pharma123` | PHARMACIST |
| `lab.sow@chu-donka.gn` | `lab123` | LAB_TECH |
| `ca.diallo@chu-donka.gn` | `cashier123` | CASHIER |
| `admin.facility@chu-donka.gn` | `admin123` | ADMIN |

### 6. Tests

```bash
# Backend
cd backend
source .venv/bin/activate
python -m pytest --tb=short -q

# Frontend
cd ../frontend
npx tsc --noEmit
npm run build
```

## Option B — Développement avec Docker

### 1. Cloner + configurer

```bash
git clone https://github.com/skaba89/guineecare-hospital-suite.git
cd guineecare-hospital-suite
cp .env.example .env
```

### 2. Démarrer tous les services

```bash
docker compose up -d --build
```

Services démarrés :
- **nginx** : `http://localhost` (reverse proxy)
- **backend** : `http://localhost:8000` (interne)
- **frontend** : `http://localhost:8080` (interne)
- **postgres** : `localhost:5432` (interne)
- **redis** : `localhost:6379` (interne)
- **db-backup** : cron backup quotidien

### 3. Vérifier

```bash
# Health
curl http://localhost/health
# Attendu : {"status":"ok",...}

# Login
bash scripts/verify-demo.sh
```

### 4. Logs

```bash
# Tous les services
docker compose logs -f

# Backend seulement
docker compose logs -f backend

# Frontend seulement
docker compose logs -f frontend
```

### 5. Arrêter

```bash
docker compose down
# Pour supprimer les volumes (DB, backups) :
docker compose down -v
```

## Option C — Démo Render (gratuit, sans installation)

1. Aller sur `https://guineecare.onrender.com`
2. Login avec `admin@guineecare.com` / `admin123`
3. ⚠️ Données réinitialisées toutes les 24-48h (free tier)

## Structure du projet

```
guineecare-hospital-suite/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── main.py         # Point d'entrée
│   │   ├── core/           # Config, sécurité, tenant
│   │   ├── db/             # Base, session, seed
│   │   └── modules/        # 33 modules métier
│   ├── alembic/versions/   # 23 migrations
│   ├── tests/              # 512 tests pytest
│   ├── Dockerfile
│   └── render_start.sh
├── frontend/               # SPA React/Vite
│   ├── src/
│   │   ├── pages/          # 32 pages
│   │   ├── components/     # Composants réutilisables
│   │   ├── layout/         # Sidebar, AppLayout
│   │   └── i18n/           # FR/EN
│   ├── Dockerfile
│   └── frontend-nginx.conf
├── mobile/                 # App React Native (Expo)
├── docs/                   # Documentation
├── scripts/                # Scripts déploiement
├── docker-compose.yml      # Dev
├── docker-compose.prod.yml # Production
├── render.yaml             # Démo Render
└── .env.example            # Template dev
```

## Problèmes fréquents

### "psycopg2 build error" (Python 3.14)

Python 3.14 n'a pas encore de wheel psycopg2 précompilée. Utiliser Python 3.12 :
```bash
pyenv install 3.12.13
pyenv local 3.12.13
```

### "Port 8000 déjà utilisé"

```bash
# Trouver le processus
lsof -i :8000
# Tuer
kill -9 <PID>
# Ou utiliser un autre port
uvicorn app.main:app --port 8001
```

### "Module not found" après pull

```bash
cd backend && source .venv/bin/activate
pip install -r requirements.txt
```

### Frontend ne se connecte pas au backend

Vérifier `vite.config.ts` — le proxy doit pointer vers `http://localhost:8000` :
```typescript
proxy: {
  "/api": {
    target: "http://localhost:8000",
    changeOrigin: true,
  },
}
```

### Alembic : "Can't locate revision"

```bash
cd backend
rm -f dev_guineecare.db  # SQLite — repartir de zéro
alembic upgrade head
```

## Voir aussi

- `docs/deploiement/onboarding-nouvel-hopital.md` — Installation production
- `docs/deploiement/guide-render-neon.md` — Démo Render + Neon
- `docs/deploiement/guide-vps-rapide.md` — VPS en 30 min
- `docs/developpement/lancement-local.md` — Guide dev détaillé
