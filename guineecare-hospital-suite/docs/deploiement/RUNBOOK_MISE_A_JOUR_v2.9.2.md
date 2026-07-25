# Runbook — Mise à jour v2.9.2

**Projet :** GuinéeCare Hospital Suite
**Version cible :** 2.9.2 (depuis 2.8.9 / 2.9.0 / 2.9.1)
**Date :** Juillet 2026
**Durée estimée :** 1h30 à 2h (selon infrastructure)
**Classification :** Interne — Équipe technique
**Complexité :** 🟡 Moyenne (ajout Redis + Celery, sans casser l'existant)

---

## 1. Objectif

Ce runbook décrit la procédure de mise à jour de GuinéeCare Hospital Suite vers la version **2.9.2**, qui introduit :

1. **Redis** pour le rate limit partagé multi-instance
2. **Celery worker + beat** pour les tâches planifiées (pruning audit log, backup auto, push DHIS2, retry SMS)
3. **Module ICD-11** (catalogue OMS, ~80 codes)
4. **Mode sombre** frontend (toggle 🌙/☀️)
5. **Infinite scroll** (hook `useInfiniteScroll`)
6. **Documentation juridique** (DPO + cahier des charges pen test)

La mise à jour est **rétro-compatible** : si Redis ou Celery ne sont pas configurés, l'application continue de fonctionner en mode dégradé (rate limit en mémoire, tâches exécutables en synchrone via API).

---

## 2. Pré-requis

### 2.1 Environnement source

| Élément | Valeur minimale |
|---------|-----------------|
| Version actuelle | ≥ 2.8.9 |
| Backend Python | 3.12 |
| Frontend Node | 20+ |
| Base de données | PostgreSQL 16 (ou SQLite en dev) |
| Dernier backup DB | < 24h |
| Tests backend passent | ✅ 100% |

### 2.2 Compétences requises

- Administration Render (ou Docker selon infra)
- Administration PostgreSQL
- Notions Redis et Celery (concepts de base suffisent)
- Lecture de logs Python

### 2.3 Sauvegardes pré-mise à jour

```bash
# 1. Backup DB complet (Neon / PostgreSQL)
pg_dump $DATABASE_URL -Fc > /tmp/pre-v292-backup-$(date +%Y%m%d_%H%M%S).dump

# 2. Snapshot Render (si Render web service)
# → Dashboard Render → service → Settings → Create Snapshot

# 3. Sauvegarde variables d'environnement actuelles
render env:list > /tmp/pre-v292-envs.txt
# ou, sur VPS :
docker compose config | grep -A 1 environment > /tmp/pre-v292-envs.txt
```

---

## 3. Procédure de mise à jour

### 3.1 Phase 1 — Préparation (15 min)

#### 3.1.1 Vérifier l'état du système

```bash
# Health check backend
curl -s https://[votre-url]/health | jq .

# Doit retourner : {"status": "healthy", "version": "2.8.9" ou 2.9.x}

# Vérifier la queue SMS (v1.4.0) — si 0, OK
curl -s -H "Authorization: Bearer $TOKEN" \
  https://[votre-url]/api/v1/notifications/sms/messages?status=PENDING | jq .total
```

#### 3.1.2 Récupérer le code v2.9.2

```bash
cd /path/to/guineecare-hospital-suite
git fetch origin
git checkout v2.9.2  # ou le commit/branch correspondant
git log --oneline -5
# Vérifier que la version est bien 2.9.2 :
grep APP_VERSION backend/app/main.py
# Doit afficher : APP_VERSION = "2.9.2"
```

#### 3.1.3 Tests locaux avant déploiement

```bash
# Backend tests (doivent tous passer)
cd backend
source .venv/bin/activate
DATABASE_URL="sqlite:///./test_guineecare.db" \
AUTH_SECRET="test-secret-key-for-integration-tests" \
ENVIRONMENT=local \
pytest tests/ -q --tb=short

# Frontend typecheck + build
cd ../frontend
npx tsc --noEmit
npm run build
```

> ⚠️ Si un test échoue, NE PAS déployer en production. Investiguer d'abord.

---

### 3.2 Phase 2 — Déploiement sur Render (45 min)

#### 3.2.1 Créer le service Redis sur Render

1. **Dashboard Render** → New → Redis
2. **Configuration** :
   - Name : `guineecare-redis`
   - Region : `frankfurt` (même région que le backend)
   - Plan : `Starter` ($10/mois, recommandé) ou `Free` (25MB, démo)
3. **Create Redis**
4. **Copier l'URL de connexion** (`redis://:...@...`)

#### 3.2.2 Mettre à jour les variables d'environnement du backend Render

1. **Dashboard Render** → service `guineecare` → Environment
2. **Ajouter** les variables suivantes :

| Variable | Valeur | Notes |
|----------|--------|-------|
| `REDIS_URL` | `redis://:...@...` (URL du service Redis) | Connexion Redis Render |
| `CELERY_BROKER_URL` | (même valeur que `REDIS_URL`) | Broker Celery |
| `CELERY_RESULT_BACKEND` | (même valeur que `REDIS_URL`) | Résultats Celery |
| `AUDIT_LOG_RETENTION_DAYS` | `365` | Rétention RGPD (jours) |
| `BACKUP_RETENTION_DAYS` | `30` | Rotation backups (jours) |
| `DHIS2_URL` | (optionnel) | `https://dhis2.sante.gov.gn` |
| `DHIS2_USERNAME` | (optionnel) | User DHIS2 |
| `DHIS2_PASSWORD` | (optionnel, sync=false) | Password DHIS2 |

3. **Save Changes**

#### 3.2.3 Créer le service Celery worker

1. **Dashboard Render** → New → Background Worker
2. **Configuration** :
   - Name : `guineecare-worker`
   - Runtime : Python
   - Region : `frankfurt`
   - Plan : `Starter` ($7/mois)
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `celery -A app.tasks.celery_app worker --loglevel=info -c 2 --max-tasks-per-child=100`
   - Root Directory : `backend`
3. **Environment** : copier les mêmes variables que le backend (DATABASE_URL, AUTH_SECRET, REDIS_URL, CELERY_*, AUDIT_LOG_RETENTION_DAYS, BACKUP_RETENTION_DAYS, DHIS2_*)
4. **Create Background Worker**

#### 3.2.4 Créer le service Celery beat

1. **Dashboard Render** → New → Background Worker
2. **Configuration** :
   - Name : `guineecare-beat`
   - Runtime : Python
   - Plan : `Starter` ($7/mois)
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `celery -A app.tasks.celery_app beat --loglevel=info`
   - Root Directory : `backend`
3. **Environment** : DATABASE_URL, AUTH_SECRET, REDIS_URL, CELERY_*
4. **Create Background Worker**

#### 3.2.5 Déployer le backend

1. **Dashboard Render** → service `guineecare` → Manual Deploy → Deploy latest commit
2. **Attendre** le build (~3-5 min)
3. **Vérifier** les logs au démarrage — doivent contenir :
   ```
   INFO: Rate limiter: storage Redis branché (partagé multi-instance)
   INFO: Redis connecté à ... — rate limit partagé multi-instance
   INFO: Application startup complete.
   ```

---

### 3.3 Phase 3 — Déploiement sur VPS Docker (alternative à Render)

Si vous déployez sur VPS avec Docker Compose :

```bash
# 1. Pull le nouveau code
cd /opt/guineecare-hospital-suite
git fetch origin && git checkout v2.9.2

# 2. Mettre à jour .env.production
# Ajouter les variables Redis/Celery :
cat >> .env.production << 'EOF'
# v2.9.2 — Redis + Celery
REDIS_PASSWORD=générer-une-chaine-aleatoire-32-caracteres
AUDIT_LOG_RETENTION_DAYS=365
BACKUP_RETENTION_DAYS=30
# DHIS2 (optionnel)
DHIS2_URL=
DHIS2_USERNAME=
DHIS2_PASSWORD=
EOF

# 3. Démarrer les nouveaux services
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d \
  celery-worker celery-beat redis

# 4. Vérifier le statut
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
# Tous les services doivent être "healthy" ou "running"
```

---

### 3.4 Phase 4 — Migration base de données (5 min)

La version 2.9.2 **n'introduit pas** de nouvelle migration Alembic (les tables `insurance_providers` et `patient_insurances` ont été créées en v2.9.1 via la migration `0029_v291_insurance`).

Si vous venez de v2.8.x ou antérieur :

```bash
# Sur Render : la migration est automatique via render_start.sh
# Sur VPS :
docker compose exec backend alembic upgrade head

# Vérifier la version
docker compose exec backend alembic current
# Doit afficher : 0029_v291_insurance (head)
```

---

### 3.5 Phase 5 — Validation post-déploiement (15 min)

#### 3.5.1 Health checks

```bash
# Backend
curl -s https://[votre-url]/health | jq .
# Attendu : {"status": "healthy", "version": "2.9.2", ...}

# Version API
curl -s https://[votre-url]/api/v1 | jq .version
# Attendu : "2.9.2"
```

#### 3.5.2 Validation Redis (rate limit partagé)

```bash
# Logs backend Render doivent montrer :
# "Rate limiter: storage Redis branché"
# Sinon, vérifier REDIS_URL et la connectivité Redis

# Test manuel : faire 6 logins rapides
for i in {1..6}; do
  curl -s -X POST https://[votre-url]/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}' \
    -o /dev/null -w "%{http_code}\n"
done
# Attendu : 401, 401, 401, 401, 401, 429 (rate limit déclenché)
```

#### 3.5.3 Validation Celery worker

```bash
# Lister les tâches disponibles
TOKEN=$(curl -s -X POST https://[votre-url]/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.com","password":"admin123"}' | jq -r .access_token)

curl -s -H "Authorization: Bearer $TOKEN" \
  https://[votre-url]/api/v1/tasks | jq .

# Attendu :
# {
#   "tasks": [
#     {"name": "prune_audit_logs", "path": "...", "async_enabled": true},
#     {"name": "backup_database", "path": "...", "async_enabled": true},
#     ...
#   ],
#   "celery_available": true,
#   "broker_url_configured": true
# }
```

#### 3.5.4 Test d'exécution d'une tâche (dry-run)

```bash
# Déclencher un backup manuellement
curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  https://[votre-url]/api/v1/tasks/trigger/backup_database | jq .

# Attendu :
# {
#   "task": "backup_database",
#   "status": "sync_executed",  # ou "submitted" si Celery async
#   "result": {
#     "backup_file": "...",
#     "size_bytes": 12345,
#     "rotation_deleted": 0
#   }
# }
```

#### 3.5.5 Validation ICD-11

```bash
# Recherche ICD-11
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://[votre-url]/api/v1/icd11/search?q=paludisme" | jq .

# Attendu : 2 résultats (1F03 Paludisme à P. falciparum + 1F2Z Paludisme non précisé)
```

#### 3.5.6 Validation mode sombre (frontend)

1. Aller sur `https://[votre-url]`
2. Se connecter en SUPER_ADMIN
3. Vérifier que le bouton 🌙 est visible dans le topbar (entre RealtimeStatus et LanguageToggle)
4. Cliquer → l'UI doit passer en sombre immédiatement
5. Recharger la page → le thème sombre doit persister

#### 3.5.7 Validation E2E Playwright (optionnel)

```bash
cd frontend
npx playwright test tests/e2e/v292-dark-mode.spec.ts
npx playwright test tests/e2e/v292-extended.spec.ts
# Tous les tests doivent passer
```

---

## 4. Rollback (procédure d'urgence)

### 4.1 Critères de rollback

Déclencher un rollback si :
- Backend ne démarre pas après 5 min
- Health check `https://[votre-url]/health` retourne 500 ou timeout
- Erreurs 500 en cascade sur les endpoints critiques (login, patients)
- Corruption de données (audit log, factures)

### 4.2 Procédure de rollback Render

```bash
# 1. Rollback backend vers la version précédente
# Dashboard Render → service guineecare → Manual Deploy → Deploy specific commit
# Sélectionner le dernier commit de la version 2.8.9 ou 2.9.0

# 2. Restaurer la DB si corruption
pg_restore -d $DATABASE_URL -c /tmp/pre-v292-backup-YYYYMMDD_HHMMSS.dump

# 3. Désactiver les workers Celery (les laisser tourner ne pose pas de problème,
# mais ils consomment des ressources inutilement)
# Dashboard Render → guineecare-worker → Suspend
# Dashboard Render → guineecare-beat → Suspend
```

### 4.3 Procédure de rollback VPS Docker

```bash
# 1. Revenir au commit précédent
cd /opt/guineecare-hospital-suite
git checkout v2.8.9  # ou la dernière version stable

# 2. Restaurer la DB
docker compose exec postgres pg_restore -U guineecare -d guineecare -c /backups/pre-v292-backup.dump

# 3. Redémarrer les services (sans les workers Celery)
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop celery-worker celery-beat
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d backend frontend nginx

# 4. Vérifier
curl -s https://[votre-url]/health | jq .version
# Doit afficher : "2.8.9" ou la version précédente
```

---

## 5. Post-mise à jour (J+1 à J+7)

### 5.1 Surveillance active (J+1 à J+3)

- [ ] Vérifier les logs backend Render chaque matin
  - Pas d'erreur `Redis connection failed`
  - Pas d'erreur `Celery task failed`
- [ ] Vérifier que le pruning audit log s'est exécuté à 03h00 UTC
  ```bash
  curl -s -H "Authorization: Bearer $TOKEN" \
    "https://[votre-url]/api/v1/audit/logs?action=system.audit_prune" | jq .
  ```
- [ ] Vérifier que le backup database s'est exécuté à 04h00 UTC
  ```bash
  curl -s -H "Authorization: Bearer $TOKEN" \
    "https://[votre-url]/api/v1/audit/logs?action=system.backup" | jq .
  ```
- [ ] Vérifier la taille du backup dans `/tmp/guineecare-backups/` (ou `/backups` en Docker)

### 5.2 Surveillance passive (J+4 à J+7)

- [ ] Métriques Prometheus : pas de pic d'erreurs 5xx
- [ ] Métriques Prometheus : latence médiane < 200ms
- [ ] Aucune alerte quality dashboard (page /quality)
- [ ] Aucune alerte SMS en échec (page /sms-admin)

### 5.3 Tâches administratives (J+7)

- [ ] Notifier le DPO de la mise à jour (nouveau module ICD-11 = nouveau traitement)
- [ ] Mettre à jour l'AIPD si nécessaire (ajout ICD-11 est un enrichissement, pas une nouvelle finalité)
- [ ] Prévoir une session de formation utilisateur sur le mode sombre (1 slide)
- [ ] Documenter les éventuels ajustements de configuration dans ce runbook

---

## 6. Troubleshooting

### 6.1 Backend ne démarre pas

**Symptôme** : Health check 500 ou timeout après déploiement

**Diagnostic** :
```bash
# Logs Render
Dashboard Render → service guineecare → Logs

# Chercher :
# - "FATAL: AUTH_SECRET must be set" → vérifier AUTH_SECRET
# - "ModuleNotFoundError: redis" → installer redis: pip install redis>=5.0
# - "Connection refused redis:6379" → vérifier REDIS_URL
```

**Solution** :
- Si `redis` manquant : ajouter `redis>=5.0` dans `backend/requirements.txt` et redéployer
- Si `REDIS_URL` incorrect : corriger dans Render Environment et redéployer
- Si AUTH_SECRET vide : le définir (sync: false) — ne jamais committer

### 6.2 Redis non connecté (rate limit en mémoire)

**Symptôme** : Logs backend affichent `Rate limiter: storage mémoire (par worker)` au lieu de `storage Redis branché`

**Diagnostic** :
```bash
# Tester la connexion Redis manuellement
docker compose exec backend python -c "
from app.core.redis import get_redis_client
c = get_redis_client()
print('Redis client:', c)
if c:
    c.ping()
    print('PING OK')
"

# Logs Redis
docker compose logs redis | tail -20
```

**Solutions** :
- Vérifier que `REDIS_URL` est correctement formatée (`redis://:password@host:port/0`)
- Vérifier que le service Redis est démarré et sain
- Vérifier qu'il n'y a pas de firewall bloquant le port 6379

### 6.3 Celery worker ne traite pas les tâches

**Symptôme** : `celery_available: false` dans la réponse de `/api/v1/tasks`, ou tâches en statut PENDING indéfiniment

**Diagnostic** :
```bash
# Logs worker
Dashboard Render → guineecare-worker → Logs
# ou
docker compose logs celery-worker | tail -30

# Vérifier que le worker est connecté à Redis
docker compose exec celery-worker celery -A app.tasks.celery_app inspect ping
# Doit retourner : {"pong": "1"}
```

**Solutions** :
- Si worker crash : vérifier que `celery` est dans `requirements.txt`
- Si worker idle : vérifier que beat tourne (sinon, déclencher manuellement via API `/api/v1/tasks/trigger/{name}`)
- Si erreur de import : vérifier que `app.tasks.celery_app` est bien accessible

### 6.4 Mode sombre ne s'applique pas

**Symptôme** : Le bouton 🌙 est cliqué mais l'UI ne change pas

**Diagnostic** :
1. Ouvrir DevTools (F12) → Console
2. Vérifier qu'il n'y a pas d'erreur JavaScript
3. Inspecter `<html>` → vérifier l'attribut `data-theme`

**Solutions** :
- Vider le cache navigateur (Ctrl+Shift+R)
- Vider localStorage : `localStorage.clear()` puis recharger
- Vérifier que `ThemeProvider` est bien wrappé dans `main.tsx`

### 6.5 ICD-11 retourne 404

**Symptôme** : `GET /api/v1/icd11/search?q=...` retourne 404

**Diagnostic** :
```bash
# Vérifier que le router est bien enregistré
curl -s https://[votre-url]/api/v1/openapi.json | jq '.paths | keys[] | select(. | contains("icd11"))'
# Doit retourner :
# "/api/v1/icd11/categories"
# "/api/v1/icd11/search"
# "/api/v1/icd11/{code}"
```

**Solutions** :
- Si absent : le déploiement n'a pas pris en compte `app/modules/icd11/routes.py`. Vérifier le build.
- Si présent mais 404 : vérifier que `icd11_router` est bien inclus dans `main.py`

---

## 7. Métriques de succès

La mise à jour v2.9.2 est considérée comme **réussie** si :

| Métrique | Cible | Mesure |
|----------|-------|--------|
| Backend démarre | ✅ | `/health` retourne 200 avec `version: 2.9.2` |
| Redis connecté | ✅ | Logs : `storage Redis branché` |
| Celery worker actif | ✅ | `/api/v1/tasks` → `celery_available: true` |
| Tâche backup exécutable | ✅ | `/api/v1/tasks/trigger/backup_database` → 200 |
| ICD-11 fonctionnel | ✅ | `/api/v1/icd11/search?q=paludisme` → 200 + ≥1 résultat |
| Mode sombre fonctionne | ✅ | Bouton 🌙 visible, click change `data-theme` |
| Aucune erreur 500 | ✅ | Logs backend : 0 erreur sur 1h |
| Tests backend passent | ✅ | 280+ tests en CI |
| Tests E2E passent | ✅ | Playwright (24 parcours) |
| Latence API normale | ✅ | < 200ms p95 (mêmes qu'avant) |

---

## 8. Contacts

| Rôle | Contact | Disponibilité |
|------|---------|---------------|
| Lead dev GuinéeCare | tech@guinecare.gn | 9h-18h GMT |
| DSI Ministère | dsi@sante.gov.gn | 9h-17h GMT |
| DPO | dpo@sante.gov.gn | 9h-17h GMT |
| RSSI | rssi@sante.gov.gn | 9h-17h GMT |
| Support Render | support@render.com | 24/7 (ticket) |

---

## 9. Historique des versions de ce runbook

| Version | Date | Auteur | Modifications |
|---------|------|--------|---------------|
| 1.0 | 2026-07-14 | Équipe GuinéeCare | Version initiale (mise à jour 2.8.9 → 2.9.2) |
