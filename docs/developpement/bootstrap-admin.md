# Bootstrap du premier administrateur

## Objectif

Créer le premier compte `SUPER_ADMIN` sans stocker de mot de passe de démonstration dans le dépôt.

## Étapes

1. Lancer l'application.
2. Ouvrir Swagger : `http://localhost:8000/docs`.
3. Créer le premier utilisateur via `POST /api/v1/users/bootstrap`.
4. Se connecter via `POST /api/v1/auth/login`.
5. Créer ensuite les établissements, services et autres utilisateurs avec le token administrateur.

## Important

`POST /api/v1/users/bootstrap` fonctionne uniquement si aucun utilisateur n'existe encore.

Dès que le premier utilisateur existe, cette route retourne une erreur `403`.

## Exemple de création du premier super administrateur

```json
{
  "email": "admin@guineecare.com",
  "password": "A_REMPLACER_PAR_UN_SECRET_LOCAL",
  "first_name": "Admin",
  "last_name": "GuineeCare",
  "facility_id": null,
  "role": "ADMIN"
}
```

Même si `role` vaut `ADMIN` dans le payload, le backend force automatiquement le premier compte en `SUPER_ADMIN`.

## Connexion

Endpoint :

```http
POST /api/v1/auth/login
```

Payload :

```json
{
  "email": "admin@guineecare.com",
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

## Créer ensuite un utilisateur standard

Endpoint protégé :

```http
POST /api/v1/users
```

Cette route exige un token `SUPER_ADMIN` ou `ADMIN`.

## Recommandations production

- Ne jamais utiliser un mot de passe faible.
- Changer `AUTH_SECRET`.
- Supprimer ou désactiver le bootstrap après initialisation production si nécessaire.
- Créer les utilisateurs uniquement depuis un compte administrateur.
- Auditer la création des comptes dans une étape suivante.
