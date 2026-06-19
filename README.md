# GuinéeCare Hospital Suite

Plateforme hospitalière complète pour la Guinée, inspirée des meilleurs SIH modernes : dossier patient informatisé, maternité, urgences, hospitalisation, pharmacie, laboratoire, imagerie, facturation, bloc opératoire, RH, qualité, reporting national et architecture technique industrielle.

**Version actuelle :** `v0.4.0` — Pages admin + RBAC hardening + bug fixes backend

## Objectif

Construire une suite hospitalière modulaire, sécurisée, multi-hôpitaux et interopérable, capable de servir un hôpital pilote puis un déploiement régional et national.

## Stack technique

- **Backend** : FastAPI 0.115, Python 3.12, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Frontend** : React 18, TypeScript, Vite, Tailwind CSS
- **Base de données** : PostgreSQL 16 (production) / SQLite (dev/test)
- **Cache / jobs** : Redis 7 + Celery (prévu)
- **Auth** : JWT + RBAC + multi-tenant RLS
- **Rate limiting** : slowapi (5 logins/min sur `/auth/login`)
- **Déploiement** : Docker Compose (pilote) → Kubernetes (national)

## Démarrage rapide

### Prérequis
- Python 3.12+ avec venv
- Node.js 20+
- npm ou bun

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Démarrer avec seed de démo
DATABASE_URL="sqlite:///./dev_guineecare.db" \
AUTH_SECRET="dev-secret-key-2025" \
ENVIRONMENT=local \
SEED_DEMO_DATA=true \
CORS_ORIGINS='["*"]' \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Le backend démarre sur http://localhost:8000 — documentation OpenAPI sur http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env.local
npm run dev
```

Le frontend démarre sur http://localhost:5173

### Script tout-en-un

```bash
bash /home/z/my-project/scripts/start_dev.sh
```

## Comptes de test

| Email | Mot de passe | Rôle | Périmètre |
|---|---|---|---|
| `admin@guineecare.com` | `admin123` | SUPER_ADMIN | National (tous les établissements) |
| `admin.donka@chu-donka.gn` | `admin123` | ADMIN | CHU Donka (Conakry) |
| `dr.diallo@chu-donka.gn` | `doctor123` | DOCTOR | CHU Donka |
| `inf.konde@chu-donka.gn` | `nurse123` | NURSE | CHU Donka |
| `pharma.dubois@chu-donka.gn` | `pharma123` | PHARMACIST | CHU Donka |
| `lab.sakouv@chu-donka.gn` | `labtech123` | LAB_TECH | CHU Donka |
| `sf.bangoura@chu-donka.gn` | `sagefemme123` | MIDWIFE | CHU Donka |
| `caisse.tamba@chu-ignace.gn` | `caisse123` | CASHIER | CHU Ignace Deen |

## Modules fonctionnels

### Soins
- Dashboard, Patients, Admissions
- Urgences (file d'attente, triage, orientation)
- Hospitalisation (lits, séjour, bed-board)
- Maternité (grossesses, accouchements, CPoN)
- Bloc opératoire, Imagerie, Laboratoire, Pharmacie

### Administration
- Facturation & Caisse
- Personnel (RH, contrats, gardes, congés)
- Qualité (événements indésirables, audits)
- Journal d'activité

### Système (v0.4.0 — NOUVEAU)
- **Utilisateurs** : CRUD, activation/désactivation, filtre par rôle
- **Rôles & Permissions** : matrice RBAC visuelle, création de rôles
- **Établissements** : gestion multi-hôpitaux
- **Départements** : unités fonctionnelles

### National
- Pilotage national (KPI agrégés)
- Reporting (statistiques sanitaires)

## Tests & CI

### Tests locaux

```bash
# Backend pytest
cd backend && pytest -q

# E2E pages admin (31 tests)
python /home/z/my-project/scripts/verify_admin_pages.py
```

### CI GitHub Actions

3 workflows sur chaque push/PR :
- `backend-tests.yml` — pytest backend
- `frontend-build.yml` — build Vite
- `e2e-admin-pages.yml` — 31 tests E2E pages admin + RBAC

## Architecture

### Multi-tenant RLS

Chaque table métier possède une colonne `facility_id`. Le helper `tenant_query(db, Model, current_user)` filtre automatiquement les enregistrements selon l'établissement du user connecté. Le SUPER_ADMIN voit tous les établissements.

### RBAC

8 rôles prédéfinis (SUPER_ADMIN, ADMIN, DOCTOR, NURSE, PHARMACIST, LAB_TECH, MIDWIFE, CASHIER). 41 permissions granulaires regroupées par module. Les endpoints FastAPI utilisent `require_permission("code")` ou `require_role("ROLE1", "ROLE2")`. SUPER_ADMIN et ADMIN bypass toutes les permissions.

### Authentification

JWT signé avec `AUTH_SECRET`. Claims : `sub` (user_id), `facility_id`, `role`. Rate limiter : 5 tentatives de login / minute par IP.

## Roadmap

- v0.5 — Tests Playwright (parcours UI complets)
- v0.6 — Monitoring Prometheus + Grafana
- v0.7 — Audit sécurité OWASP ZAP
- v1.0 — Déploiement pilote CHU Donka

## Organisation documentaire

- `docs/00_CAHIER_DES_CHARGES_GLOBAL.md` — cahier des charges
- `docs/01_MODULES_COMPLETS_HOPITAUX.md` — modules détaillés
- `docs/lots/lot-01-...md` à `lot-16-...md` — 16 lots fonctionnels
- `docs/architecture/architecture-technique-cible.md`
- `docs/roadmap/roadmap-mvp.md`
- `docs/deploiement/deploiement-national.md`
- `docs/formation/conduite-du-changement.md`

## Lots fonctionnels

- Lot 01 — Socle technique, sécurité, référentiels
- Lot 02 — Patient, admission, rendez-vous, file d'attente
- Lot 03 — DPI clinique
- Lot 04 — Maternité, grossesse, accouchement, néonatalogie
- Lot 05 — Urgences, triage et prise en charge immédiate
- Lot 06 — Hospitalisation, lits, soins et prescriptions
- Lot 07 — Pharmacie, stock, médicaments et dispensation
- Lot 08 — Laboratoire, prélèvements, analyses et résultats
- Lot 09 — Imagerie médicale, radiologie et comptes rendus
- Lot 10 — Facturation hospitalière, caisse, paiements
- Lot 11 — Bloc opératoire, anesthésie, chirurgie, stérilisation
- Lot 12 — RH hospitalières, plannings, gardes, habilitations
- Lot 13 — Qualité, risques, événements indésirables
- Lot 14 — Reporting national, statistiques sanitaires, interopérabilité
- Lot 15 — Architecture technique, DevOps, sécurité, déploiement
- Lot 16 — Roadmap, MVP, budget, équipe, cahier des charges final

## Licence

Projet privé — © GuinéeCare 2026
