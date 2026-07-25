# Guide OpenAPI — GuinéeCare Hospital Suite v0.10.0

Ce document explique comment l'API GuinéeCare est documentée avec **OpenAPI 3.1**, comment consulter la spécification, et comment éviter le *spec drift* en CI.

## 1. Vue d'ensemble

| Élément | Valeur |
|---------|--------|
| Version API | `v0.10.0` |
| Spécification OpenAPI | `3.1.0` |
| Endpoints documentés | 138 opérations sur 98 chemins |
| Tags | 25 (auth, users, rbac, patients, …, system) |
| Schémas de sécurité | `HTTPBearer` (JWT) |
| Serveurs déclarés | 3 (courant, localhost, production) |

## 2. Endpoints exposés

| URL | Type | Description |
|-----|------|-------------|
| `/api/v1/openapi.json` | JSON | Spécification OpenAPI 3.1 machine-lisible |
| `/docs` | Swagger UI | Interface interactive pour tester les endpoints |
| `/redoc` | ReDoc | Vue lecture seule, plus adaptée à la lecture |

> ℹ️ Les trois URLs sont publiques (pas de JWT requis) — elles ne révèlent aucune donnée métier, seulement la structure de l'API.

## 3. Métadonnées de documentation

Chaque endpoint documenté expose :

- **`summary`** (1 ligne) — titre court dans Swagger/ReDoc.
- **`description`** (optionnel) — explication détaillée, en Markdown.
- **`tags`** — catégorie pour grouper dans la doc (25 tags définis).
- **`parameters`** — query/path params typés avec description et exemple.
- **`requestBody`** — schéma Pydantic v2 avec exemples.
- **`responses`** — codes 200, 422, 401, 403, 429, 500 standardisés automatiquement (voir ci-dessous).

## 4. Enrichissement automatique (custom `openapi()`)

Plutôt que de déclarer manuellement les réponses `401/403/429/500` sur **chacune** des 137 routes protégées, GuinéeCare utilise une fonction `custom_openapi()` dans `backend/app/main.py` qui injecte automatiquement :

| Code | Injecté sur | Description |
|------|------------|-------------|
| 401 | Routes protégées | JWT manquant / expiré / révoqué |
| 403 | Routes protégées | Permission RBAC insuffisante / cross-tenant |
| 422 | Routes avec `requestBody` | Erreur validation Pydantic |
| 429 | Routes protégées | Rate limit dépassé (SlowAPI) |
| 500 | Routes protégées | Erreur serveur interne |

Et le security scheme `HTTPBearer` est attaché automatiquement à chaque opération non-publique, ce qui fait apparaître le bouton **Authorize** 🔓 dans Swagger UI.

### Routes publiques (sans authentification)

Les routes suivantes sont exemptées de l'enrichissement `401/403/429/500` :

- `/api/v1` (racine — version et modules)
- `/api/v1/auth/login`
- `/api/v1/auth/refresh`
- `/health`, `/health/live`, `/health/ready`
- `/metrics`
- `/docs`, `/redoc`, `/api/v1/openapi.json`

La liste est définie dans `_PUBLIC_PATHS` dans `main.py`.

## 5. Génération statique des artifacts

Le script `scripts/generate_openapi_artifacts.py` génère trois fichiers dans `docs/api/` :

```bash
cd /home/z/my-project/guineecare-hospital-suite
python scripts/generate_openapi_artifacts.py
```

| Fichier | Taille typique | Usage |
|---------|----------------|------|
| `openapi.json` | ~545 KB | Spécification OpenAPI 3.1 statique (versionnée dans Git) |
| `guineecare.postman_collection.json` | ~170 KB | Collection Postman v2.1 (importable) |
| `guineecare-local.postman_environment.json` | ~1 KB | Environnement Postman (variables locales) |

Ces artifacts sont **commités dans Git** pour deux raisons :

1. **Audit** — un reviewer peut lire la spec sans devoir démarrer le backend.
2. **CI drift detection** — le workflow `openapi-check.yml` régénère la spec et la compare au fichier commité ; si elles diffèrent, le CI échoue (voir section 7).

## 6. Workflow de mise à jour

Quand vous ajoutez/modifiez un endpoint :

1. **Codez** la route avec `@router.get(..., summary="...", description="...")`.
2. **Ajoutez** un `response_model=...` et un `responses={...}` si nécessaire pour les codes spécifiques (404, 409, etc.).
3. **Ne déclarez PAS** manuellement 401/403/429/500 — c'est injecté automatiquement.
4. **Exécutez** `python scripts/generate_openapi_artifacts.py` pour régénérer les artifacts.
5. **Committez** les fichiers `docs/api/openapi.json` + `guineecare.postman_collection.json` modifiés.

## 7. CI — détection de drift

Le workflow `.github/workflows/openapi-check.yml` s'exécute sur chaque PR :

```yaml
- name: Regenerate openapi.json
  run: python scripts/generate_openapi_artifacts.py
- name: Check for drift
  run: |
    if ! git diff --exit-code docs/api/openapi.json; then
      echo "::error::openapi.json drift détecté. Régénérez avec :"
      echo "::error::  python scripts/generate_openapi_artifacts.py"
      exit 1
    fi
```

Si un développeur modifie une route sans régénérer la spec, le CI échoue et lui rappelle la commande à exécuter.

## 8. Validation tests

Le test `backend/tests/test_openapi.py` valide au runtime que :

- ✅ Tous les endpoints ont au moins un tag.
- ✅ Tous les endpoints ont un `summary` non vide.
- ✅ Tous les endpoints protégés ont une réponse `401` déclarée.
- ✅ Tous les endpoints avec body ont une réponse `422` déclarée.
- ✅ Tous les endpoints protégés référencent `HTTPBearer` dans `security`.
- ✅ Le tag `system` est utilisé (sur la racine `/api/v1`).

## 9. Consultation interactive

### Swagger UI (`/docs`)

- Cliquez sur 🔓 **Authorize** → collez votre JWT.
- Toutes les routes protégées deviennent testables directement.
- Les exemples de body sont pré-remplis depuis les schémas Pydantic.

### ReDoc (`/redoc`)

- Vue lecture seule, plus ergonomique pour la documentation.
- Pas de test interactif, mais recherche full-text et arborescence par tag.

### Import dans un client tiers

- **Postman** : Import → `docs/api/guineecare.postman_collection.json` (+ environnement local).
- **Insomnia** : Import → `docs/api/openapi.json` (OpenAPI 3.1 natif).
- **Hoppscotch** : Import → `docs/api/openapi.json`.
- **curl** : un script de génération `curl` peut être dérivé de l'OpenAPI (ex: `openapi-generator-cli`).

## 10. Bonnes pratiques

- **Toujours** fournir un `summary` court et descriptif (max 60 caractères).
- **Éviter** les descriptions trop verbeuses — Swagger les affiche en entier.
- **Toujours** déclarer `response_model` sur les GET qui retournent des données structurées.
- **Ne pas** dupliquer les réponses 401/403/422 — c'est géré centralisé.
- **Toujours** régénérer les artifacts avant de committer une modification de routes.
