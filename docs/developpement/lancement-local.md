# Lancement local — GuinéeCare Hospital Suite

## Objectif

Permettre à un développeur de lancer rapidement le socle MVP en local.

## Prérequis

- Git
- Docker
- Docker Compose
- Python 3.11
- Node.js pour le frontend futur

## Lancer avec Docker

```bash
docker compose up --build
```

API disponible :

- http://localhost:8000/health
- http://localhost:8000/api/v1
- http://localhost:8000/docs

## Lancer le backend sans Docker

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Initialiser les données de démonstration

Après démarrage de PostgreSQL :

```bash
cd backend
python -m app.db.seed
```

Le seed crée :

- l'établissement CHU Donka ;
- les services Urgences, Maternité, Médecine générale, Laboratoire, Pharmacie, Caisse ;
- un patient de démonstration.

## Endpoints MVP disponibles

- GET `/health`
- GET `/api/v1`
- GET `/api/v1/facilities`
- POST `/api/v1/facilities`
- GET `/api/v1/departments`
- POST `/api/v1/departments`
- GET `/api/v1/patients`
- POST `/api/v1/patients`
- GET `/api/v1/admissions`
- POST `/api/v1/admissions`
- POST `/api/v1/admissions/{id}/close`
- GET `/api/v1/emergency/queue`
- GET `/api/v1/pharmacy/stock`
- GET `/api/v1/laboratory/tests`
- GET `/api/v1/billing/invoices`

## Tests

```bash
cd backend
pytest
```

## État technique actuel

- FastAPI en place.
- PostgreSQL via Docker Compose.
- SQLAlchemy configuré.
- Initialisation automatique des tables MVP au démarrage.
- Modèles MVP : Facility, Department, Patient, Admission.
- Routes DB : facilities, departments, patients, admissions.
- Routes temporaires : emergency, pharmacy, laboratory, billing.

## Prochaine étape technique

- Ajouter Alembic pour les migrations propres.
- Ajouter l'authentification JWT.
- Ajouter les modèles utilisateurs, rôles et permissions.
- Remplacer les routes temporaires par des routes reliées à la base.
- Ajouter le frontend React.
