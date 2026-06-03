# Tests backend

## Objectif

Valider automatiquement le socle API, l'authentification, le RBAC et les premiers parcours MVP.

## Commande

Depuis le dossier `backend` :

```bash
pytest
```

## Tests disponibles

### Santé API

- `test_health_check`
- `test_api_root`

### Authentification

- utilisateur inconnu rejeté ;
- accès `/auth/me` sans token rejeté ;
- création du premier super administrateur ;
- login JWT ;
- appel `/auth/me` avec token ;
- mauvais mot de passe rejeté.

### Contrôle d'accès

Routes rejetées sans token :

- `/api/v1/patients`
- `/api/v1/admissions`
- `/api/v1/facilities`
- `/api/v1/departments`

### Accès autorisé

Avec un token `SUPER_ADMIN` :

- création et liste des établissements ;
- création patient ;
- création admission ;
- clôture admission.

## Base de test

Les tests utilisent une base SQLite locale `test_guineecare.db` et réinitialisent les tables à chaque test.

## Prochaines améliorations

- Remplacer SQLite par PostgreSQL de test via Docker.
- Ajouter tests RBAC par rôle métier.
- Ajouter tests du journal d'activité.
- Ajouter tests de migrations Alembic.
- Ajouter pipeline CI GitHub Actions quand disponible.
