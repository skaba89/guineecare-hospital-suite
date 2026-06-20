# Rapport d'audit de sécurité — v0.8.0

**Date** : 2026-06-20
**Périmètre** : backend FastAPI + frontend React
**Méthodologie** : OWASP Top 10 (2021) + SAST Bandit + revue manuelle
**Auditeur** : automatique + revue humaine

---

## Synthèse

| Sévérité | Avant fix | Après fix | Statut |
|----------|-----------|-----------|--------|
| CRITICAL | 2         | 0         | ✅ tous corrigés |
| HIGH     | 2         | 0         | ✅ tous corrigés |
| MEDIUM   | 9         | 0         | ✅ tous corrigés |
| LOW      | 8         | 5         | ⚠️ 5 acceptés (documentés ci-dessous) |

**Total** : 13/21 findings corrigés en v0.8.0. Les 5 restants sont LOW severity, documentés comme risques acceptés avec plan de mitigation.

---

## Findings corrigés (v0.8.0)

### CRITICAL — A02-001 : Fuite de `password_hash` via /users endpoints

**Fichier** : `backend/app/modules/users/routes.py`
**Problème** : Les endpoints `GET /users`, `POST /users`, `PUT /users/{id}`, `POST /users/bootstrap` retournaient l'objet User ORM brut, qui inclut la colonne `password_hash` (bcrypt). Un ADMIN pouvait moissonner tous les hashes de mots de passe de sa facility.
**Fix** : Ajout de la méthode `User.to_read_dict()` qui exclut `password_hash`. Tous les endpoints /users retournent maintenant ce dict sécurisé. La schéma `UserRead` est défini avec Pydantic pour validation.
**Tests** : `test_security_hardening.py::TestPasswordHashNotExposed` (4 tests).

### CRITICAL — A01-001 : ADMIN facility-scoped pouvait muter le RBAC global

**Fichier** : `backend/app/modules/rbac/routes.py`
**Problème** : Les endpoints `POST /rbac/roles`, `POST /rbac/permissions`, `POST /rbac/role-permissions` étaient gardés par `require_role("SUPER_ADMIN", "ADMIN")`. Or ADMIN est facility-scoped (`CROSS_TENANT_ROLES = {"SUPER_ADMIN"}`). Un ADMIN de la facility A pouvait créer des rôles/permissions globaux affectant toutes les facilities.
**Fix** : Restriction à `require_role("SUPER_ADMIN")` uniquement pour les 3 endpoints de mutation. Les endpoints de lecture (GET) restent accessibles à ADMIN.
**Tests** : `test_security_hardening.py::TestRBACSuperAdminOnly` (4 tests).

### HIGH — A01-002 : /activity leakait l'activité cross-facility à ADMIN

**Fichier** : `backend/app/modules/activity/routes.py`
**Problème** : `GET /activity` était accessible à ADMIN mais `ActivityEntry` n'a pas de colonne `facility_id` — la table est globale. Un ADMIN facility-scoped pouvait lire toutes les actions de toutes les facilities.
**Fix** : Restriction à `require_role("SUPER_ADMIN")` uniquement.
**Tests** : `test_security_hardening.py::TestActivitySuperAdminOnly`.

### HIGH — A09-001 : Mutations users/facilities/departments/RBAC non auditées

**Fichiers** : `users/routes.py`, `facilities/routes.py`, `departments/routes.py`, `rbac/routes.py`
**Problème** : Les mutations (create/update) sur users, facilities, departments et RBAC n'appelaient pas `audit_log()`. Un ADMIN pouvait changer le mot de passe de n'importe quel utilisateur de sa facility sans laisser de trace.
**Fix** : Ajout de `audit_log()` sur toutes les mutations. Pour les changements de mot de passe, le payload contient `"password": "[REDACTED]"` — jamais le mot de passe en clair.
**Tests** : `test_security_hardening.py::TestAuditLogOnMutations` (6 tests).

### MEDIUM — A01-003 : /notifications/send sans contrôle tenant sur le destinataire

**Fichier** : `backend/app/modules/notifications/routes.py`
**Problème** : Un ADMIN facility-scoped pouvait envoyer une notification (in_app + email si SMTP configuré) à n'importe quel utilisateur de n'importe quelle facility — vecteur de phishing cross-tenant.
**Fix** : Ajout de `enforce_facility_access(current_user, recipient.facility_id)` après la récupération du destinataire.
**Tests** : `test_security_hardening.py::TestNotificationSendTenantIsolation`.

