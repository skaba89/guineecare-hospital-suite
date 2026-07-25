# Migrations Alembic — GuinéeCare Hospital Suite

## Objectif

Remplacer progressivement la création automatique des tables par des migrations versionnées, professionnelles et traçables.

## Pourquoi Alembic ?

Alembic permet de :

- versionner le schéma PostgreSQL ;
- rejouer les migrations sur plusieurs environnements ;
- revenir en arrière si nécessaire ;
- sécuriser les déploiements ;
- éviter les différences entre local, test, UAT et production.

## Structure

```text
backend/
  alembic.ini
  alembic/
    env.py
    script.py.mako
    versions/
      0001_initial_mvp_schema.py
      0002_mvp_business_modules.py
```

## Commandes principales

Depuis le dossier backend :

```bash
cd backend
```

Appliquer toutes les migrations :

```bash
alembic upgrade head
```

Voir la migration courante :

```bash
alembic current
```

Voir l'historique :

```bash
alembic history
```

Créer une migration automatique après modification des modèles :

```bash
alembic revision --autogenerate -m "describe change"
```

Créer une migration manuelle :

```bash
alembic revision -m "describe change"
```

Revenir à la migration précédente :

```bash
alembic downgrade -1
```

Revenir à zéro en local uniquement :

```bash
alembic downgrade base
```

## Variables d'environnement

Alembic lit `DATABASE_URL` si elle est définie :

```bash
export DATABASE_URL=postgresql://guineecare:guineecare@localhost:5432/guineecare
alembic upgrade head
```

## Migrations actuelles

### 0001_initial_mvp_schema

Crée les tables :

- facilities
- departments
- patients
- admissions
- users
- roles
- permissions
- role_permissions

### 0002_mvp_business_modules

Crée les tables :

- activity_entries
- emergency_visits
- pharmacy_products
- pharmacy_stock
- stock_movements
- lab_tests
- lab_orders
- lab_results
- tariff_items
- invoices
- payments

## Règle projet

En production, ne pas utiliser `Base.metadata.create_all()` pour faire évoluer la base.
Utiliser Alembic pour toutes les évolutions de schéma.

## Transition MVP

Pendant la phase MVP, `init_db()` peut rester utile pour accélérer le développement local.
Avant préproduction, il faudra :

1. désactiver la création automatique des tables au démarrage ;
2. lancer `alembic upgrade head` au déploiement ;
3. documenter chaque migration ;
4. tester les migrations en environnement de recette ;
5. interdire les modifications directes de schéma en production.
