# Guide Postman — GuinéeCare Hospital Suite v0.10.0

Ce guide explique comment importer et utiliser la collection Postman générée automatiquement pour tester l'API GuinéeCare.

## 1. Fichiers fournis

| Fichier | Description |
|---------|-------------|
| `docs/api/guineecare.postman_collection.json` | Collection Postman v2.1 (138 endpoints groupés en 25 dossiers) |
| `docs/api/guineecare-local.postman_environment.json` | Environnement local (localhost:8000, comptes de test) |

Ces fichiers sont **générés** par `scripts/generate_openapi_artifacts.py` à partir de l'OpenAPI statique — ne pas les modifier à la main.

## 2. Import dans Postman

1. Ouvrez Postman (v10+).
2. **File → Import** :
   - Sélectionnez `guineecare.postman_collection.json`.
   - Sélectionnez `guineecare-local.postman_environment.json`.
3. Activez l'environnement **GuinéeCare - Local** (en haut à droite).
4. La collection **GuinéeCare Hospital Suite API** apparaît dans la sidebar.

## 3. Variables d'environnement

| Variable | Valeur par défaut (local) | Description |
|----------|---------------------------|-------------|
| `host` | `localhost:8000` | Hôte backend |
| `base_url` | `http://localhost:8000/api/v1` | Base URL (sans trailing slash) |
| `access_token` | *(vide — auto-rempli)* | JWT access token (60 min) |
| `refresh_token` | *(vide — auto-rempli)* | JWT refresh token (30 jours) |
| `access_token_exp` | `0` | Timestamp d'expiration (pour auto-refresh futur) |
| `admin_email` | `admin@guineecare.com` | Email compte SUPER_ADMIN |
| `admin_password` | `admin123` | Mot de passe SUPER_ADMIN |
| `doctor_email` | `dr.diallo@chu-donka.gn` | Email compte DOCTOR |
| `doctor_password` | `doctor123` | Mot de passe DOCTOR |

## 4. Authentification automatique

La collection inclut un **script de test** Postman exécuté après chaque requête :

```javascript
if (pm.request.url.path.includes('auth/login') || pm.request.url.path.includes('auth/refresh')) {
    const json = pm.response.json();
    if (json.access_token) {
        pm.environment.set('access_token', json.access_token);
        pm.environment.set('access_token_exp', Date.now() + 59 * 60 * 1000);
    }
    if (json.refresh_token) {
        pm.environment.set('refresh_token', json.refresh_token);
    }
}
pm.test('Status 2xx', () => pm.expect(pm.response.code).to.be.within(200, 299));
```

**Résultat** : après avoir appelé `Auth > Login`, les variables `access_token` et `refresh_token` sont automatiquement renseignées. Toutes les autres requêtes utilisent `Bearer {{access_token}}` dans le header `Authorization`.

## 5. Démarrage rapide

### Scénario : liste des patients en tant que SUPER_ADMIN

1. **Démarrer le backend** localement :
   ```bash
   cd backend
   source .venv/bin/activate
   DATABASE_URL="sqlite:///./dev_guineecare.db" AUTH_SECRET="dev-secret-key-2025" \
   ENVIRONMENT=local SEED_DEMO_DATA=true python -m uvicorn app.main:app --reload
   ```

2. Dans Postman, ouvrez la collection → dossier **Auth** → **Login**.
3. Le body est pré-rempli avec `{{admin_email}}` / `{{admin_password}}`. Cliquez sur **Send**.
4. Vérifiez que la réponse contient `access_token` et `refresh_token`.
5. Ouvrez **Patients** → **List patients** → **Send**.
   → Vous devriez recevoir un tableau paginé de patients.

### Scénario : cross-tenant refusé

1. Connectez-vous en tant que `dr.diallo@chu-donka.gn` (DOCTOR CHU Donka).
2. Essayez d'accéder à `GET /api/v1/facilities` → 403 (DOCTOR n'a pas la permission `facilities.read`).
3. Essayez `GET /api/v1/patients?facility_id=<id CHU Ignace>` → 403 (cross-tenant refusé).

## 6. Structure de la collection

La collection est organisée en 25 dossiers, correspondant aux tags OpenAPI :

| Dossier | Nb endpoints | Dossier | Nb endpoints |
|---------|--------------|---------|--------------|
| System API | 1 | Pharmacy API | 5 |
| Auth API | 4 | Laboratory API | 7 |
| Users API | 5 | Imaging API | 8 |
| Rbac API | 5 | Surgery API | 10 |
| Facilities API | 4 | Billing API | 7 |
| Departments API | 2 | Personnel API | 15 |
| Patients API | 3 | Quality API | 8 |
| Admissions API | 3 | Reporting API | 11 |
| Emergency API | 6 | Audit API | 2 |
| Hospitalization API | 8 | Activity API | 1 |
| Clinical API | 6 | Notifications API | 6 |
| Maternity API | 7 | Health API | 3 |
| | | Metrics API | 1 |

## 7. Runner Postman

Pour exécuter toute la collection en batch :

1. Cliquez sur la collection → **Run collection**.
2. Sélectionnez l'environnement **GuinéeCare - Local**.
3. Cochez **Save responses** pour le debug.
4. Cliquez **Run GuinéeCare Hospital Suite API**.

> ⚠️ Certaines routes nécessitent des IDs d'entités créées par d'autres routes (ex: `POST /patients` puis `GET /patients/{id}`). Pour ces chaînes, créez un folder dédié ou utilisez le Newman CLI avec un data file JSON.

## 8. Newman (CLI)

```bash
npm install -g newman
newman run docs/api/guineecare.postman_collection.json \
  -e docs/api/guineecare-local.postman_environment.json \
  --reporters cli,htmlextra \
  --reporter-htmlextra-export newman-report.html
```

## 9. Régénération après modification d'API

À chaque modification d'endpoint :

```bash
python scripts/generate_openapi_artifacts.py
git add docs/api/guineecare.postman_collection.json docs/api/openapi.json
git commit -m "docs(api): regenerate openapi + postman after <feature>"
```

Le CI `openapi-check.yml` vérifiera automatiquement que les fichiers sont à jour.

## 10. Astuces

- **Path params** : Postman utilise `{{id}}` comme variable. Renseignez la valeur dans l'onglet **Path Variables** de la requête, ou utilisez une variable d'environnement `id`.
- **Refresh automatique** : si l'access_token expire (401), appelez `Auth > Refresh` pour en obtenir un nouveau sans se reconnecter.
- **Multi-tenant testing** : créez un environnement par établissement (CHU Donka, CHU Ignace) avec des credentials différents pour tester le RBAC.
- **Audit log** : après une mutation (POST/PUT/DELETE), consultez `Audit > List audit logs` pour vérifier que l'action a bien été journalisée.
