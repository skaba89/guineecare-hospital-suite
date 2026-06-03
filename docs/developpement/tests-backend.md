# Tests backend

## Objectif

Valider automatiquement les routes critiques du backend MVP.

## Lancer les tests

Depuis le dossier `backend` :

```bash
pytest
```

## Tests actuellement couverts

- `GET /health`
- `GET /api/v1`
- refus sans token sur les routes protégées :
  - patients
  - admissions
  - facilities
  - departments
- refus login avec utilisateur inconnu
- refus `/auth/me` sans token

## Stratégie de tests cible

1. Tests unitaires de services.
2. Tests d'intégration API.
3. Tests RBAC.
4. Tests d'audit activité.
5. Tests E2E métier.

## À ajouter ensuite

- Base SQLite isolée pour tests.
- Création bootstrap super admin.
- Login réussi.
- Accès autorisé avec token.
- Tests de permissions par rôle.
