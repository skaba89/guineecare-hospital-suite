# Lancement local — GuinéeCare Hospital Suite

## Objectif

Permettre à un développeur de lancer rapidement le socle MVP en local.

## Prérequis

- Git
- Docker
- Docker Compose
- Python 3.11
- Node.js pour le frontend futur

## Lancer le backend sans Docker

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API disponible :

- http://localhost:8000/health
- http://localhost:8000/api/v1
- http://localhost:8000/docs

## Lancer avec Docker

```bash
docker compose up --build
```

## Endpoints MVP disponibles

- GET `/health`
- GET `/api/v1`
- GET `/api/v1/patients`
- POST `/api/v1/patients`
- GET `/api/v1/admissions`
- POST `/api/v1/admissions`
- GET `/api/v1/emergency/queue`
- GET `/api/v1/pharmacy/stock`
- GET `/api/v1/laboratory/tests`
- GET `/api/v1/billing/invoices`

## Prochaine étape technique

- Ajouter SQLAlchemy.
- Ajouter les migrations Alembic.
- Ajouter PostgreSQL.
- Ajouter l'authentification JWT.
- Ajouter les tests automatisés.
