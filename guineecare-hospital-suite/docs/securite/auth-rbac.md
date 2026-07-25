# Authentification et RBAC — GuinéeCare Hospital Suite

## Objectif

Sécuriser l'accès à la plateforme avec une authentification JWT et un contrôle d'accès par rôle et permission.

## Concepts

### Utilisateur

Un utilisateur représente une personne autorisée à se connecter à la plateforme.

Champs principaux :

- email
- mot de passe chiffré
- prénom
- nom
- établissement
- rôle
- statut actif/inactif

### Rôle

Un rôle représente une responsabilité métier ou technique.

Rôles MVP :

- SUPER_ADMIN
- ADMIN
- DOCTOR
- NURSE
- PHARMACIST
- LAB_TECH
- CASHIER

### Permission

Une permission représente une action autorisée.

Exemples :

- patient.read
- patient.create
- admission.read
- admission.create
- admission.close
- facility.read
- facility.manage
- department.read
- department.manage

## Endpoints Auth

### Login

POST `/api/v1/auth/login`

Payload :

```json
{
  "email": "admin@guineecare.com",
  "password": "admin123"
}
```

Réponse :

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "...",
    "role": "SUPER_ADMIN",
    "facility_id": "..."
  }
}
```

### Utilisateur courant

GET `/api/v1/auth/me`

Header :

```text
Authorization: Bearer <token>
```

## Bootstrap premier utilisateur

POST `/api/v1/users/bootstrap`

Ce endpoint permet de créer le premier super administrateur uniquement si aucun utilisateur n'existe encore.

## Administration des utilisateurs

- GET `/api/v1/users`
- POST `/api/v1/users`

Ces endpoints nécessitent le rôle `SUPER_ADMIN` ou `ADMIN`.

## Administration RBAC

- GET `/api/v1/rbac/roles`
- POST `/api/v1/rbac/roles`
- GET `/api/v1/rbac/permissions`
- POST `/api/v1/rbac/permissions`
- POST `/api/v1/rbac/role-permissions`

## Règles importantes

- Les mots de passe ne sont jamais stockés en clair.
- Les routes protégées exigent un token JWT valide.
- Les permissions sont vérifiées par `require_permission`.
- Les rôles élevés `SUPER_ADMIN` et `ADMIN` ont un accès élargi sur le MVP.
- Les actions sensibles doivent être auditées progressivement.

## Commandes de test manuel

Créer le premier admin :

```bash
curl -X POST http://localhost:8000/api/v1/users/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.com","password":"admin123","first_name":"Admin","last_name":"GuineeCare","role":"SUPER_ADMIN"}'
```

Se connecter :

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.com","password":"admin123"}'
```

Appeler une route protégée :

```bash
curl http://localhost:8000/api/v1/patients \
  -H "Authorization: Bearer <token>"
```
