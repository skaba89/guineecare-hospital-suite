# Changelog

## [0.7.0] — 2026-06-20

### Added — Module notifications (multicanal)
- **Migration Alembic 0012** : table `notifications` (recipient_id, sender_id, facility_id, category, priority, title, body, action_url, channels CSV, in_app/email/sms delivered flags, read_at, dismissed_at, resource_type, resource_id).
- **Service `notify()`** (`app/modules/notifications/service.py`) : helper à appeler depuis n'importe quelle route. Jamais bloquant — les échecs d'envoi sont enregistrés sur la ligne mais ne lèvent jamais d'exception.
- **3 canaux pluggables** : `ConsoleChannel` (toujours actif pour in_app), `EmailChannel` (SMTP — activé quand `SMTP_HOST` est set), `SmsChannel` (Twilio — activé quand `TWILIO_ACCOUNT_SID` est set). Aucune dépendance externe supplémentaire (smtplib + lazy import de twilio).
- **Routes** :
  - `GET /notifications` — liste paginée des notifications de l'utilisateur courant (filtres category, unread_only).
  - `GET /notifications/unread-count` — compteur pour badge d'en-tête.
  - `PATCH /notifications/{id}/read` — marquer comme lu.
  - `POST /notifications/mark-all-read` — tout marquer comme lu.
  - `DELETE /notifications/{id}` — supprimer (soft-delete via `dismissed_at`).
  - `POST /notifications/send` — admin-only (permission `notification.send`) pour envoyer à un utilisateur spécifique. Audit log automatique.
