# Déploiement Render + Neon — Guide pas-à-pas (15 min)

> **Coût : 0 FCFA** · **Permanent** · **1 seule URL**
> Backend + frontend sur Render, base de données sur Neon serverless

## Architecture

```
Utilisateur (navigateur)
    │
    ▼
Render (backend FastAPI + frontend statique)     ← gratuit, 1 URL
    │
    ▼  (SQL)
Neon (PostgreSQL serverless)                     ← gratuit, permanent
```

## Pourquoi Neon plutôt que Render DB ?

| Critère | Render PostgreSQL | Neon PostgreSQL |
|---------|-------------------|-----------------|
| Durée | **90 jours** puis supprimé | **Permanent** |
| Stockage | 1 GB | 0.5 GB (suffisant ~50 000 patients) |
| Scale-to-zero | Non | Oui (économie de ressources) |
| Connection pooling | Non | Oui (pgBouncer intégré) |
| Branching (DB de test) | Non | Oui (1 clic) |

---

## Étape 1 — Créer la base Neon (3 min)

1. Allez sur https://neon.tech
2. **Sign in with GitHub**
3. **New Project** → nom : `guineecare`
4. Region : **AWS Frankfurt** (eu-central-1) — le plus proche de la Guinée
5. PostgreSQL version : 16
6. Click **Create project**

### Récupérer l'URL de connexion

Sur le dashboard Neon → **Connection Details** :

```
postgresql://guineecare:AbCdEfGhIjKlMnOp@ep-xxx.eu-central-1.aws.neon.tech/guineecare?sslmode=require
```

**Copiez cette URL** — vous en aurez besoin pour Render.

⚠️ Utilisez l'URL **avec pooling** (onglet "Pooled connection") pour de meilleures performances.

---

## Étape 2 — Déployer sur Render (10 min)

### 2.1 Créer le service

1. Allez sur https://render.com
2. **Sign in with GitHub**
3. Dashboard → **New +** → **Blueprint**
4. Sélectionnez votre repo : `skaba89/guineecare-hospital-suite`
5. Render lit `render.yaml` automatiquement → propose le service `guineecare`

### 2.2 Configurer les variables d'environnement

Avant de cliquer "Apply", configurez les variables :

| Variable | Valeur | Commentaire |
|----------|--------|-------------|
| `AUTH_SECRET` | *(générer ci-dessous)* | Clé secrète JWT |
| `DATABASE_URL` | *(URL Neon de l'étape 1)* | Connexion PostgreSQL |
| `CORS_ORIGINS` | `["*"]` | Déjà pré-rempli |
| `SEED_DEMO_DATA` | `true` | Charge les données de démo |
| `ENVIRONMENT` | `production` | Déjà pré-rempli |

**Générer AUTH_SECRET** (sur votre terminal Git Bash) :
```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2.3 Déployer

1. Cliquez **Apply**
2. Render démarre le build (~5 min) :
   - `pip install -r requirements.txt` (dépendances Python)
   - `cd ../frontend && npm ci && npm run build` (build frontend)
   - `cp -r dist ../backend/static` (copie frontend dans backend)
3. Puis le démarrage :
   - `alembic upgrade head` (migrations DB)
   - Seed des données de démo (50 patients, 20 établissements...)
   - `uvicorn app.main:app` (serveur web)
4. Suivez les logs : Render → `guineecare` → **Logs**

### 2.4 Vérifier le seed

Dans les logs, vous devez voir :
```
✅ Sections 1-1 committed
✅ Sections 1-2 committed
...
Seed data loaded successfully
Application startup complete.
```

Si vous voyez des ❌, copiez l'erreur et envoyez-la moi.

---

## Étape 3 — Tester (2 min)

### Votre URL
Render vous donne une URL comme :
```
https://guineecare.onrender.com
```

### Tests

```bash
# 1. Test API
curl https://guineecare.onrender.com/api/v1
# → {"name":"GuineeCare Hospital Suite","version":"1.7.1",...}

# 2. Test login
curl -X POST https://guineecare.onrender.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.com","password":"admin123"}'
# → {"access_token":"eyJ...","user":{...}}

# 3. Test santé DB
curl https://guineecare.onrender.com/health
# → {"status":"healthy",...}
```

### Dans le navigateur

1. Ouvrez `https://guineecare.onrender.com`
2. Login : `admin@guineecare.com` / `admin123`
3. Vérifiez :
   - [ ] Dashboard avec KPIs
   - [ ] Liste des patients (50 patients de démo)
   - [ ] Création d'un nouveau patient
   - [ ] Toggle FR/EN
   - [ ] Page Qualité avec indicateurs OMS/HAS

---

## Limites du gratuit

| Service | Limite | Impact | Solution |
|---------|--------|--------|----------|
| Render free | S'endort après 15 min | 1er appel = 30s | Plan Starter $7/mois |
| Render free | 750h/mois | Suffisant pour 1 service | — |
| Neon free | 0.5 GB | ~50 000 patients | Plan Launch $19/mois |
| Neon free | 100 compute heures/mois | Suffisant pour démo | — |

### Astuce démo ministre
2 minutes avant la présentation, ouvrez l'URL dans un onglet pour
"réveiller" le service. Ensuite, l'application répond instantanément.

---

## Gérer la base Neon

### Voir les données
1. Dashboard Neon → `guineecare` → **Tables**
2. Vous voyez toutes les tables (patients, admissions, invoices, etc.)

### Backup manuel
```bash
pg_dump "VOTRE_URL_NEON" -Fc > backup.dump
```

### Restaurer
```bash
pg_restore -d "VOTRE_URL_NEON" backup.dump
```

### Reset complet (re-seed)
1. Dashboard Neon → SQL Editor
2. Exécutez : `DROP SCHEMA public CASCADE; CREATE SCHEMA public;`
3. Sur Render → Manual Deploy → Clear cache & deploy
4. Le seed se relance automatiquement

---

## Mise à jour du code

Quand vous poussez sur `main` sur GitHub :
- Render redéploie automatiquement (~5 min)
- Neon reste inchangé (données préservées)

Pour forcer un redéploiement sans changer le code :
- Render → Dashboard → **Manual Deploy** → **Clear cache & deploy**

---

## Migration vers VPS (quand prêt)

```bash
# 1. Export Neon
pg_dump "VOTRE_URL_NEON" -Fc > neon_backup.dump

# 2. Import sur VPS
pg_restore -d guineecare neon_backup.dump

# 3. Suivre docs/deploiement/guide-vps-rapide.md
```

---

## Dépannage

### "Could not connect to database"
→ Vérifiez que `DATABASE_URL` sur Render correspond exactement à l'URL Neon
→ L'URL doit contenir `?sslmode=require` à la fin
→ Utilisez l'URL "Pooled connection" (pas "Direct connection")

### Build échoue sur `npm ci`
→ Render build en Python — Node.js n'est peut-être pas disponible
→ Solution : ajouter `apt-get install -y nodejs npm` dans le buildCommand
→ Ou utiliser le runtime Docker sur Render au lieu de Python

### "ModuleNotFoundError: No module named 'app'"
→ Le `rootDir` doit être `backend` dans render.yaml (déjà configuré)

### Le seed échoue avec "no such column"
→ Les migrations Alembic ne sont pas appliquées
→ Vérifiez que `alembic upgrade head` est dans le startCommand (déjà configuré)

### Page blanche sur le frontend
→ Le dossier `backend/static/` n'a pas été créé pendant le build
→ Vérifiez les logs Render pour l'étape `cp -r dist ../backend/static`
