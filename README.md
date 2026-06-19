# GuinéeCare Hospital Suite

[![Backend tests](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/backend-tests.yml)
[![Frontend build](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/frontend-build.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/frontend-build.yml)
[![E2E admin pages](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/e2e-admin-pages.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/e2e-admin-pages.yml)
[![E2E Playwright](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/e2e-playwright.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/e2e-playwright.yml)
[![Version](https://img.shields.io/badge/version-v0.5.0-blue.svg)](https://github.com/skaba89/guineecare-hospital-suite/releases)
[![License](https://img.shields.io/badge/license-Private-red.svg)](#licence)

Plateforme hospitalière complète pour la Guinée, inspirée des meilleurs SIH modernes : dossier patient informatisé, maternité, urgences, hospitalisation, pharmacie, laboratoire, imagerie, facturation, bloc opératoire, RH, qualité, reporting national et architecture technique industrielle.

**Version actuelle :** `v0.5.0` — Tests Playwright + CI/CD complet + Vite proxy

## Objectif

Construire une suite hospitalière modulaire, sécurisée, multi-hôpitaux et interopérable, capable de servir un hôpital pilote puis un déploiement régional et national. La plateforme vise à remplacer les systèmes papier encore largement utilisés dans les établissements de santé guinéens, en offrant une solution numérique adaptée au contexte local (connectivité limitée, formation continue, multilinguisme).

## Stack technique

- **Backend** : FastAPI 0.115, Python 3.12, SQLAlchemy 2.0, Alembic, Pydantic v2
- **Frontend** : React 18, TypeScript, Vite, Tailwind CSS
- **Base de données** : PostgreSQL 16 (production) / SQLite (dev/test)
- **Cache / jobs** : Redis 7 + Celery (prévu)
- **Auth** : JWT + RBAC + multi-tenant RLS
- **Rate limiting** : slowapi (5 logins/min sur `/auth/login` en production, désactivé en dev/test)
- **Tests E2E** : Playwright 1.61 (12 parcours UI critiques)
- **CI/CD** : GitHub Actions (4 workflows : backend-tests, frontend-build, e2e-admin-pages, e2e-playwright)
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

# Démarrer avec seed de démo (20 établissements, 38 users, 50 patients)
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
npm run dev
```

Le frontend démarre sur http://localhost:5173 — le proxy Vite `/api` forward automatiquement vers `http://localhost:8000`.

> Plus besoin de `VITE_API_BASE_URL` — le proxy Vite est configuré dans `vite.config.ts`.

### Script tout-en-un

```bash
bash scripts/start_dev.sh  # démarre backend + frontend
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
- **Dashboard** — KPI temps réel (patients, lits occupés, urgences en cours)
- **Patients** — DPI complet, recherche, création auto-générée (`PAT-YYYYMMDDHHMMSS`)
- **Admissions** — admissions programmées et urgentes
- **Urgences** — file d'attente, triage (niveaux 1-5), orientation
- **Hospitalisation** — lits, séjours, bed-board par établissement
- **Maternité** — grossesses, accouchements, CPoN
- **Bloc opératoire** — programmation, comptes rendus
- **Imagerie** — demandes, résultats
- **Laboratoire** — prélèvements, analyses, validation
- **Pharmacie** — stock, dispensation

### Administration
- **Facturation & Caisse** — factures, paiements
- **Personnel** — RH, contrats, gardes, congés
- **Qualité** — événements indésirables, audits
- **Journal d'activité** — traçabilité complète

### Système (v0.4.0+)
- **Utilisateurs** : CRUD, activation/désactivation, filtre par rôle
- **Rôles & Permissions** : matrice RBAC visuelle, création de rôles
- **Établissements** : gestion multi-hôpitaux (20 établissements seedés)
- **Départements** : unités fonctionnelles

### National
- **Pilotage national** — KPI agrégés sur tous les établissements
- **Reporting** — statistiques sanitaires, alertes épidémiques

## Tests & CI

### Tests locaux

```bash
# Backend pytest (84 tests, ~25s)
cd backend && pytest -q

# E2E pages admin (31 tests API)
python scripts/verify_admin_pages.py

# E2E Playwright (12 parcours UI)
cd frontend
npx playwright install chromium  # une seule fois
npm run test:e2e                 # lance les tests
npm run test:e2e:ui              # mode interactif
npm run test:e2e:report          # ouvre le rapport HTML
```

### CI GitHub Actions

4 workflows sur chaque push/PR sur `main` :

| Workflow | Description | Durée |
|---|---|---|
| `backend-tests.yml` | pytest backend (84 tests) + cache pip | ~1 min |
| `frontend-build.yml` | TypeCheck + build Vite | ~1 min |
| `e2e-admin-pages.yml` | 31 tests API E2E (login, RBAC, multi-tenant) | ~2 min |
| `e2e-playwright.yml` | 12 parcours UI Playwright avec seed | ~3 min |

Les artifacts (rapports HTML, traces, screenshots) sont téléversés sur chaque run.

## Architecture

### Multi-tenant RLS (Row-Level Security)

Chaque table métier possède une colonne `facility_id`. Le helper `tenant_query(db, Model, current_user)` filtre automatiquement les enregistrements selon l'établissement du user connecté. Le SUPER_ADMIN voit tous les établissements.

```python
# Exemple dans un route FastAPI
@router.get("/patients")
def list_patients(db: Session = Depends(get_db), user = Depends(get_current_user)):
    query = tenant_query(db, Patient, user)  # filtre par facility_id
    return paginate(query)
```

### RBAC granulaire

8 rôles prédéfinis (SUPER_ADMIN, ADMIN, DOCTOR, NURSE, PHARMACIST, LAB_TECH, MIDWIFE, CASHIER). 41 permissions granulaires regroupées par module. Les endpoints FastAPI utilisent `require_permission("code")` ou `require_role("ROLE1", "ROLE2")`. SUPER_ADMIN et ADMIN bypass toutes les permissions.

Côté frontend, `<ProtectedRoute permission="patient.read">` ou `<ProtectedRoute roles={["SUPER_ADMIN", "ADMIN"]}>` protège chaque route React. La visibilité des liens sidebar est gérée par `useNavVisibility()`.

### Authentification

JWT signé avec `AUTH_SECRET` (HS256). Claims : `sub` (user_id), `facility_id`, `role`. Durée : 60 minutes par défaut. Rate limiter slowapi : 5 tentatives de login / minute par IP en production, désactivé en `ENVIRONMENT=local|test|dev` pour faciliter les tests.

### Proxy Vite (v0.5.0+)

Le frontend Vite proxy les appels `/api/*` vers le backend FastAPI. Plus besoin de configurer `VITE_API_BASE_URL` — tout fonctionne en local via `http://localhost:5173`.

```ts
// vite.config.ts
server: {
  proxy: {
    "/api": {
      target: "http://127.0.0.1:8000",
      changeOrigin: true,
    },
  },
}
```

## Roadmap

- ✅ v0.1 — Socle technique + auth + RBAC
- ✅ v0.2 — Modules métiers (patients, urgences, hospitalisation, pharmacie, labo, imagerie, etc.)
- ✅ v0.3 — Multi-tenant RLS + 84 tests backend + 109 tests E2E API
- ✅ v0.4 — Pages admin (Users, RBAC, Facilities, Departments) + bug fixes
- ✅ v0.5 — Tests Playwright + CI/CD GitHub Actions (4 workflows) + Vite proxy
- 🔜 v0.6 — Monitoring Prometheus + Grafana
- 🔜 v0.7 — Audit sécurité OWASP ZAP
- 🔜 v0.8 — Tests de charge (Locust)
- 🔜 v0.9 — Documentation OpenAPI complète + Postman collection
- 🎯 v1.0 — Déploiement pilote CHU Donka

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

## Contribution

1. Fork le projet
2. Créer une branche : `git checkout -b feat/ma-feature`
3. Commit : `git commit -m "feat: ma feature"`
4. Push : `git push origin feat/ma-feature`
5. Ouvrir une Pull Request vers `main`

Les PR déclenchent automatiquement les 4 workflows CI. Tous doivent passer avant merge.

### Conventions de commit (Angular)

- `feat:` nouvelle fonctionnalité
- `fix:` correction de bug
- `docs:` documentation
- `test:` tests
- `refactor:` refactor sans changement fonctionnel
- `chore:` maintenance
- `release:` nouvelle version

## Licence

Projet privé — © GuinéeCare 2026
