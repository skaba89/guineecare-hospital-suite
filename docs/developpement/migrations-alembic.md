# Migrations Alembic

## Objectif

Remplacer progressivement la création automatique des tables par des migrations versionnées et traçables.

## Fichiers ajoutés

- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/script.py.mako`
- `backend/alembic/versions/0001_initial_mvp_schema.py`

## Commandes utiles

Depuis le dossier `backend` :

```bash
alembic upgrade head
```

Créer une nouvelle migration automatiquement :

```bash
alembic revision --autogenerate -m "message"
```

Créer une migration manuelle :

```bash
alembic revision -m "message"
```

Revenir en arrière :

```bash
alembic downgrade -1
```

## Stratégie recommandée

Phase actuelle : `create_all()` reste actif pour faciliter le développement local.

Phase suivante :

1. Stabiliser les modèles.
2. Lancer Alembic en local.
3. Supprimer progressivement `create_all()` du démarrage.
4. Utiliser uniquement les migrations en dev, test, UAT et production.

## Tables de la migration initiale

- facilities
- departments
- patients
- admissions
- users
- roles
- permissions
- role_permissions
