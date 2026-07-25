# Guide de déploiement rapide — GuinéeCare sur VPS

> Déploiement en production sur un VPS (DigitalOcean, Hetzner, OVH)
> Temps estimé : 30 minutes

## Prérequis

- VPS avec Ubuntu 22.04+ (minimum 2 vCPU, 4 GB RAM, 40 GB SSD)
- Accès root via SSH
- Nom de domaine pointant vers l'IP du VPS (ex: `demo.guineecare.gn`)

## Étape 1 — Préparer le serveur

```bash
# Connexion SSH
ssh root@VOTRE_IP_VPS

# Mise à jour
apt update && apt upgrade -y

# Installer Docker + Docker Compose
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin git certbot python3-certbot-nginx

# Créer un utilisateur non-root
adduser guineecare
usermod -aG docker guineecare
su - guineecare
```

## Étape 2 — Cloner le dépôt

```bash
cd /home/guineecare
git clone https://github.com/skaba89/guineecare-hospital-suite.git
cd guineecare-hospital-suite
```

## Étape 3 — Configurer les secrets

```bash
# Copier le template
cp .env.production.template .env.production

# Générer les secrets
python3 -c "import secrets; print('AUTH_SECRET=' + secrets.token_urlsafe(48))"
python3 -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(24))"
python3 -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(24))"

# Éditer .env.production avec les valeurs générées
nano .env.production
```

Remplacer :
- `AUTH_SECRET` → la clé générée
- `DB_PASSWORD` → le mot de passe PostgreSQL
- `REDIS_PASSWORD` → le mot de passe Redis
- `PUBLIC_URL` → `https://VOTRE_DOMAINE`
- `CORS_ORIGINS` → `["https://VOTRE_DOMAINE"]`

## Étape 4 — Configurer HTTPS

```bash
# Obtenir un certificat Let's Encrypt
sudo certbot certonly --standalone -d VOTRE_DOMAINE

# Copier les certificats dans le dossier tls
sudo mkdir -p tls
sudo cp /etc/letsencrypt/live/VOTRE_DOMAINE/fullchain.pem tls/
sudo cp /etc/letsencrypt/live/VOTRE_DOMAINE/privkey.pem tls/
sudo chown -R guineecare:guineecare tls
```

## Étape 5 — Démarrer les services

```bash
# Build et démarrage
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build

# Vérifier que tout tourne
docker compose ps
docker compose logs backend --tail 20

# Appliquer les migrations Alembic
docker compose exec backend alembic upgrade head

# Créer le super-admin
docker compose exec backend python -m app.cli create-superuser admin@guineecare.gn

# (Optionnel) Seeder des données de démo
# ATTENTION : en production, ne pas utiliser SEED_DEMO_DATA=true
# Pour la démo ministre uniquement :
docker compose exec -e SEED_DEMO_DATA=true backend python -c "from app.db.seed import run_seed; run_seed()"
```

## Étape 6 — Vérifier

```bash
# Test API
curl https://VOTRE_DOMAINE/api/v1
# Doit retourner : {"name":"GuineeCare Hospital Suite","version":"1.7.1",...}

# Test login
curl -X POST https://VOTRE_DOMAINE/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@guineecare.gn","password":"VOTRE_MOT_DE_PASSE"}'

# Ouvrir dans le navigateur
# https://VOTRE_DOMAINE → frontend
# https://VOTRE_DOMAINE/api/v1/docs → Swagger UI
```

## Étape 7 — Sauvegarde automatique

Le service `db-backup` dans `docker-compose.prod.yml` effectue déjà un
backup quotidien à 02:00 UTC avec rétention 14 jours.

Pour un backup manuel :
```bash
docker compose exec db-backup bash -c 'pg_dump -Fc > /backups/manual_$(date +%Y%m%d_%H%M%S).dump'
```

Pour restaurer :
```bash
docker compose exec postgres pg_restore -d guineecare -c /backups/guineecare_YYYYMMDD_HHMMSS.dump
```

## Commandes utiles

```bash
# Voir les logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f nginx

# Redémarrer un service
docker compose restart backend

# Mettre à jour le code
git pull origin main
docker compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --build

# Arrêter tout
docker compose down

# Voir l'utilisation des ressources
docker stats
```

## En cas de problème

### Backend ne démarre pas
```bash
docker compose logs backend --tail 50
# Vérifier : AUTH_SECRET non vide, DB_PASSWORD correct, PostgreSQL démarré
```

### Frontend ne charge pas
```bash
docker compose logs frontend --tail 50
# Vérifier : nginx.conf correct, certificats TLS présents
```

### Erreur 502 Bad Gateway
```bash
# Le backend n'est pas prêt — attendre 30s ou vérifier les logs
docker compose logs backend --tail 20
```

### Base de données inaccessible
```bash
docker compose logs postgres --tail 20
docker compose exec postgres psql -U guineecare -d guineecare -c "SELECT 1;"
```
