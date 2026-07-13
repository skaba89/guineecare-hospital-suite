# Release Notes — GuinéeCare Hospital Suite v2.9.2

**Date :** 14 juillet 2026
**Version :** 2.9.2 (depuis 2.8.9 / 2.9.0 / 2.9.1)
**Statut :** ✅ Prête pour déploiement national flagship

---

## 📦 Contenu de la release

L'archive `v2.9.2.zip` contient le code source complet du projet GuinéeCare Hospital Suite, sans les dépendances (`node_modules`, `.venv`, `__pycache__`).

**Taille :** 31 MB (1 729 fichiers)
**Dépendances à installer :**
- Backend : `cd backend && pip install -r requirements.txt`
- Frontend : `cd frontend && npm install`
- Mobile : `cd mobile && npm install`

---

## ✨ Nouveautés principales

### 1. Redis rate limit partagé multi-instance (P1)

- Nouveau module `backend/app/core/redis.py`
- Branchement automatique du storage Redis dans slowapi quand `REDIS_URL` est configurée
- Fallback mémoire en l'absence de Redis (dev/test) — pas de dépendance dure
- Compatible Render multi-instance et Kubernetes replicas

### 2. Celery worker + beat — 5 tâches planifiées (P1)

- Nouveau module `backend/app/tasks/` (celery_app, maintenance_tasks, reporting_tasks, routes)
- **Tâches planifiées (cron) :**
  - `prune_audit_logs` — quotidien 03h UTC — purge RGPD Art. 25
  - `backup_database` — quotidien 04h UTC — dump PostgreSQL + rotation 30j
  - `retry_sms_pending` — 5 min — retry SMS en échec
  - `push_dhis2_monthly` — 5 du mois 06h UTC — push DHIS2 M-1
  - `send_quality_alerts_digest` — digest quotidien alertes qualité
- **Routes API :** `GET /api/v1/tasks` + `POST /api/v1/tasks/trigger/{name}` (SUPER_ADMIN)
- Compatible Celery absent : exécution synchrone via `submit_task()`

### 3. Mode sombre frontend (P2)

- Nouveau `ThemeContext.tsx` + composant `ThemeToggle.tsx`
- Variables CSS `[data-theme="dark"]` redéfinissent toute la palette
- Toggle 🌙/☀️ dans le topbar
- Persistance `localStorage` (clé `guineecare_theme`)
- Respect `prefers-color-scheme` au premier chargement

### 4. Hook infinite scroll (P2)

- Nouveau hook `useInfiniteScroll` + composant `Sentinel` (IntersectionObserver)
- Append-only avec debounce search
- Compatible `apiRequest` existant — pas de refactor des pages

### 5. Module ICD-11 (P2)

- Nouveau module `backend/app/modules/icd11/`
- Catalogue embarqué de ~80 codes ICD-11 (classification OMS 2022) prioritaires pour la Guinée
- **Endpoints :**
  - `GET /api/v1/icd11/search?q=...&limit=20` — recherche fuzzy
  - `GET /api/v1/icd11/{code}` — détail d'un code
  - `GET /api/v1/icd11/categories` — liste des catégories
- Codes clés : paludisme, hypertension, diabète, prééclampsie, hémorragie post-partum, Ebola, Lassa, VIH, TB

### 6. Documentation juridique (P0)

- **`docs/securite/DPO_DESIGNATION_v1.md`** (~250 lignes)
  - Charte complète du DPO (Article 39 RGPD)
  - Fiche de poste détaillée (6 missions, KPI annuels)
  - Modèle d'arrêté ministériel de nomination
  - Plan de mise en œuvre en 5 étapes
- **`docs/securite/CAHIER_DES_CHARGES_PEN_TEST_v1.md`** (~350 lignes)
  - Périmètre backend + frontend + mobile (boîte noire/grise/blanche)
  - Méthodologie OWASP WSTG + API Top 10 + Mobile Top 10
  - Règles d'engagement
  - Critères CVSS v3.1
  - Budget indicatif : 25 000 € – 50 000 € HT
  - Planning 19 semaines

### 7. Tests backend étendus (+38 tests)

- `tests/test_v292_redis_celery.py` (16 tests) — Redis fallback + Celery synchrone + routes /tasks RBAC
- `tests/test_v292_icd11.py` (22 tests) — Catalogue + routes API + RBAC
- **Total backend : 280+ tests passent**

### 8. Tests E2E Playwright étendus (+24 parcours)

- `frontend/tests/e2e/v292-extended.spec.ts` (12 parcours) — Pharmacy, Lab, Billing, Maternity, Hospitalization, Imaging, Surgery, Quality, Personnel, National, Activity, SMS Admin, Tasks API, DHIS2, Insurance
- `frontend/tests/e2e/v292-dark-mode.spec.ts` (12 parcours) — Toggle UI, persistance, lisibilité, ICD-11 API
- **Total E2E : 24 parcours**

### 9. Configuration production étendue

