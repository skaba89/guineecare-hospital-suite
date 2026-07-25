# Guide VPS Production — Hetzner (5€/mois)

> Migration Render free → VPS dédié (pas de sommeil, pas de rate limit)

## Pourquoi migrer ?

| Render free | VPS Hetzner |
|---|---|
| S'endort après 15 min | Toujours actif |
| Rate limit (429) | Pas de limite |
| 512 MB RAM | 4 GB RAM |
| Pas de Redis | Redis inclus |
| Pas de Grafana | Monitoring complet |

## Étape 1 — Louer le VPS

1. Allez sur https://www.hetzner.com/cloud
2. Créez un serveur **CX22** :
   - CPU : 2 vCPU AMD
   - RAM : 4 GB
   - Disk : 40 GB SSD
   - OS : Ubuntu 22.04
   - Prix : ~5€/mois
3. Notez l'IP du serveur

## Étape 2 — Préparer le serveur

```bash
ssh root@VOTRE_IP

# Mise à jour
apt update && apt upgrade -y

# Docker
curl -fsSL https://get.docker.com | sh

# Git
apt install -y git certbot python3-certbot-nginx

# Utilisateur non-root
adduser guineecare
usermod -aG docker guineecare
```

## Étape 3 — Déployer

```bash
su - guineecare
git clone https://github.com/skaba89/guineecare-hospital-suite.git
cd guineecare-hospital-suite

# Configurer les secrets
cp .env.production.template .env.production
nano .env.production
# Remplir : AUTH_SECRET, DB_PASSWORD, REDIS_PASSWORD, CORS_ORIGINS

# HTTPS
sudo certbot certonly --standalone -d guineecare.gn
sudo cp /etc/letsencrypt/live/guineecare.gn/*.pem tls/

# Démarrer
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
  --env-file .env.production up -d --build

# Migrations
docker compose exec backend alembic upgrade head

# Super-admin
docker compose exec backend python -m app.cli create-superuser admin@guineecare.gn

# Seed démo (optionnel)
docker compose exec -e SEED_DEMO_DATA=true backend python -c \
  "from app.db.seed import run_seed; run_seed()"
```

## Étape 4 — Redis (déjà inclus)

Le `docker-compose.prod.yml` inclut Redis. Pour vérifier :
```bash
docker compose exec redis redis-cli ping
# Doit retourner : PONG
```

## Étape 5 — Monitoring avec Grafana

```bash
# Installer Grafana
apt install -y grafana
systemctl enable grafana-server
systemctl start grafana-server

# Accès : http://VOTRE_IP:3000 (admin/admin)

# Configurer Prometheus comme datasource :
# URL : http://backend:8000/metrics
# (ajouter le token METRICS_TOKEN si configuré)
```

## Étape 6 — Backup automatique

```bash
# Créer un cron job
crontab -e
# Ajouter :
0 2 * * * /home/guineecare/guineecare-hospital-suite/scripts/backup.sh >> /var/log/guineecare-backup.log 2>&1

# Tester le backup manuellement
docker compose exec db-backup bash -c 'pg_dump -Fc > /backups/manual_$(date +%Y%m%d).dump'
```

## Étape 7 — Migration des données Neon → VPS

```bash
# Export depuis Neon
pg_dump "VOTRE_URL_NEON" -Fc > neon_backup.dump

# Import sur VPS
docker compose exec -T postgres pg_restore -d guineecare -c < neon_backup.dump
```

## Étape 8 — DNS

Pointez votre nom de domaine vers l'IP du VPS :
```
guineecare.gn  A  VOTRE_IP_VPS
```

## Coûts totaux

| Service | Coût/mois |
|---|---|
| VPS Hetzner CX22 | 5 € |
| Nom de domaine .gn | ~50 000 GNF/an |
| **Total** | **~5 €/mois** |

## Comparaison Render free vs VPS

| Critère | Render free | VPS Hetzner |
|---|---|---|
| Disponibilité | ~95% (sommeil) | 99.9%+ |
| Temps de réponse | 30s au réveil | <100ms |
| Rate limit | Oui (429) | Non |
| Redis | Non | Oui |
| Grafana | Non | Oui |
| Backup | Non | Oui (cron) |
| Prix | 0 € | 5 € |
