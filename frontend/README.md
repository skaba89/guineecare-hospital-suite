# Frontend — GuinéeCare Hospital Suite

## Objectif

Interface web MVP pour la plateforme hospitalière GuinéeCare.

## Stack

- React
- TypeScript
- Vite
- CSS simple et responsive
- API REST backend FastAPI

## Pages MVP

- Connexion
- Dashboard hôpital
- Patients
- Admissions
- Urgences
- Pharmacie
- Laboratoire
- Facturation

## Lancement local

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Application :

- http://localhost:5173

Backend attendu :

- http://localhost:8000/api/v1

## Avec Docker Compose

Depuis la racine :

```bash
docker compose up --build
```

Services :

- Frontend : http://localhost:5173
- Backend : http://localhost:8000
- Swagger : http://localhost:8000/docs

## Connexion

Utiliser le compte démo créé par le seed backend :

```text
Email: admin@guineecare.local
Password: admin123
```

## État actuel

Le frontend MVP permet :

- de se connecter ;
- de conserver le token dans le navigateur ;
- de naviguer entre les modules ;
- de lire les données backend sur les principales pages ;
- de visualiser les ressources dans des tableaux simples.

## Prochaines améliorations

- Formulaires de création patient et admission.
- Formulaire triage urgence.
- Formulaire mouvement de stock.
- Formulaire résultat laboratoire.
- Formulaire paiement facture.
- Gestion fine des erreurs API.
- Composants UI réutilisables.
