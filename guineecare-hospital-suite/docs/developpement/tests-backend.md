# Tests backend

## Objectif

Valider automatiquement le socle API, l'authentification, le RBAC et les premiers parcours MVP.

## Commande

Depuis le dossier `backend`, lancer les tests avec Pytest.

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

### Journal d'activité

Les tests vérifient maintenant que les actions suivantes produisent une entrée dans `activity_entries` :

- création patient ;
- création admission ;
- clôture admission.

## Base de test

Les tests utilisent une base SQLite locale `test_guineecare.db` et réinitialisent les tables à chaque test.

## Correction email-validator

Si le backend affiche une erreur indiquant que `email_validator` est manquant, reconstruire l'image backend après mise à jour des dépendances. Le fichier `backend/requirements.txt` contient désormais `email-validator`, requis par `EmailStr` de Pydantic.

Étapes recommandées :

1. arrêter les conteneurs ;
2. reconstruire l'image backend sans cache ;
3. relancer les services ;
4. vérifier `/health` et `/docs`.

## Prochaines améliorations

- Remplacer SQLite par PostgreSQL de test via Docker.
- Ajouter tests RBAC par rôle métier.
- Ajouter tests de migrations Alembic.
- Ajouter pipeline CI GitHub Actions quand disponible.