### MEDIUM — A04-001 : Pas de lockout après échecs de login

**Fichiers** : `auth/routes.py`, `users/models.py`, migration `0013_security_hardening.py`
**Problème** : Le rate-limiter (5/min par IP) pouvait être contourné en changeant d'IP. Aucun verrouillage par compte.
**Fix** : Ajout des colonnes `failed_login_count` et `locked_until` sur User. Après 5 échecs, le compte est verrouillé 15 minutes. Le compteur est réinitialisé sur login réussi. Réponse 423 Locked si tentative sur compte verrouillé.
**Tests** : `test_security_hardening.py::TestAccountLockout` (2 tests).

### MEDIUM — A04-002 : Politique de mot de passe trop faible

**Fichier** : `backend/app/modules/users/schemas.py`
**Problème** : `UserCreate.password = Field(min_length=8)` — aucune exigence de complexité. Les seeds utilisent `admin123`, `doctor123`, etc.
**Fix** : Validation Pydantic personnalisée exigeant : ≥12 caractères, ≥1 majuscule, ≥1 minuscule, ≥1 chiffre, ≥1 caractère spécial (`!@#$%^&*()-_=+[]{}|;:,.<>?`).
**Tests** : `test_security_hardening.py::TestPasswordPolicy` (5 tests).

### MEDIUM — A04-003 : /auth/refresh non rate-limité

**Fichier** : `backend/app/modules/auth/routes.py`
**Problème** : Seul `/auth/login` était rate-limité. `/auth/refresh` ne l'était pas — vecteur de DoS et de flooding d'audit logs.
**Fix** : Ajout de `@_REFRESH_LIMIT = limiter.limit("30/minute")` en production/staging (no-op en dev/test). Audit log ajouté sur tous les échecs de refresh (unknown_token, revoked, expired, user_inactive).

### MEDIUM — A05-003 : `AUTH_SECRET` vide accepté en non-local

**Fichier** : `backend/app/core/config.py`
**Problème** : `validate_settings()` levait `RuntimeError` mais `main.py` catchait l'exception et continuait. L'app démarrait avec un secret vide en production → JWTs trivialement forgeables.
**Fix** : `validate_settings()` appelle `sys.exit(1)` en non-local si `AUTH_SECRET` est vide. En local, un warning est émis. Hard-fail, pas de continuité.
**Tests** : `test_security_hardening.py::TestAuthSecretValidation` (3 tests).

### MEDIUM — A09-002/003/004 : Mutations facilities/departments/RBAC non auditées

Voir A09-001 ci-dessus — même fix appliqué à `facilities/routes.py`, `departments/routes.py`, `rbac/routes.py`.

---

## Risques acceptés (LOW severity)

Les 5 findings suivants sont LOW severity et acceptés avec plan de mitigation.

### LOW — A05-001 : `X-Forwarded-For` trusted sans validation

**Fichier** : `backend/app/core/limiter.py`
**Risque** : Si le backend est exposé directement (sans reverse proxy), un attaquant peut spoofé `X-Forwarded-For` pour bypasser le rate-limiter.
**Mitigation actuelle** : Documentation — le backend DOIT être derrière nginx/ingress qui overwrite `X-Forwarded-For`.
**Plan** : v0.9 — ajouter une liste `TRUSTED_PROXIES` et vérifier que le remote addr est dans cette liste avant de trust `X-Forwarded-For`.

### LOW — A05-002 : Seeds avec mots de passe faibles (admin123, etc.)

**Fichier** : `backend/app/db/seed.py`
**Risque** : Si `SEED_DEMO_DATA=true` est accidentellement activé en prod, les comptes créés ont des mots de passe trivialement devinables.
**Mitigation actuelle** : `SEED_DEMO_DATA` defaults to `false` ; `main.py` ne l'active que si explicitement set.
**Plan** : v0.9 — refuser le seed en production (`ENVIRONMENT=production` + `SEED_DEMO_DATA=true` → erreur fatale).

### LOW — A05-004 : POST /users/bootstrap non authentifié

