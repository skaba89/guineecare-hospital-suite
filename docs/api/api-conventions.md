# Conventions API

## Versioning

Toutes les routes MVP utilisent le préfixe :

`/api/v1`

## Format des réponses

Réponse standard de succès :

```json
{
  "data": {},
  "message": "success"
}
```

Réponse d'erreur :

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Description de l'erreur",
    "details": []
  }
}
```

## Pagination

Les listes doivent accepter :

- page
- page_size
- search
- sort
- filters

## Sécurité

- JWT obligatoire pour les routes protégées.
- Vérification du rôle.
- Vérification de l'établissement.
- Vérification des permissions.
- Audit pour les actions sensibles.

## Endpoints MVP

### Auth

- POST `/api/v1/auth/login`
- POST `/api/v1/auth/refresh`
- POST `/api/v1/auth/logout`
- GET `/api/v1/auth/me`

### Patients

- POST `/api/v1/patients`
- GET `/api/v1/patients`
- GET `/api/v1/patients/{id}`
- PATCH `/api/v1/patients/{id}`

### Admissions

- POST `/api/v1/admissions`
- GET `/api/v1/admissions`
- GET `/api/v1/admissions/{id}`
- POST `/api/v1/admissions/{id}/close`

### Clinical

- GET `/api/v1/clinical/patients/{patient_id}/summary`
- POST `/api/v1/clinical/observations`
- POST `/api/v1/clinical/vitals`
- POST `/api/v1/clinical/diagnoses`

### Emergency

- POST `/api/v1/emergency/visits`
- POST `/api/v1/emergency/visits/{id}/triage`
- GET `/api/v1/emergency/queue`
- POST `/api/v1/emergency/visits/{id}/orientation`

### Billing

- POST `/api/v1/billing/invoices`
- POST `/api/v1/billing/invoices/{id}/payments`
- GET `/api/v1/billing/payments/{id}/receipt`
