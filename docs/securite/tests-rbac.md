# Tests RBAC MVP

## Objectif

Valider que les accès aux routes sensibles sont contrôlés par rôle et permissions.

## Étape 1 — Créer le premier super administrateur

Créer le premier utilisateur via :

```http
POST /api/v1/users
```

Le premier utilisateur devient automatiquement `SUPER_ADMIN`.

## Étape 2 — Se connecter

```http
POST /api/v1/auth/login
```

Récupérer le token et l'utiliser dans Swagger avec :

```text
Authorization: Bearer TOKEN
```

## Étape 3 — Vérifier le profil connecté

```http
GET /api/v1/auth/me
```

## Étape 4 — Consulter les rôles et permissions

```http
GET /api/v1/rbac/roles
GET /api/v1/rbac/permissions
```

Ces routes doivent être accessibles à `SUPER_ADMIN` ou `ADMIN`.

## Étape 5 — Tester patients

Sans token :

```http
GET /api/v1/patients
```

Résultat attendu : erreur 401.

Avec un token sans permission : erreur 403.

Avec un rôle autorisé ou la permission `patient.read` : succès.

## Étape 6 — Tester admissions

Routes protégées :

- `GET /api/v1/admissions` exige `admission.read`.
- `POST /api/v1/admissions` exige `admission.create`.
- `POST /api/v1/admissions/{id}/close` exige `admission.close`.

## Permissions initiales

- `patient.read`
- `patient.create`
- `admission.read`
- `admission.create`
- `admission.close`
- `facility.read`
- `facility.manage`
- `department.read`
- `department.manage`
- `pharmacy.read`
- `lab.read`
- `billing.read`

## Prochaine étape

- Protéger facilities et departments.
- Ajouter audit des refus d'accès.
- Ajouter permissions par établissement.
- Ajouter tests automatisés Pytest.
