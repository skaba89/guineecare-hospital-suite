# Backend — GuinéeCare Hospital Suite

Backend API de la plateforme hospitalière.

## Stack cible

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- JWT
- RBAC

## Lancement local prévu

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Modules MVP

- auth
- facilities
- users
- patients
- admissions
- clinical
- emergency
- hospitalization
- pharmacy
- laboratory
- billing
- reporting
