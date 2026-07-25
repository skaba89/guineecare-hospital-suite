# Tests d'intégration backend — MVP

## Objectif

Valider que les modules backend MVP fonctionnent avec une vraie base PostgreSQL et les permissions RBAC.

## Préparation

1. Démarrer PostgreSQL :

```bash
docker compose up -d postgres
```

2. Appliquer les migrations :

```bash
cd backend
alembic upgrade head
```

3. Initialiser les données de démonstration :

```bash
python -m app.db.seed
```

4. Lancer le backend :

```bash
uvicorn app.main:app --reload
```

## Parcours de test 1 — Authentification

- POST `/api/v1/auth/login`
- Vérifier le token JWT.
- GET `/api/v1/auth/me` avec le token.
- Vérifier que l'utilisateur connecté est `SUPER_ADMIN`.

## Parcours de test 2 — Référentiels

- GET `/api/v1/facilities`
- POST `/api/v1/facilities`
- GET `/api/v1/departments`
- POST `/api/v1/departments`

Résultat attendu : les données sont persistées en base.

## Parcours de test 3 — Patient et admission

- POST `/api/v1/patients`
- GET `/api/v1/patients`
- POST `/api/v1/admissions`
- GET `/api/v1/admissions`
- POST `/api/v1/admissions/{id}/close`

Résultat attendu : le patient est créé, l'admission est ouverte puis clôturée.

## Parcours de test 4 — Urgences

- POST `/api/v1/emergency/visits`
- GET `/api/v1/emergency/queue`
- POST `/api/v1/emergency/visits/{id}/triage`
- POST `/api/v1/emergency/visits/{id}/orientation`

Résultat attendu : le passage urgence est créé, trié puis clôturé avec orientation.

## Parcours de test 5 — Pharmacie

- POST `/api/v1/pharmacy/products`
- GET `/api/v1/pharmacy/products`
- POST `/api/v1/pharmacy/stock/movements` avec `IN`
- POST `/api/v1/pharmacy/stock/movements` avec `OUT`
- GET `/api/v1/pharmacy/stock`

Résultat attendu : le stock augmente puis diminue correctement.

## Parcours de test 6 — Laboratoire

- POST `/api/v1/laboratory/tests`
- POST `/api/v1/laboratory/orders`
- POST `/api/v1/laboratory/orders/{id}/results`
- POST `/api/v1/laboratory/results/{id}/validate`

Résultat attendu : le résultat passe de brouillon à validé.

## Parcours de test 7 — Facturation

- POST `/api/v1/billing/tariffs`
- POST `/api/v1/billing/invoices`
- POST `/api/v1/billing/invoices/{id}/payments`
- GET `/api/v1/billing/payments/{id}/receipt`

Résultat attendu : le paiement met à jour le solde de facture et génère un reçu JSON.

## Tests de sécurité

- Appeler une route protégée sans token.
- Appeler une route protégée avec un token invalide.
- Appeler une route avec un rôle sans permission.

Résultat attendu : accès refusé avec HTTP 401 ou 403.

## Critères d'acceptation

- Les migrations passent sans erreur.
- Le seed est idempotent.
- Les endpoints protégés refusent les accès non autorisés.
- Les données métier sont persistées.
- Les parcours MVP critiques sont exécutables de bout en bout.
