# GuinéeCare Hospital Suite v1.4.0 — Patch de livraison

Cette livraison contient les **2 premières évolutions moyen terme** de la
roadmap v1.4 : le **module SMS réel** (Orange/MTN/Moov) et le **tableau de
bord qualité avancé** avec seuils d'alerte automatiques.

## Statut

- **Version cible** : v1.3.0 → v1.4.0
- **Date** : 2026-06-21
- **Tests backend** : 49 nouveaux tests (27 SMS + 22 quality dashboard), tous au vert
- **Build frontend** : validé par `npx vite build` (sortie `dist/` correcte)
- **Aucun test existant cassé** : 119 tests de non-régression passent

## Contenu

### Fichiers modifiés (13)
- `CHANGELOG.md` — section v1.4.0 ajoutée en haut
- `README.md` — badge version + description v1.4.0
- `backend/app/main.py` — version bump + nouveaux routers + nouveaux tags OpenAPI
- `backend/app/modules/rbac/seed.py` — 2 nouvelles permissions + `quality.dashboard` ajoutée à DOCTOR/NURSE
- `backend/requirements.txt` — `requests==2.32.3` ajouté
- `backend/tests/conftest.py` — import des 5 nouveaux modèles
- `docs/post-pilot/EVOLUTIONS_POST_PILOTE.md` — section v1.4.0 ajoutée
- `frontend/src/App.tsx` — route `/sms-admin`
- `frontend/src/components/ProtectedRoute.tsx` — flag `canSeeSmsAdmin`
- `frontend/src/hooks/useLookupData.ts` — fetch `/quality/indicators`
- `frontend/src/layout/Sidebar.tsx` — entrée SMS Admin (icône MessageSquare)
- `frontend/src/pages/QualityPage.tsx` — onglets Dashboard + Alertes
- `frontend/src/types.ts` — `indicators: Row[]` dans `LookupData`

### Fichiers nouveaux (16)

**Backend SMS** (`backend/app/modules/notifications/`) :
- `sms_models.py` — SmsProvider, SmsMessage, SmsRoutingRule
- `sms_provider.py` — Mock / Orange / MTN / Moov + normalize_phone_gn + encrypt_credential
- `sms_service.py` — send_sms, retry_failed_sms, get_sms_stats, seed defaults
- `sms_schemas.py` — schémas Pydantic
- `sms_routes.py` — 14 endpoints sous `/api/v1/notifications/sms/*`

**Backend Quality Dashboard** (`backend/app/modules/quality/`) :
- `dashboard_models.py` — QualityThreshold, QualityAlert + evaluate_threshold
- `dashboard_service.py` — compute_dashboard, check_thresholds, seed defaults
- `dashboard_schemas.py` — schémas Pydantic
- `dashboard_routes.py` — 11 endpoints sous `/api/v1/quality/*`

**Migrations Alembic** :
- `backend/alembic/versions/0017_sms_v14.py` — 3 tables SMS
- `backend/alembic/versions/0018_quality_dashboard.py` — 2 tables qualité

**Tests backend** :
- `backend/tests/test_sms.py` — 27 tests
- `backend/tests/test_quality_dashboard.py` — 22 tests

**Frontend** :
- `frontend/src/pages/SmsAdminPage.tsx` — page admin SMS (4 onglets)
- `frontend/src/pages/QualityDashboardTab.tsx` — onglet dashboard qualité
- `frontend/src/pages/QualityAlertsTab.tsx` — onglet alertes + seuils

## Installation

### Option A — Appliquer le patch sur votre repo local

```bash
# 1. Dans votre clone local du dépôt
cd /path/to/guineecare-hospital-suite

# 2. Créer une branche v1.4.0
git checkout -b v1.4.0-sms-quality

# 3. Appliquer le patch des fichiers modifiés
git apply v1.4.0_modified.patch

# 4. Copier les nouveaux fichiers (préservant la structure)
cp -r new_files/* .

# 5. Vérifier que tout est bien en place
git status
git add .
git commit -m "v1.4.0: SMS réel (Orange/MTN/Moov) + dashboard qualité avancé"
```

### Option B — Copier les fichiers manuellement

Pour chaque fichier modifié, recopiez le contenu depuis le patch ou
depuis le clone `/home/z/my-project/guineecare-hospital-suite/`. Pour
chaque nouveau fichier, créez-le à l'emplacement indiqué.

## Post-installation

### Backend

```bash
cd backend

# Si vous utilisez un venv existant, ajoutez requests
pip install requests==2.32.3

# Appliquer les migrations Alembic (PostgreSQL production)
alembic upgrade head

# En dev/test (SQLite), les tables sont créées automatiquement par
# Base.metadata.create_all() au démarrage de l'app.

# Lancer les tests
python -m pytest tests/test_sms.py tests/test_quality_dashboard.py -v
```

### Frontend

```bash
cd frontend
npm install   # pas de nouvelle dépendance npm
npm run build # vérifier que le build passe
npm run dev   # démarrer en dev
```

### Variables d'environnement (optionnelles)

