# Frontend MVP — GuinéeCare Hospital Suite

## Objectif

Fournir une première interface web fonctionnelle pour tester les principaux modules du backend MVP.

## Stack

- React
- TypeScript
- Vite
- CSS simple sans dépendance UI externe
- Fetch API native

## Pages MVP disponibles

- Login
- Dashboard
- Patients
- Admissions
- Urgences
- Pharmacie
- Laboratoire
- Facturation

## Connexion

Compte de démonstration après seed backend :

```text
Email: admin@guineecare.local
Password: admin123
```

## Lancement local

Depuis la racine :

```bash
docker compose up --build
```

Puis ouvrir :

```text
http://localhost:5173
```

Backend Swagger :

```text
http://localhost:8000/docs
```

## Lancement frontend seul

```bash
cd frontend
npm install
npm run dev
```

Configurer l'API :

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Fonctionnement

Le frontend :

1. affiche une page de connexion ;
2. appelle `/api/v1/auth/login` ;
3. stocke le token JWT dans le stockage local du navigateur ;
4. appelle les endpoints protégés avec `Authorization: Bearer <token>` ;
5. charge les listes de référence depuis l'API ;
6. affiche les listes retournées par l'API ;
7. propose des formulaires MVP de création ;
8. recharge automatiquement les données après création.

## Données chargées pour les listes déroulantes

L'interface charge automatiquement :

- établissements depuis `/api/v1/facilities` ;
- patients depuis `/api/v1/patients` ;
- services depuis `/api/v1/departments` ;
- admissions depuis `/api/v1/admissions` ;
- produits depuis `/api/v1/pharmacy/products` ;
- examens laboratoire depuis `/api/v1/laboratory/tests` ;
- demandes laboratoire depuis `/api/v1/laboratory/orders` ;
- factures depuis `/api/v1/billing/invoices`.

## Formulaires MVP disponibles

### Patients

Permet de créer un patient avec :

- établissement sélectionné dans la liste ;
- numéro patient ;
- prénom ;
- nom.

Endpoint appelé : `POST /api/v1/patients`.

### Admissions

Permet de créer une admission avec :

- établissement sélectionné ;
- patient sélectionné ;
- service sélectionné ;
- type admission.

Endpoint appelé : `POST /api/v1/admissions`.

### Urgences

Permet de créer un passage urgence avec :

- établissement sélectionné ;
- patient sélectionné ;
- admission optionnelle ;
- priorité ;
- motif.

Endpoint appelé : `POST /api/v1/emergency/visits`.

### Pharmacie

Permet de :

- créer un produit pharmacie via `POST /api/v1/pharmacy/products` ;
- créer un mouvement de stock via `POST /api/v1/pharmacy/stock/movements`.

Le mouvement de stock utilise une liste de produits alimentée par l'API.

### Laboratoire

Permet de :

- créer un examen laboratoire via `POST /api/v1/laboratory/tests` ;
- créer une demande laboratoire via `POST /api/v1/laboratory/orders` ;
- saisir un résultat via `POST /api/v1/laboratory/orders/{order_id}/results`.

Les patients, admissions, examens et demandes sont sélectionnés dans des listes alimentées par l'API.

### Facturation

Permet de :

- créer une facture via `POST /api/v1/billing/invoices` ;
- enregistrer un paiement via `POST /api/v1/billing/invoices/{invoice_id}/payments`.

Les patients, admissions et factures sont sélectionnés dans des listes alimentées par l'API.

## Fichiers principaux

- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/src/services/api.ts`
- `frontend/src/services/authService.ts`

## Limites actuelles

Cette version reste volontairement simple :

- pas encore de router React ;
- pas encore de composants UI professionnels ;
- pas encore de validation avancée côté formulaire ;
- pas encore de tri, filtre ou pagination frontend ;
- pas encore de refresh token côté frontend ;
- pas encore de séparation complète des composants par module.

## Prochaine étape

Ajouter :

- le tri et la recherche dans les tableaux ;
- un router React ;
- des composants UI réutilisables ;
- une séparation des pages par fichier ;
- des formulaires plus proches du terrain hospitalier ;
- une expérience utilisateur plus proche d'un SIH professionnel.