#### `render.yaml` (Render Blueprint)
- 4 services : web + redis + worker + beat
- Variables `REDIS_URL`, `CELERY_BROKER_URL`, `AUDIT_LOG_RETENTION_DAYS`, `BACKUP_RETENTION_DAYS`, `DHIS2_*`
- Plans Render : Starter $7/mois (web) + Starter $10/mois (redis) + Starter $7/mois (worker) + Starter $7/mois (beat) = ~$31/mois

#### `docker-compose.prod.yml` (Docker Compose)
- 2 services ajoutés : `celery-worker` + `celery-beat`
- Security hardening : user non-root, read-only, cap_drop ALL, no-new-privileges
- Resource limits : 512M + 1 CPU (worker), 256M + 0.25 CPU (beat)

### 10. Runbook & script de validation

- **`docs/deploiement/RUNBOOK_MISE_A_JOUR_v2.9.2.md`** (~400 lignes)
  - 5 phases : préparation, déploiement Render/VPS, migration DB, validation, post-déploiement
  - Procédure de rollback (Render + Docker)
  - Troubleshooting (5 problèmes courants)
  - 10 KPIs de succès
- **`scripts/validate_v292.sh`** (~250 lignes)
  - 10 checks automatisés : health, version, login, Redis, Celery, tâches, ICD-11, insurance, DHIS2, metrics
  - Code couleur (pass/fail/warn) + résumé final

---

## 📊 Métriques de la release

| Métrique | Avant (v2.8.9) | Après (v2.9.2) | Δ |
|----------|----------------|----------------|---|
| Version | 2.8.9 | **2.9.2** | +0.0.3 |
| Tests backend | 243+ | **280+** | +38 |
| Modules backend | 27 | **29** | +2 (tasks, icd11) |
| Parcours E2E | 12 | **24** | +12 |
| Migrations Alembic | 28 | 28 | 0 (pas de nouvelle table) |
| Pages frontend | 32 | 32 | 0 |
| Écrans mobile | 10 | 10 | 0 |
| Documents | 96 | **98** | +2 (DPO + pen test CDC) |
| Score conformité RGPD | 55% | **75%** | +20% (estimation) |

---

## 🚀 Procédure d'installation

### Pré-requis

- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (ou Neon serverless)
- Redis 7+ (optionnel en dev, requis en prod pour Celery)
- Compte Render (ou VPS Docker)

### Démarrage local (dev)

```bash
# 1. Extraire l'archive
unzip v2.9.2.zip
cd v2.9.2/guineecare-hospital-suite

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL="sqlite:///./dev_guineecare.db" \
AUTH_SECRET="dev-secret-key-2025" \
ENVIRONMENT=local \
SEED_DEMO_DATA=true \
CORS_ORIGINS='["*"]' \
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Frontend (autre terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

### Déploiement production (Render)

Voir `docs/deploiement/RUNBOOK_MISE_A_JOUR_v2.9.2.md` pour la procédure complète.

Résumé :
1. Créer un service Redis sur Render
2. Ajouter `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` aux variables d'env du backend
3. Créer 2 background workers (celery-worker + celery-beat)
4. Déployer le backend
5. Valider avec `./scripts/validate_v292.sh https://votre-url admin@guineecare.com admin123`

### Déploiement production (VPS Docker)

```bash
# 1. Configurer .env.production
cp .env.production.template .env.production
# Éditer : DB_PASSWORD, AUTH_SECRET, REDIS_PASSWORD, CORS_ORIGINS, etc.

# 2. Démarrer
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. Valider
./scripts/validate_v292.sh https://votre-domaine.gn admin@guineecare.com admin123
```

---

## ✅ Comptes de test (seed démo)

| Rôle | Email | Mot de passe |
|------|-------|--------------|
| SUPER_ADMIN | admin@guinecare.com | admin123 |
| DOCTOR | dr.diallo@chu-donka.gn | doctor123 |
| NURSE | inf.konde@chu-donka.gn | nurse123 |
| PHARMACIST | ph.bah@chu-donka.gn | pharma123 |
| LAB_TECH | lab.cisse@chu-donka.gn | lab123 |
| CASHIER | caissier.camara@chu-donka.gn | cash123 |

---

## ⚠️ Reste à traiter (décisions administratives)

Les 3 P0 restants ne relèvent plus du code mais de **décisions administratives** :

| Priorité | Élément | Action |
|----------|---------|--------|
| P0 | Render Starter plan ($7/mois) | Upgrade Render à Starter |
| P0 | DPO officiellement nommé | Signer l'arrêté (modèle dans `DPO_DESIGNATION_v1.md`) |
| P0 | Pen test externe réalisé | Lancer appel d'offres (CDC dans `CAHIER_DES_CHARGES_PEN_TEST_v1.md`) |

---

## 📞 Support

- **Documentation complète** : `docs/` dans l'archive
- **Runbook mise à jour** : `docs/deploiement/RUNBOOK_MISE_A_JOUR_v2.9.2.md`
- **Troubleshooting** : section 6 du runbook
- **Contact technique** : tech@guineecare.gn
- **Contact juridique** : dpo@sante.gov.gn

---

## 📋 Changelog complet

Voir `CHANGELOG.md` dans l'archive pour le détail exhaustif des modifications.
