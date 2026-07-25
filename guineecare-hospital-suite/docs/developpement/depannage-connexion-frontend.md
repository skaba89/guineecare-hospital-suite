# Dépannage connexion frontend local

## Problème

Le frontend affiche la page de connexion mais l'utilisateur n'arrive pas à se connecter avec :

```text
admin@guineecare.com / admin123
```

## Corrections appliquées

Les corrections suivantes sont intégrées au projet :

1. CORS activé côté backend pour :
   - `http://localhost:5173`
   - `http://127.0.0.1:5173`
   - `http://localhost:3000`
   - `http://127.0.0.1:3000`
2. Le backend lance automatiquement le seed au démarrage Docker.
3. Le compte admin local est créé automatiquement.
4. PostgreSQL a un healthcheck.
5. Le backend a un healthcheck.
6. Le frontend attend que le backend soit prêt.
7. Le frontend vérifie l'ancien token au démarrage et le supprime s'il est invalide.
8. Le mot de passe local est prérempli sur la page de connexion.

## Commandes recommandées

Depuis la racine du projet :

```bash
git pull
```

Puis reconstruire proprement :

```bash
docker compose down
docker compose up --build
```

Si tu veux repartir de zéro avec une base propre :

```bash
docker compose down -v
docker compose up --build
```

Attention : `docker compose down -v` supprime le volume PostgreSQL local.

## URLs à vérifier

Frontend :

```text
http://localhost:5173
```

Backend healthcheck :

```text
http://localhost:8000/health
```

Swagger :

```text
http://localhost:8000/docs
```

## Identifiants locaux

```text
Email: admin@guineecare.com
Password: admin123
```

## Test API direct

Tester le backend sans passer par le frontend :

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.com","password":"admin123"}'
```

Résultat attendu :

```json
{
  "access_token": "...",
  "token_type": "bearer",
  "user": {
    "email": "admin@guineecare.com",
    "role": "SUPER_ADMIN"
  }
}
```

## Si le frontend bloque encore

### 1. Supprimer l'ancien token navigateur

Dans le navigateur :

- ouvrir les DevTools ;
- aller dans Application / Local Storage ;
- supprimer `guineecare_token` ;
- recharger la page.

Ou dans la console navigateur :

```javascript
localStorage.removeItem("guineecare_token")
location.reload()
```

### 2. Vérifier les logs backend

```bash
docker compose logs -f backend
```

Tu dois voir :

```text
Seed completed successfully
Demo admin: admin@guineecare.com / admin123
```

### 3. Vérifier les logs frontend

```bash
docker compose logs -f frontend
```

### 4. Vérifier les conteneurs

```bash
docker compose ps
```

Les services attendus :

- `guineecare-postgres` healthy ;
- `guineecare-backend` healthy ;
- `guineecare-frontend` up.

## Causes fréquentes

### CORS

Avant correction, le backend ne déclarait pas explicitement l'origine `localhost:5173`.
Le navigateur pouvait donc bloquer l'appel `/auth/login`.

### Seed non lancé

Avant correction, le compte admin existait seulement après lancement manuel :

```bash
python -m app.db.seed
```

Maintenant Docker lance automatiquement ce seed avant l'API.

### Ancien token invalide

Si un ancien token était stocké dans le navigateur, le frontend pouvait croire que l'utilisateur était connecté.
Maintenant il vérifie `/auth/me` au démarrage et supprime le token invalide.
