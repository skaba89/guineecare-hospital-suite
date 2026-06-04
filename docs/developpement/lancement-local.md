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
- un patient de démonstration ;
- un compte super administrateur de démonstration.

Compte démo :

```text
Email: admin@guineecare.local
Password: admin123
Role: SUPER_ADMIN
```

## Authentification

Connexion :

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.local","password":"admin123"}'
```

Utiliser ensuite le token retourné :

```bash
curl http://localhost:8000/api/v1/patients \
  -H "Authorization: Bearer <token>"
```

## Endpoints MVP disponibles

- GET `/health`
- GET `/api/v1`
- POST `/api/v1/auth/login`
- GET `/api/v1/auth/me`
- GET `/api/v1/users`
- POST `/api/v1/users`
- GET `/api/v1/rbac/roles`
- GET `/api/v1/rbac/permissions`
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
- POST `/api/v1/emergency/visits`
- POST `/api/v1/emergency/visits/{id}/triage`
- POST `/api/v1/emergency/visits/{id}/orientation`
- GET `/api/v1/pharmacy/products`
- POST `/api/v1/pharmacy/products`
- GET `/api/v1/pharmacy/stock`
- POST `/api/v1/pharmacy/stock/movements`
- GET `/api/v1/laboratory/tests`
- POST `/api/v1/laboratory/tests`
- GET `/api/v1/laboratory/orders`
- POST `/api/v1/laboratory/orders`
- POST `/api/v1/laboratory/orders/{id}/results`
- POST `/api/v1/laboratory/results/{id}/validate`
- GET `/api/v1/billing/tariffs`
- POST `/api/v1/billing/tariffs`
- GET `/api/v1/billing/invoices`
- POST `/api/v1/billing/invoices`
- POST `/api/v1/billing/invoices/{id}/payments`
- GET `/api/v1/billing/payments/{id}/receipt`

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
- Modèles MVP : Facility, Department, Patient, Admission, User, Role, Permission, RolePermission.
- Modèles métier MVP : EmergencyVisit, PharmacyProduct, PharmacyStock, StockMovement, LabTest, LabOrder, LabResult, TariffItem, Invoice, Payment.
- Authentification JWT opérationnelle.
- RBAC avec rôles et permissions.
- Routes protégées : users, rbac, facilities, departments, patients, admissions, emergency, pharmacy, laboratory, billing.

## Prochaine étape technique

- Ajouter Alembic pour les migrations propres.
- Ajouter les tests d'intégration avec base de test.
- Ajouter le frontend React.
- Enrichir les modèles métier avec relations, contraintes et audit détaillé.
