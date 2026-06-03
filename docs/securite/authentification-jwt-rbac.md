# Authentification JWT et RBAC

## Objectif

Mettre en place une première sécurité applicative pour le MVP : utilisateurs, login, token et rôles.

## Endpoints disponibles

### Créer un utilisateur

```http
POST /api/v1/users
```

Exemple de payload :

```json
{
  "email": "admin@guineecare.local",
  "password": "ChangerCeMotDePasse",
  "first_name": "Admin",
  "last_name": "GuineeCare",
  "facility_id": "ID_ETABLISSEMENT",
  "role": "ADMIN"
}
```

### Se connecter

```http
POST /api/v1/auth/login
```

Exemple de payload :

```json
{
  "email": "admin@guineecare.local",
  "password": "ChangerCeMotDePasse"
}
```

Réponse attendue :

```json
{
  "access_token": "TOKEN",
  "token_type": "bearer",
  "user": {
    "id": "...",
    "email": "admin@guineecare.local",
    "role": "ADMIN",
    "facility_id": "..."
  }
}
```

## Règles de sécurité

- Ne jamais utiliser un mot de passe de démo en production.
- Définir `AUTH_SECRET` dans l'environnement.
- Changer le secret par environnement.
- Activer progressivement les permissions fines.
- Auditer les actions sensibles.

## RBAC cible

Rôles initiaux :

- SUPER_ADMIN
- ADMIN
- DIRECTOR
- DOCTOR
- NURSE
- MIDWIFE
- PHARMACIST
- LAB_TECH
- CASHIER
- STATISTICIAN

## Prochaine étape

Ajouter une dépendance `get_current_user`, protéger les routes sensibles, puis appliquer les permissions par module.
