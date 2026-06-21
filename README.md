# GuinéeCare Hospital Suite

[![Backend tests](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/backend-tests.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/backend-tests.yml)
[![Frontend build](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/frontend-build.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/frontend-build.yml)
[![E2E admin pages](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/e2e-admin-pages.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/e2e-admin-pages.yml)
[![E2E Playwright](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/e2e-playwright.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/e2e-playwright.yml)
[![OpenAPI drift](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/openapi-check.yml/badge.svg)](https://github.com/skaba89/guineecare-hospital-suite/actions/workflows/openapi-check.yml)
[![Version](https://img.shields.io/badge/version-v1.6.0-blue.svg)](https://github.com/skaba89/guineecare-hospital-suite/releases)
[![License](https://img.shields.io/badge/license-Private-red.svg)](#licence)

Plateforme hospitalière complète pour la Guinée, inspirée des meilleurs SIH modernes : dossier patient informatisé, maternité, urgences, hospitalisation, pharmacie, laboratoire, imagerie, facturation, bloc opératoire, RH, qualité, reporting national et architecture technique industrielle.

**Version actuelle :** `v1.6.0` — Interopérabilité HL7 FHIR R4 (5 ressources : Patient, Encounter, Observation, MedicationRequest, DiagnosticReport) avec conversions automatiques depuis les modèles internes, recherche RESTful conforme FHIR, CapabilityStatement, OperationOutcome — complète les évolutions v1.5 (RH v2) et v1.4 (SMS réel + dashboard qualité OMS/HAS)

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
- ✅ v0.6 — Refresh token + audit log + code splitting (sécurité + compliance)
- ✅ v0.7 — Notifications multicanal + observabilité (Prometheus, health checks, JSON logs)
- ✅ v0.8 — Audit sécurité OWASP Top 10 + hardening (13/21 findings corrigés, Bandit SAST en CI)
- ✅ v0.9 — Hardening LOW restant + tests de charge Locust (TRUSTED_PROXIES, METRICS_TOKEN, bootstrap CLI, jti blacklist, A06 fail-mode)
- ✅ v0.10 — Documentation OpenAPI complète + Postman collection (138 endpoints, 25 tags, Bearer security, drift CI)
- ✅ v1.0 — Déploiement pilote CHU Donka (docker-compose prod hardening, TLS, scripts ops, runbook, CI release GHCR)
- ✅ v1.1 — Conduite du changement + formation + évolutions post-pilote (préférences user, feedback, items récents, 10 fiches rapides, FAQ, roadmap v1.2+)
- ✅ v1.2 — Export PDF (ordonnances, imagerie, labo, factures via ReportLab) + recherche globale Ctrl+K (patients, factures, labo, imagerie, notes cliniques)
- 🔜 v1.3 — i18n EN/FR complète + dashboard temps réel (WebSocket) + mode hors-ligne PWA + app mobile Android

## Sécurité

Le rapport d'audit sécurité complet est disponible dans `docs/security/AUDIT_V0.8.0.md`. La v0.9.0 corrige les 5 findings LOW restants acceptés en v0.8.0 — l'ensemble des 21 findings OWASP Top 10 sont désormais couverts.

### OWASP Top 10 — statut après v0.9.0

| ID  | Catégorie | Statut |
|-----|-----------|--------|
| A01 | Broken Access Control | ✅ Tous findings corrigés (CRITICAL + HIGH + LOW) |
| A02 | Cryptographic Failures | ✅ password_hash masqué ; bcrypt + HS256 OK |
| A03 | Injection | ✅ Aucune injection SQL (SAST clean) |
| A04 | Insecure Design | ✅ Lockout + password policy + rate-limit refresh |
| A05 | Security Misconfiguration | ✅ AUTH_SECRET hard-fail + TRUSTED_PROXIES + METRICS_TOKEN + bootstrap CLI + SEED_DEMO_DATA guard |
| A06 | Vulnerable Components | ✅ pip-audit + npm-audit en fail-mode (HIGH+) |
| A07 | Identification & Auth Failures | ✅ Lockout + jti blacklist pour révocation immédiate |
| A08 | Software & Data Integrity Failures | ✅ Pas d'eval/exec/pickle/yaml.load |
| A09 | Security Logging & Monitoring | ✅ Audit log complet |
| A10 | SSRF | ✅ Pas de requêtes HTTP basées sur input utilisateur |

### Variables d'environnement de sécurité (v0.9.0+)

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_SECRET` | (vide) | Secret JWT. **Obligatoire en non-local** — hard-fail au démarrage si vide. |
| `TRUSTED_PROXIES` | (vide) | Liste comma-separated d'IPs/CIDRs autorisés à setter `X-Forwarded-For`. Ex: `10.0.0.0/8,172.16.0.0/12`. Vide = aucun proxy trusté (raw `remote_addr` utilisé). |
| `METRICS_TOKEN` | (vide) | Bearer token requis pour `/metrics`. Vide = endpoint ouvert (dev/local). En prod, set à une valeur aléatoire ≥ 32 chars. |
| `BOOTSTRAP_TOKEN` | (vide) | Token requis pour `POST /users/bootstrap` en non-local. Vide = endpoint désactivé en non-local (utiliser `python -m app.cli create-superuser`). |

### CLI bootstrap (v0.9.0+)

Pour créer le premier SUPER_ADMIN sur une instance fraîchement déployée (alternativaire à l'HTTP `/users/bootstrap`) :

```bash
cd backend
python -m app.cli create-superuser \
    --email admin@chu-donka.gn \
    --first_name Admin \
    --last_name Root \
    --password 'StrongPass123!'
# Ou en interactif (password prompt) :
python -m app.cli create-superuser --email admin@chu-donka.gn --first-name Admin --last-name Root
```

Le CLI valide la politique de mot de passe (12+ chars, complexité) et refuse la création si la table users est non-vide (sans `--force`).

### Workflow CI sécurité

`security-scan.yml` tourne à chaque push + schedule hebdomadaire :
- `bandit-sast` — SAST Python (fail sur HIGH)
- `pip-audit` — dépendances backend (fail sur HIGH+ — v0.9.0)
- `npm-audit` — dépendances frontend (fail sur HIGH+ — v0.9.0)

### Tests de charge (v0.9.0+)

`load_tests/locustfile.py` — 2 scénarios Locust :
- `GuineeCareUser` (default) — login → browse patients → dashboard → notifications → logout (avec révocation jti)
- `GuineeCareLoginStorm` (`--tags login_storm`) — login fresh à chaque itération

Workflow CI `load-test.yml` : nightly 03:00 UTC, 20 users / 30s, rapport HTML uploadé en artifact.

## Documentation API (v0.10.0+)

L'API GuinéeCare est entièrement documentée en **OpenAPI 3.1** (138 endpoints, 25 tags thématiques). Toutes les routes protégées exposent automatiquement les réponses `401`, `403`, `429`, `500` et le security scheme `HTTPBearer` (JWT).

### Consultation interactive

| URL | Usage |
|-----|-------|
| `http://localhost:8000/docs` | Swagger UI — test interactif (cliquez sur 🔒 Authorize puis collez votre JWT) |
| `http://localhost:8000/redoc` | ReDoc — vue lecture seule, plus ergonomique |
| `http://localhost:8000/api/v1/openapi.json` | Spécification OpenAPI 3.1 machine-lisible |

### Artifacts versionnés

| Fichier | Taille | Usage |
|---------|--------|-------|
| `docs/api/openapi.json` | 545 KB | Spec OpenAPI 3.1 statique (auditable hors-ligne) |
| `docs/api/guineecare.postman_collection.json` | 173 KB | Collection Postman v2.1 (138 endpoints, 25 dossiers, auto-capture du JWT) |
| `docs/api/guineecare-local.postman_environment.json` | 1 KB | Environnement Postman (localhost + comptes de test) |

### Régénération

Après toute modification d'endpoint, exécutez :

```bash
python scripts/generate_openapi_artifacts.py
git add docs/api/
git commit -m "docs(api): regenerate openapi + postman"
```

Le workflow CI `openapi-check.yml` détecte automatiquement tout drift oublié et exécute `pytest tests/test_openapi.py` (19 tests de structure).

### Guides détaillés

- [`docs/api/OPENAPI_GUIDE.md`](docs/api/OPENAPI_GUIDE.md) — Vue d'ensemble, enrichissement automatique, CI drift detection, consultation interactive (Postman/Insomnia/Hoppscotch).
- [`docs/api/POSTMAN_GUIDE.md`](docs/api/POSTMAN_GUIDE.md) — Import Postman, variables d'environnement, authentification automatique, scénarios de démarrage rapide, Newman CLI.

Voir `load_tests/README.md` pour la doc complète des tests de charge.

## Conduite du changement et formation (v1.1.0+)

La version v1.1.0 introduit un socle d'endpoints orientés "expérience utilisateur" et un corpus documentaire complet pour la conduite du changement au CHU Donka.

### Nouveaux endpoints `/me` et `/feedback`

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/v1/me/preferences` | GET | Préférences UI de l'utilisateur courant (locale, theme, page_size, refresh) |
| `/api/v1/me/preferences` | PUT | Mise à jour partielle des préférences (audit log) |
| `/api/v1/me/recent` | GET | Items récemment consultés (patients, labo, imagerie…) |
| `/api/v1/me/recent` | POST | Enregistrer une consultation (upsert + pruning 50 items) |
| `/api/v1/me/recent` | DELETE | Vider l'historique |
| `/api/v1/feedback` | POST | Soumettre un retour (bug/suggestion/question/praise) |
| `/api/v1/feedback` | GET | Lister les feedbacks (filtrable, RBAC par établissement) |
| `/api/v1/feedback/{id}` | PATCH | Triage / résolution (ADMIN+ uniquement) |

Toutes les mutations sont journalisées dans l'audit log (`user.preferences.update`, `feedback.create`, `feedback.resolve`). Deux nouvelles permissions RBAC seedées : `feedback.read` et `feedback.resolve`.

### Documentation de conduite du changement

- [`docs/formation/conduite-du-changement.md`](docs/formation/conduite-du-changement.md) — Plan complet : objectifs chiffrés, 10 publics, 5 formats de formation, calendrier 12 semaines, gestion de la résistance, métriques d'adoption.
- [`docs/formation/quickstart-utilisateur.md`](docs/formation/quickstart-utilisateur.md) — Prise en main en 10 minutes, 4 cas pratiques par rôle.
- [`docs/formation/faq-utilisateurs.md`](docs/formation/faq-utilisateurs.md) — 27 Q/R en 7 thèmes (connexion, DPI, saisie, RBAC, performance, sécurité, feedback).
- [`docs/formation/parcours-recette-par-role.md`](docs/formation/parcours-recette-par-role.md) — Check-list de validation des compétences par rôle (~170 actions).
- [`docs/formation/fiches-rapides/`](docs/formation/fiches-rapides/) — 10 fiches A4 (une par rôle) à imprimer et distribuer.

### Roadmap post-pilote

- [`docs/post-pilot/EVOLUTIONS_POST_PILOTE.md`](docs/post-pilot/EVOLUTIONS_POST_PILOTE.md) — 15 évolutions candidates (v1.2 / v1.3 / v2.0) priorisées sur 5 critères, alimentées par la boucle feedback.

## Déploiement production (v1.0.0+)

Le déploiement pilote CHU Donka s'appuie sur Docker Compose avec un fichier de production durci (`docker-compose.prod.yml`) qui override la stack dev :

```bash
# 1. Cloner et préparer les secrets
git clone https://github.com/skaba89/guineecare-hospital-suite.git
cd guineecare-hospital-suite && git checkout v1.0.0

cp .env.production.template .env.production
# éditer .env.production et remplacer tous les CHANGE_ME_* par :
#   openssl rand -hex 48  # AUTH_SECRET
#   openssl rand -hex 32  # DB_PASSWORD, METRICS_TOKEN, BOOTSTRAP_TOKEN, REDIS_PASSWORD

# 2. Certificats TLS Let's Encrypt
sudo certbot certonly --standalone -d chu-donka.guineecare.gn
sudo mkdir -p tls && sudo cp /etc/letsencrypt/live/chu-donka.guineecare.gn/*.pem tls/

# 3. Validation pré-déploiement
bash scripts/deploy.sh --check-only

# 4. Déploiement
bash scripts/deploy.sh

# 5. Bootstrap super-admin
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production exec backend \
    python -m app.cli create-superuser \
        --email admin@chu-donka.gn --password '...' \
        --first-name Admin --last-name Donka
```

### Hardening production (vs dev)

| Aspect | Dev (`docker-compose.yml`) | Prod (`docker-compose.prod.yml`) |
|--------|---------------------------|----------------------------------|
| Utilisateur backend | root | `appuser` (UID 1001) non-root |
| Filesystem | writable | `read_only: true` + tmpfs `/tmp` |
| Capabilities | default | `cap_drop: ALL` |
| Security opt | — | `no-new-privileges:true` |
| ENVIRONMENT | development | production |
| SEED_DEMO_DATA | true | false (refusé au démarrage si true) |
| TLS | — | TLS 1.2/1.3, HSTS 1 an, redirect HTTP→HTTPS |
| Headers | backend-only | CSP strict + Permissions-Policy + COOP/CORP |
| Rate limiting | backend (slowapi) | nginx (5 logins/min, 120 API/min) + backend |
| `/metrics` | ouvert | IP allowlist (private ranges) + token |
| `/docs` `/redoc` | public | IP allowlist (admin office) |
| Resources | illimitées | limits mémoire + CPU par service |
| Backup | — | quotidien 02:00 UTC, rétention 14 jours |
| Restart | unless-stopped | always |

### Scripts opérationnels

| Script | Usage |
|--------|-------|
| `scripts/deploy.sh` | Déploiement complet (build + migrations + start + smoke test) |
| `scripts/deploy.sh --check-only` | Validation pré-déploiement (secrets, TLS, ressources) |
| `scripts/backup.sh` | Backup manuel immédiat |
| `scripts/backup.sh --verify` | Valide le dernier backup (`pg_restore --list`) |
| `scripts/backup.sh --list` | Liste les backups existants |
| `scripts/restore.sh --latest` | Restaure le dernier backup (DROP + recreate) |
| `scripts/restore.sh --host <file>` | Restaure depuis un fichier sur l'hôte |
| `scripts/seed-pilot.sh` | Crée le premier super-admin CHU Donka |

### CI release

Le workflow `.github/workflows/deploy-release.yml` build et push les images Docker vers GHCR (`ghcr.io/skaba89/guineecare-backend`, `ghcr.io/skaba89/guineecare-frontend`) à chaque tag `v*`. Les releases GitHub sont créées automatiquement avec les notes de changelog.

### Documentation déploiement

- [`docs/deploiement/RUNBOOK_CHU_DONKA.md`](docs/deploiement/RUNBOOK_CHU_DONKA.md) — Runbook complet : architecture, pré-requis serveur, installation, déploiement, opérations courantes, monitoring, procédures d'incident (P0/P1/P2), maintenance planifiée, rollback, checklist go-live.

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
