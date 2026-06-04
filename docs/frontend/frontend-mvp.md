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
5. affiche les listes retournées par l'API ;
6. propose des formulaires MVP de création ;
7. recharge automatiquement la liste après création.

## Formulaires MVP disponibles

### Patients

Permet de créer un patient avec :

- établissement ID ;
- numéro patient ;
- prénom ;
- nom.

Endpoint appelé : `POST /api/v1/patients`.

### Admissions

Permet de créer une admission avec :

- établissement ID ;
- patient ID ;
- service ID ;
- type admission.

Endpoint appelé : `POST /api/v1/admissions`.

### Urgences

Permet de créer un passage urgence avec :

- établissement ID ;
- patient ID ;
- admission ID optionnel ;
- priorité ;
- motif.

Endpoint appelé : `POST /api/v1/emergency/visits`.

### Pharmacie

Permet de créer un produit pharmacie avec :

- établissement ID ;
- code produit ;
- nom produit ;
- catégorie ;
- forme ;
- dosage.

Endpoint appelé : `POST /api/v1/pharmacy/products`.

### Laboratoire

Permet de créer un examen laboratoire avec :

- établissement ID ;
- code examen ;
- nom examen ;
- catégorie ;
- type échantillon.

Endpoint appelé : `POST /api/v1/laboratory/tests`.

### Facturation

Permet de créer une facture avec :

- établissement ID ;
- patient ID ;
- admission ID optionnel ;
- numéro facture ;
- description ;
- montant.

Endpoint appelé : `POST /api/v1/billing/invoices`.

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
- pas encore de listes de sélection dynamiques pour les IDs ;
- pas encore de paiement depuis l'écran facture ;
- pas encore de tri, filtre ou pagination frontend ;
- pas encore de refresh token côté frontend.

## Prochaine étape

Ajouter :

- des listes déroulantes alimentées par l'API ;
- la création de paiement sur une facture ;
- le tri et la recherche dans les tableaux ;
- un router React ;
- des composants UI réutilisables ;
- une expérience utilisateur plus proche d'un SIH professionnel.