```bash
# Chiffrement des credentials SMS (recommandé en production)
# Générez une clé avec : python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
export SMS_FERNET_KEY="votre-clé-fernet-base64"

# Log JSONL des SMS mock (utile en démo)
export SMS_MOCK_LOG="/var/log/guineecare/sms_mock.jsonl"
```

## Configuration initiale

### 1. Activer un provider SMS réel (Orange par exemple)

```bash
# Via l'UI : page "SMS Admin" → onglet "Providers" → "+ Nouveau provider"
# Ou via l'API :
curl -X POST http://localhost:8000/api/v1/notifications/sms/providers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "orange",
    "name": "Orange Guinée SMS Pro",
    "api_url": "https://api.orange.com/smsmessaging/v1/outbound/tel%3A%2B{sender}/requests",
    "api_key": "VOTRE_CLIENT_ID",
    "api_secret": "VOTRE_CLIENT_SECRET",
    "sender_id": "GUINEECARE",
    "cost_per_sms_gnf": 25
  }'
```

### 2. Tester le provider

```bash
curl -X POST http://localhost:8000/api/v1/notifications/sms/providers/{provider_id}/test \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"to": "+224622000000", "body": "Test GuinéeCare v1.4"}'
```

### 3. Seed des indicateurs OMS/HAS

```bash
# Via l'UI : page "Qualité" → onglet "Dashboard" → bouton "📚 Seed OMS/HAS"
# Ou via l'API :
curl -X POST "http://localhost:8000/api/v1/quality/seed-defaults?facility_id=$FACILITY_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Déclencher le check des seuils

```bash
# Via l'UI : page "Qualité" → onglet "Dashboard" → bouton "🔔 Check seuils"
# Ou via l'API :
curl -X POST http://localhost:8000/api/v1/quality/alerts/check \
  -H "Authorization: Bearer $TOKEN"
```

## Endpoints exposés

### SMS (`/api/v1/notifications/sms/*`)
- `GET /providers` — liste (credentials masqués)
- `GET /providers/supported` — catalogue statique
- `POST /providers` — création (credentials chiffrés)
- `PATCH /providers/{id}` — mise à jour
- `DELETE /providers/{id}` — suppression (mock protégé)
- `POST /providers/{id}/test` — test d'envoi
- `GET /rules` — liste des règles de routage
- `POST /rules` — création
- `PATCH /rules/{id}` — mise à jour
- `DELETE /rules/{id}` — suppression
- `POST /send` — envoi manuel
- `POST /messages/{id}/retry` — retry
- `GET /messages` — historique paginé
- `GET /stats?days=30` — statistiques

### Quality Dashboard (`/api/v1/quality/*`)
- `GET /dashboard?days=30` — dashboard agrégé
- `GET /indicators/catalog` — catalogue OMS/HAS
- `POST /seed-defaults?facility_id=...` — seed indicateurs + seuils
- `GET /thresholds` — liste seuils
- `POST /thresholds` — création
- `PATCH /thresholds/{id}` — mise à jour
- `DELETE /thresholds/{id}` — suppression
- `GET /alerts?status=...` — liste alertes
- `POST /alerts/check` — évaluation manuelle
- `POST /alerts/{id}/acknowledge` — prise en charge
- `POST /alerts/{id}/resolve` — résolution avec note
- `POST /alerts/{id}/close` — clôture

## Prochaines étapes (v1.5)

Les 3 évolutions moyen terme restantes sont reportées à v1.5 :
- Application mobile Android (React Native) — 30 j-h
- Interopérabilité HL7 FHIR R4 — 25 j-h
- Module RH v2 (plannings/gardes) — 18 j-h

Voir `docs/post-pilot/EVOLUTIONS_POST_PILOTE.md` pour le détail.

## Points d'attention production

1. **Credentials SMS** : utilisez `SMS_FERNET_KEY` en production pour chiffrer
   les credentials Orange/MTN/Moov au repos. Sans cette clé, les credentials
   sont stockés en clair (acceptable en dev/test uniquement).

2. **Job Celery pour `check_thresholds()`** : en production, l'évaluation des
   seuils devrait être automatisée via un job Celery horaire. Actuellement,
   l'endpoint `POST /quality/alerts/check` est appelé manuellement depuis
   l'UI. Configurer un beat Celery :
   ```python
   crontab(hour="*", minute="0")  # toutes les heures
   ```

3. **Quotas opérateurs** : vérifier les quotas SMS quotidiens auprès de
   chaque opérateur (Orange Guinée propose généralement 10 000 SMS/jour
   en SMS Pro). Le champ `daily_quota` du modèle `SmsProvider` permet de
   suivre cette limite — mais l'application ne bloque pas encore l'envoi
   au-delà (à implémenter en v1.5 si besoin).

4. **RGPD/PII** : le corps des SMS est stocké dans `sms_messages.body`. Pour
   les SMS contenant des données patient sensibles, prévoir une rétention
   limitée (90 jours) via un job de purge.

5. **Audit** : chaque envoi SMS via `POST /notifications/sms/send` écrit
   une entrée dans `audit_logs` (action `sms.send_manual`). Les envois
   automatiques (déclenchés par `notify()`) ne journalisent pas
   d'entrée d'audit (le `SmsMessage` lui-même sert de journal).
