# Bootstrap du premier administrateur

## Objectif

Créer le premier compte administrateur sans stocker de mot de passe de démonstration dans le dépôt.

## Étapes

1. Lancer l'application.
2. Ouvrir Swagger : `http://localhost:8000/docs`.
3. Créer le premier établissement via `POST /api/v1/facilities`.
4. Créer le premier utilisateur via `POST /api/v1/users`.

## Important

Si aucun utilisateur n'existe encore, le premier utilisateur créé reçoit automatiquement le rôle `SUPER_ADMIN`.

## Exemple de création utilisateur

```json
{
  "email": "admin@guineecare.local",
  "password": "A_REMPLACER_PAR_UN_SECRET_LOCAL",
  "first_name": "Admin",
  "last_name": "GuineeCare",
  "facility_id": "ID_ETABLISSEMENT",
  "role": "ADMIN"
}
```

## Connexion

Endpoint :

```http
POST /api/v1/auth/login
```

Payload :

```json
{
  "email": "admin@guineecare.local",
  "password": "LE_MOT_DE_PASSE_CHOISI"
}
```

## Vérifier le token

Endpoint :

```http
GET /api/v1/auth/me
```

Ajouter l'en-tête :

```text
Authorization: Bearer TOKEN
```

## Recommandations production

- Ne jamais utiliser un mot de passe faible.
- Changer `AUTH_SECRET`.
- Désactiver le bootstrap public après initialisation.
- Activer la création utilisateur uniquement depuis un compte administrateur.