**Fichier** : `backend/app/modules/users/routes.py`
**Risque** : Sur une instance fraîchement déployée mais network-reachable, un attaquant peut créer le premier SUPER_ADMIN.
**Mitigation actuelle** : L'endpoint n'accepte qu'une seule création (user_count == 0). La fenêtre de vulnérabilité est courte.
**Plan** : v0.9 — préférer un script CLI `python -m app.cli create-superuser` (pas d'endpoint HTTP) OU gate avec un bootstrap token env var.

### LOW — A05-005 : /metrics non authentifié

**Fichier** : `backend/app/modules/observability/routes.py`
**Risque** : `/metrics` expose des métriques Prometheus (compteurs par endpoint, latences) sans auth. Utile pour reconnaissance.
**Mitigation actuelle** : Documentation — `/metrics` doit être restreint au niveau ingress (IP Prometheus uniquement).
**Plan** : v0.9 — ajouter un `METRICS_TOKEN` optionnel (bearer token) pour authentifier `/metrics`.

### LOW — A01-004/005 : Pattern fetch-then-check (404 vs 403 oracle)

**Fichiers** : `imaging/routes.py`, `surgery/routes.py`, `quality/routes.py`, `billing/routes.py`, `personnel/routes.py`, etc.
**Risque** : Le pattern `db.query(Model).filter(id=id).first()` + `enforce_facility_access(row.facility_id)` révèle l'existence d'un UUID cross-tenant (404 si inexistant, 403 si existe dans autre facility).
**Mitigation actuelle** : Faible impact — nécessite déjà une authentification valide, et les UUIDs ne sont pas devinables.
**Plan** : v0.9 — converger vers `tenant_query(db, Model, current_user).filter(id=id).first()` qui retourne 404 uniformément.

---

## Outils de scan intégrés

### Bandit (SAST Python)
- Installé dans le venv : `bandit==1.9.4`
- Workflow CI : `.github/workflows/security-scan.yml` (job `bandit-sast`)
- Seuil de failure : HIGH severity
- Résultat actuel : **0 findings** sur `backend/app/`

### pip-audit (dépendances Python)
- Workflow CI : `.github/workflows/security-scan.yml` (job `pip-audit`)
- Scanne `backend/requirements.txt` contre OSV
- Seuil actuel : warn-only (sera fail en v0.9)

### npm audit (dépendances frontend)
- Workflow CI : `.github/workflows/security-scan.yml` (job `npm-audit`)
- Scanne `frontend/package-lock.json`
- Seuil actuel : warn-only sur HIGH/CRITICAL (sera fail en v0.9)

---

## Tests automatisés

**Nouveau fichier** : `backend/tests/test_security_hardening.py` — 26 tests couvrant :
- `TestPasswordHashNotExposed` (4) — password_hash jamais exposé
- `TestRBACSuperAdminOnly` (4) — ADMIN ne peut pas muter RBAC global
- `TestActivitySuperAdminOnly` (1) — ADMIN ne peut pas lire /activity
- `TestNotificationSendTenantIsolation` (1) — ADMIN ne peut pas envoyer cross-facility
- `TestAccountLockout` (2) — verrouillage après 5 échecs + reset sur succès
- `TestPasswordPolicy` (5) — complexité mot de passe
- `TestAuditLogOnMutations` (6) — audit trail des mutations
- `TestAuthSecretValidation` (3) — hard-fail AUTH_SECRET en prod

**Total backend** : 161 tests (135 + 26 nouveaux), tous verts.

---

## Checklist OWASP Top 10 (2021) — statut après v0.8.0

| ID  | Catégorie                              | Statut |
|-----|----------------------------------------|--------|
| A01 | Broken Access Control                  | ✅ Critique + High corrigés ; 1 LOW accepté |
| A02 | Cryptographic Failures                 | ✅ password_hash masqué ; bcrypt + HS256 OK |
| A03 | Injection                              | ✅ Aucune injection SQL (SAST clean) |
| A04 | Insecure Design                        | ✅ Lockout + password policy + rate-limit refresh |
| A05 | Security Misconfiguration              | ✅ AUTH_SECRET hard-fail ; 3 LOW acceptés |
| A06 | Vulnerable & Outdated Components       | ⏳ pip-audit + npm-audit en warn-only (v0.9 : fail) |
| A07 | Identification & Auth Failures         | ✅ Lockout ; ⏳ jti blacklist pour v0.9 |
| A08 | Software & Data Integrity Failures     | ✅ Pas d'eval/exec/pickle/yaml.load |
| A09 | Security Logging & Monitoring          | ✅ Audit log complet sur mutations sensibles |
| A10 | SSRF                                   | ✅ Pas de requêtes HTTP basées sur input utilisateur |
