# Diagnostic connexion frontend local

## Correctifs appliqués

Le backend autorise maintenant les appels du frontend local via CORS pour :

- `http://localhost:5173`
- `http://127.0.0.1:5173`
- `http://localhost:3000`
- `http://127.0.0.1:3000`

Le backend peut aussi lancer le seed de démonstration au démarrage local si la variable `SEED_DEMO_DATA=true` est définie.

## Relancer proprement en local

Depuis la racine du projet :

```bash
git pull
```

Puis reconstruire les conteneurs :

```bash
docker compose down
docker compose up --build
```

Si la connexion échoue encore, supprimer le volume PostgreSQL local pour forcer la recréation du compte de démonstration :

```bash
docker compose down -v
docker compose up --build
```

## Vérifier le backend

Dans un autre terminal :

```bash
curl http://localhost:8000/health
```

Résultat attendu :

```json
{"status":"ok","service":"guineecare-backend"}
```

## Vérifier Swagger

Ouvrir :

```text
http://localhost:8000/docs
```

Tester `POST /api/v1/auth/login` avec le compte local indiqué sur la page frontend.

## Vérifier le frontend

Ouvrir :

```text
http://localhost:5173
```

Utiliser le compte affiché sur la page de connexion.

## Causes fréquentes

### Ancien volume PostgreSQL

Si le volume PostgreSQL existe déjà, le seed peut ne pas recréer les données comme attendu. Solution :

```bash
docker compose down -v
docker compose up --build
```

### Ancien build frontend

Si le frontend a été lancé avant les corrections :

```bash
docker compose build frontend --no-cache
docker compose up frontend
```

### Backend pas encore prêt

Attendre que le backend affiche un statut sain, puis recharger la page frontend.

### Mauvaise URL API

Le frontend doit appeler :

```text
http://localhost:8000/api/v1
```

Cette valeur est configurée dans `docker-compose.yml` avec `VITE_API_BASE_URL`.
