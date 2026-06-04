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
5. affiche les listes retournées par l'API.

## Fichiers principaux

- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles.css`
- `frontend/src/services/api.ts`
- `frontend/src/services/authService.ts`

## Limites actuelles

Cette version est volontairement simple :

- pas encore de formulaires avancés par module ;
- pas encore de router React ;
- pas encore de composants UI professionnels ;
- pas encore de gestion fine des erreurs métier ;
- pas encore de refresh token côté frontend.

## Prochaine étape

Ajouter des formulaires de création pour :

- patient ;
- admission ;
- passage urgence ;
- produit pharmacie ;
- demande laboratoire ;
- facture et paiement.