- **Permission RBAC** : `notification.send` ajoutée au seed (réservée SUPER_ADMIN/ADMIN via bypass).
- **Page frontend `/notifications`** : liste paginée avec filtres (catégorie, non lues seulement), badges de priorité colorés, icônes par catégorie, boutons marquer-comme-lu/supprimer, "tout marquer comme lu", infobulles sur l'état de livraison email/SMS.
- **Sidebar** : entrée "Notifications" ajoutée en haut de la section SOINS (visible pour tous les utilisateurs authentifiés — c'est leur boîte de réception personnelle).

### Added — Observabilité (Prometheus + health checks + logging structuré)
- **`GET /health/live`** : liveness probe — retourne 200 immédiatement si le process est vivant. Pour Kubernetes livenessProbe.
- **`GET /health/ready`** : readiness probe — ping DB (`SELECT 1`), retourne 200 si OK ou 503 si DB down. Pour Kubernetes readinessProbe.
- **`GET /metrics`** : exposition Prometheus text format (v0.0.4). Métriques :
  - `http_requests_total{method, path, status}` — counter
  - `http_request_duration_seconds{method, path, status}` — histogram (11 buckets de 5ms à 10s)
  - `http_requests_in_flight` — gauge
  - `app_info{version, environment}` — gauge constante
- **Middleware `MetricsMiddleware`** : instrumente chaque requête HTTP. Utilise le path template (ex. `/patients/{id}`) plutôt que le path brut pour éviter l'explosion de cardinalité des labels.
- **Logging structuré** : `JsonFormatter` (prod/staging) ou `PrettyFormatter` (dev/test) configuré au démarrage via `configure_logging(environment=...)`. Aucune dépendance externe (pas de structlog ni python-json-logger) — utilise la stdlib `logging` uniquement.
- **Endpoints sans auth** : `/health`, `/health/live`, `/health/ready`, `/metrics` ne nécessitent pas de JWT — par convention Kubernetes/Prometheus. En production, restreindre `/metrics` au niveau ingress (IP Prometheus uniquement).

### Added — Tests
- **`backend/tests/test_notifications.py`** : 24 tests (service notify + mark_read + dismiss + mark_all_read + HTTP list/filter/unread-count/mark-read/dismiss + admin send + RBAC + audit).
- **`backend/tests/test_observability.py`** : 12 tests (health live/ready, 503 on DB failure, metrics format/content/in-flight gauge, no-auth).
- **`frontend/tests/e2e/guineecare.spec.ts`** : 2 nouveaux tests Playwright (page /notifications accessible SUPER_ADMIN + DOCTOR).
- **Total** : 135 tests backend (99 + 36) + 16 tests Playwright (14 + 2).

### Fixed
- **`run_playwright.sh`** : `SEED_DEMO_DATA=false` → `true` (sinon le compte admin@guineecare.com n'existe pas et le check de login échoue).
- **`main.py`** : version FastAPI app mise à jour 0.1.0 → 0.7.0 (cohérence avec le tag git).

### Statistics
- 135/135 tests backend pytest (45.9 s)
- 16/16 tests Playwright UI (60 s, 1 flaky sur retry)
- 31/31 tests E2E API admin pages (inchangés)
- Bundle initial : 253 KB (gzip 80 KB) — inchangé (NotificationsPage chunké à 9.78 KB)
- 3 nouveaux modules backend : `notifications` (models + service + routes + schemas), `observability` (metrics + logging + middleware + routes)
- 1 nouvelle migration Alembic (0012)
- 1 nouvelle page frontend (NotificationsPage) + 1 nouvelle permission RBAC (notification.send)

---

## [0.6.0] — 2026-06-20

### Added — Refresh token + révocation JWT (sécurité)
- **`POST /auth/refresh`** : échange un refresh token valide contre un nouveau pair (access + refresh). Rotation automatique : l'ancien refresh token est révoqué immédiatement après usage.
- **`POST /auth/logout`** : révoque explicitement un refresh token (le `access_token` reste valide jusqu'à expiration, ~60 min).
- **Migration Alembic 0011** : table `refresh_tokens` (id, user_id, token_hash SHA-256, expires_at, revoked_at, replaced_by_id, created_ip, created_user_agent).
- **Sécurité** : le refresh token est stocké haché (SHA-256) en base — jamais en clair. Durée de vie : 30 jours.
- **Frontend** : `api.ts` gère automatiquement le refresh sur 401 (retry une fois avec un nouveau access token). Déduplication des refresh parallèles via `refreshPromise` partagé.
- **Frontend** : `authService.logout()` devient asynchrone et appelle `/auth/logout` pour révoquer côté serveur.

### Added — Module audit log (compliance)
- **Migration Alembic 0011** : table `audit_logs` (append-only) avec colonnes : user_id, facility_id, action, resource_type, resource_id, http_method, http_path, status_code, ip_address, user_agent, payload JSON.
- **Service `audit_log()`** (`app/modules/audit/service.py`) : helper à appeler depuis n'importe quelle route. Jamais bloquant (catch all errors, log + rollback).
- **Route `GET /audit/logs`** : liste paginée + filtres (action, resource_type, resource_id, user_id, start_date, end_date). SUPER_ADMIN voit tout, ADMIN voit sa facility.
- **Route `GET /audit/logs/{id}`** : détail d'une entrée.
- **Permission `audit.read`** : ajoutée au seed RBAC (réservée SUPER_ADMIN/ADMIN via bypass).
- **Audit automatique sur** : `auth.login`, `auth.login_failed`, `auth.login_inactive`, `auth.logout`.
- **Page frontend `/audit`** : tableau paginé avec filtres, codes couleur par action, modal de détail avec payload JSON formaté. Visible uniquement SUPER_ADMIN/ADMIN.
- **Sidebar** : section SYSTÈME enrichie avec "Journal d'audit".

### Added — Code splitting frontend (performance)
- **`React.lazy()` + `Suspense`** sur les 24 pages authentifiées.
- **Bundle initial** : 1014 KB → 252 KB (−75 %). Gzippé : 257 KB → 80 KB.
- Chunks par page : `AuditPage.js` 9.9 KB, `RbacPage.js` 9.5 KB, `DashboardPage.js` 15.9 KB, etc.
- Chunks Recharts isolés : `CategoricalChart.js` 296 KB (chargé uniquement sur pages avec graphiques), `BarChart.js` 47 KB, `PieChart.js` 17 KB.
- Plus d'avertissement "chunks > 500 kB" au build.

### Added — Tests
- **`backend/tests/test_refresh_audit.py`** : 15 nouveaux tests couvrant refresh token (issue, rotate, revoke, hash storage), audit log (login success/fail/logout enregistré, endpoint require auth, filtres, pagination).
- **`frontend/tests/e2e/guineecare.spec.ts`** : 2 nouveaux tests Playwright (page /audit accessible SUPER_ADMIN + DOCTOR redirigé).
- **Total** : 99 tests backend (84 + 15) + 14 tests Playwright (12 + 2).

### Fixed — Frontend
- **LoginPage** : ajout des `htmlFor` + `id` sur les labels/inputs pour sélecteurs Playwright stables (`#login-email`, `#login-password`).
- **Tests Playwright** : fonction `login()` réécrite — clear localStorage avant chaque login, IDs stables, `networkidle` wait. Tous les tests auparavant flaky sont désormais 100 % verts.
- **`playwright.config.ts`** : `reuseExistingServer: true` pour permettre le lancement d'un Vite externe + réutilisation par Playwright.
- **`vite-env.d.ts`** : recréé (perdu lors d'un reset) pour résoudre l'erreur TS2882 sur l'import side-effect CSS.

### Statistics
- 99/99 tests backend pytest (37 s)
- 14/14 tests Playwright UI (41 s)
- 31/31 tests E2E API admin pages (inchangés)
- Bundle initial : 252 KB (gzip 80 KB) — 4× plus léger
- 4 workflows GitHub Actions opérationnels
- 2 nouveaux modules backend : `auth.models` (RefreshToken, AuditLog), `audit` (service + routes)

---

## 0.5.0 — 2026-06-20

### Added — Tests Playwright E2E
- **12 parcours UI** avec Playwright 1.61 + Chromium
  - Authentification (login succès/échec, logout, multi-rôles)
  - Navigation pages admin (/users, /rbac, /facilities, /departments)
  - RBAC (DOCTOR/NURSE redirigés des pages admin)
  - Parcours patients
  - Dashboard (KPI visibles)
- `frontend/playwright.config.ts` — config avec webServer auto-start, traces, screenshots, vidéo
- `frontend/tests/e2e/guineecare.spec.ts` — 12 tests couvrant les parcours critiques
- Scripts npm : `npm run test:e2e`, `npm run test:e2e:ui`, `npm run test:e2e:report`

### Added — Vite proxy
- `frontend/vite.config.ts` — proxy `/api/*` → `http://127.0.0.1:8000`
- Plus besoin de `VITE_API_BASE_URL` en développement local
- Variable `VITE_API_PROXY_TARGET` configurable pour pointer vers un backend distant

### Added — CI/CD GitHub Actions (4 workflows)
- **`backend-tests.yml`** — pytest (84 tests) + cache pip + upload XML results
- **`frontend-build.yml`** — TypeCheck + build Vite + upload artifact `dist/`
- **`e2e-admin-pages.yml`** — 31 tests API E2E (déjà existant, inchangé)
- **`e2e-playwright.yml`** — Nouveau : démarre backend + seed, installe Chromium, lance les 12 tests Playwright, upload rapport HTML + traces
- Tous les workflows : `on: push: branches: [main]` + `pull_request`
- Badges README pour les 4 workflows

### Fixed — Backend
- **Rate limiter** `@limiter.limit("5/minute")` sur `/auth/login` :
  - Désactivé en `ENVIRONMENT=local|test|dev` (facilite tests E2E et Playwright)
  - Activé en production/staging (sécurité brute-force)
- Correction syntaxe YAML dans `backend-tests.yml` et `frontend-build.yml` (`branches: ain]` → `branches: [main]`)

### Updated — Documentation
- README enrichi : badges CI, table des 4 workflows, section Proxy Vite, section Contribution, conventions de commit Angular, roadmap v0.6-v1.0
- Référence aux scripts Playwright (`npm run test:e2e*`)
- Exemples de code multi-tenant RLS et ProtectedRoute

### Statistics
- 84/84 tests pytest backend
- 31/31 tests E2E API pages admin
- 12 tests Playwright UI (parcours critiques)
- 4 workflows GitHub Actions opérationnels
- ~3 min de pipeline CI total

---

## 0.4.0 — 2026-06-19

### Added — Pages admin (section SYSTÈME)
- **`/users`** — Gestion des utilisateurs (CRUD, activation/désactivation, filtre par rôle, recherche)
- **`/rbac`** — Matrice rôles × permissions avec toggle visuel, création de rôles et permissions
- **`/facilities`** — Établissements de santé en cartes (vue nationale pour SUPER_ADMIN, mono-établissement pour ADMIN)
- **`/departments`** — Départements avec filtre par établissement
- Section "SYSTÈME" ajoutée à la sidebar (visible uniquement SUPER_ADMIN/ADMIN)
- Routes frontend protégées par `ProtectedRoute roles={["SUPER_ADMIN","ADMIN"]}`
- Flags `canSeeUsers`, `canSeeRbac`, `canSeeFacilities`, `canSeeDepartments` dans `useNavVisibility()`

### Added — Tests E2E
- Script `scripts/verify_admin_pages.py` : 31 tests E2E automatisés
  - Authentification multi-rôles (5 comptes : SUPER_ADMIN, ADMIN, DOCTOR, NURSE, PHARMACIST)
  - RBAC strict sur `/users`, `/rbac/roles`, `/rbac/permissions` (DOCTOR/NURSE → 403)
  - Isolation multi-tenant (`/facilities` : ADMIN voit 1, SUPER_ADMIN voit 20)
  - Validation Pydantic v2 (email invalide → 422, champ manquant → 422)
  - Pages frontend servies par Vite (5 routes)

### Fixed — Backend
- **`POST /patients`** : auto-génération de `facility_id` (depuis JWT) et `patient_number` (format `PAT-YYYYMMDDHHMMSS`) si manquants — facilite l'usage API
- **`GET /hospitalization/bed-board`** : `facility_id` devient optionnel
  - SUPER_ADMIN sans `facility_id` → tous les lits
  - Autres rôles sans `facility_id` → fallback sur leur établissement
- **`UserCreate`** : durcissement de la validation
  - `email` → `EmailStr` (validation RFC 5322)
  - `password` → `Field(min_length=8)`
  - `first_name` / `last_name` → `Field(min_length=1, max_length=100)`
- **`UserUpdate`** : même durcissement
- Migration `class Config` → `model_config = ConfigDict(from_attributes=True)` sur `UserRead`, `PatientRead`

### Hygiene
- `.gitignore` backend : exclusion des `*.db` et `__pycache__/`
- Suppression du tracking git de `backend/test_guineecare.db`
- `start_dev.sh` : script de démarrage robuste avec seed complet

### Statistics
- 84/84 tests pytest backend
- 31/31 tests E2E pages admin
- 4 nouvelles pages frontend (350+ lignes chacune)
- Build Vite OK (1 MB gzippé)

---

## 0.3.0 — 2026-06-14

- Suite E2E complète (109/109 tests)
- RBAC permission improvements
- Bug fixes sur tests E2E

## 0.2.0 — 2026-06-10

- Multi-tenant RLS + RBAC robuste
- Gestion du personnel complète

## 0.1.0 — 2026-06-02

- Création de la base documentaire GuinéeCare Hospital Suite
- Ajout des 16 lots fonctionnels et techniques
- Documents de roadmap, budget, gouvernance, architecture, déploiement
