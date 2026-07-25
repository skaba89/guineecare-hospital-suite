# Runbook — Déploiement pilote CHU Donka (v1.0.0)

Ce document est la référence opérationnelle pour le déploiement, l'exploitation et la maintenance de GuinéeCare Hospital Suite au CHU Donka (Conakry, Guinée).

**Public cible** : équipe DevOps GuinéeCare, administrateur système CHU Donka, on-call.

**Version applicative** : v1.0.0
**Date de mise en production cible** : à définir avec la direction du CHU Donka.

---

## 1. Architecture cible

```
┌──────────────────────────────────────────────────────────────────┐
│  Internet (utilisateurs CHU Donka — médecins, infirmiers, etc.)  │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ HTTPS (443)
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│  nginx (reverse proxy + TLS terminator)                          │
│  - TLS 1.2/1.3 (Let's Encrypt)                                   │
│  - HSTS, CSP, X-Frame-Options: DENY                              │
│  - Rate limiting : 5 logins/min, 120 API req/min                 │
│  - /docs, /metrics : IP allowlist (admin office)                 │
└────────┬───────────────────────────────┬─────────────────────────┘
         │ /api/*                        │ /
         ▼                               ▼
┌──────────────────────┐         ┌──────────────────────┐
│  backend (FastAPI)   │         │  frontend (nginx +   │
│  - port 8000         │         │  React SPA)          │
│  - user 1001:1001    │         │  - port 80           │
│  - read_only fs      │         │  - static files only │
│  - 1 GB / 2 CPU      │         └──────────────────────┘
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐     ┌──────────────────────┐
│  PostgreSQL 16       │     │  Redis 7 (cache)     │
│  - user 70:70        │     │  - 64 MB maxmemory   │
│  - 1 GB / 1 CPU      │     │  - password-protected│
│  - daily backup 02h  │     └──────────────────────┘
└──────────────────────┘
```

### Spécifications minimales du serveur

| Ressource | Minimum | Recommandé |
|-----------|---------|------------|
| CPU | 2 cœurs | 4 cœurs |
| RAM | 4 GB | 8 GB |
| Disque | 40 GB SSD | 100 GB SSD |
| Bande passante | 10 Mbps | 50 Mbps |
| OS | Ubuntu 22.04 LTS / Debian 12 | Ubuntu 24.04 LTS |

---

## 2. Préparation du serveur (one-time)

### 2.1 Installation des dépendances

```bash
# Sur le serveur CHU Donka (Ubuntu 22.04+)
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git ufw fail2ban

# Démarrer Docker au boot
sudo systemctl enable --now docker

# Ajouter l'utilisateur ops au groupe docker
sudo usermod -aG docker $USER
newgrp docker
```

### 2.2 Pare-feu (UFW)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp        # SSH (limiter si possible à l'IP admin)
sudo ufw allow 80/tcp        # HTTP (redirect vers HTTPS)
sudo ufw allow 443/tcp       # HTTPS
sudo ufw enable
sudo ufw status verbose
```

### 2.3 Clonage du dépôt

```bash
cd /opt
sudo mkdir -p guineecare && sudo chown $USER:$USER guineecare
git clone https://github.com/skaba89/guineecare-hospital-suite.git guineecare
cd guineecare
git checkout v1.0.0   # tag de production
```

### 2.4 Configuration DNS

Faire pointer `chu-donka.guineecare.gn` vers l'IP publique du serveur. Vérifier :

```bash
dig +short chu-donka.guineecare.gn
```

### 2.5 Certificats TLS (Let's Encrypt)

```bash
sudo apt install -y certbot
sudo systemctl stop docker   # libère le port 80
sudo certbot certonly --standalone -d chu-donka.guineecare.gn \
    --email tech@guineecare.gn --agree-tos --no-eff-email

# Copier les certs vers le dossier tls/
sudo mkdir -p tls
sudo cp /etc/letsencrypt/live/chu-donka.guineecare.gn/fullchain.pem tls/
sudo cp /etc/letsencrypt/live/chu-donka.guineecare.gn/privkey.pem   tls/
sudo chown -R $USER:$USER tls/
sudo chmod 600 tls/privkey.pem

# Renouvellement auto (crontab)
echo "0 3 * * * certbot renew --quiet --post-hook 'cp /etc/letsencrypt/live/chu-donka.guineecare.gn/fullchain.pem /opt/guineecare/tls/ && cp /etc/letsencrypt/live/chu-donka.guineecare.gn/privkey.pem /opt/guineecare/tls/ && chown -R \$USER:\$USER /opt/guineecare/tls/ && cd /opt/guineecare && docker compose -f docker-compose.yml -f docker-compose.prod.yml exec nginx nginx -s reload'" | sudo tee /etc/cron.d/certbot-renew

sudo systemctl start docker
```

---

## 3. Configuration des secrets

### 3.1 Création du fichier `.env.production`

```bash
cp .env.production.template .env.production
chmod 600 .env.production

# Générer des secrets forts
openssl rand -hex 48  # → AUTH_SECRET
openssl rand -hex 32  # → DB_PASSWORD
openssl rand -hex 32  # → METRICS_TOKEN
openssl rand -hex 32  # → BOOTSTRAP_TOKEN
openssl rand -hex 32  # → REDIS_PASSWORD

# Éditer le fichier
nano .env.production
```

Vérifier que **toutes** les variables `CHANGE_ME_*` ont été remplacées.

### 3.2 Validation pré-déploiement

```bash
bash scripts/deploy.sh --check-only
```

Ce script vérifie :
- ✅ Présence du fichier `.env.production`
- ✅ Toutes les variables requises sont renseignées
- ✅ Aucune valeur placeholder `CHANGE_ME_*` restante
- ✅ `ENVIRONMENT=production`
- ✅ `SEED_DEMO_DATA=false`
- ✅ Présence des certificats TLS
- ✅ Docker + Compose installés
- ✅ Espace disque ≥ 5 GB

---

## 4. Déploiement initial

### 4.1 Lancement

```bash
bash scripts/deploy.sh
```

Le script :
1. Build les images Docker (backend + frontend).
2. Démarre PostgreSQL et attend qu'il soit healthy.
3. Applique les migrations Alembic.
4. Démarre backend + frontend + nginx + redis + db-backup.
5. Attend que le backend soit healthy.
6. Vérifie le `/health` en HTTPS.

Durée estimée : 5–10 minutes selon la bande passante.

### 4.2 Bootstrap du super-admin

Après le déploiement initial, créer le premier SUPER_ADMIN :

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production exec backend \
    python -m app.cli create-superuser \
        --email admin@chu-donka.gn \
        --password '<STRONG-PASSWORD>' \
        --first-name Admin --last-name Donka
```

> ⚠️  Le mot de passe doit respecter la politique v0.8 : ≥12 caractères, 1 majuscule, 1 minuscule, 1 chiffre, 1 caractère spécial.

Alternative via endpoint HTTP (si `BOOTSTRAP_TOKEN` est défini) :

```bash
curl -X POST https://chu-donka.guineecare.gn/api/v1/users/bootstrap \
    -H "X-Bootstrap-Token: $BOOTSTRAP_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "admin@chu-donka.gn",
        "password": "<STRONG-PASSWORD>",
        "first_name": "Admin",
        "last_name": "Donka"
    }'
```

### 4.3 Vérification post-déploiement

| Check | Commande | Résultat attendu |
|-------|----------|------------------|
| Health check | `curl https://chu-donka.guineecare.gn/health` | `{"status":"ok",...}` |
| Health ready | `curl https://chu-donka.guineecare.gn/health/ready` | `{"status":"ok","database":"ok",...}` ou `{"status":"degraded",...}` |
| Login | `POST /api/v1/auth/login` avec admin@chu-donka.gn | `access_token` + `refresh_token` |
| Swagger UI | `curl -k https://chu-donka.guineecare.gn/docs` (depuis IP allowlistée) | HTML Swagger |
| Frontend | navigateur → `https://chu-donka.guineecare.gn` | Page de login |
| TLS | `curl -vI https://chu-donka.guineecare.gn 2>&1 \| grep -E 'TLS\|SSL'` | TLSv1.3 |
| Headers | `curl -sI https://chu-donka.guineecare.gn \| grep -iE 'strict-transport\|content-security\|x-frame'` | Tous présents |

---

## 5. Opérations courantes

### 5.1 Status des conteneurs

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production ps
```

### 5.2 Logs

```bash
# Tous les services
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production logs --tail=100

# Backend uniquement (JSON structuré)
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production logs -f backend

# Erreurs uniquement
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production logs backend 2>&1 | jq 'select(.level=="ERROR")'
```

### 5.3 Redémarrage d'un service

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production restart backend
```

### 5.4 Mise à jour de l'application

```bash
cd /opt/guineecare
git fetch --tags
git checkout v1.0.1   # nouvelle version

bash scripts/deploy.sh
# Le script applique automatiquement les migrations et redémarre les services
```

### 5.5 Sauvegarde manuelle

```bash
bash scripts/backup.sh          # crée un backup immédiat
bash scripts/backup.sh --list   # liste les backups existants
bash scripts/backup.sh --verify # valide le dernier backup
```

Backups automatiques : tous les jours à 02:00 UTC par le conteneur `db-backup`. Rétention : 14 jours.

### 5.6 Restauration (disaster recovery)

```bash
# Depuis le dernier backup
bash scripts/restore.sh --latest

# Depuis un fichier spécifique
bash scripts/restore.sh /backups/guineecare_20260621_020000.dump

# Depuis un fichier sur l'hôte
bash scripts/restore.sh --host backups/guineecare_20260621_020000.dump
```

⚠️  La restauration **drop** la base existante — à n'utiliser qu'en cas de recovery.

### 5.7 Rotation des secrets

Rotation du `AUTH_SECRET` (force tous les utilisateurs à se reconnecter) :

```bash
# 1. Générer un nouveau secret
NEW_SECRET=$(openssl rand -hex 48)

# 2. Modifier .env.production
sed -i "s|^AUTH_SECRET=.*|AUTH_SECRET=$NEW_SECRET|" .env.production

# 3. Redémarrer le backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production restart backend

# 4. Vérifier
curl https://chu-donka.guineecare.gn/health
```

Rotation du `METRICS_TOKEN` :

```bash
NEW_TOKEN=$(openssl rand -hex 32)
sed -i "s|^METRICS_TOKEN=.*|METRICS_TOKEN=$NEW_TOKEN|" .env.production
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production restart backend

# Vérifier
curl -H "Authorization: Bearer $NEW_TOKEN" https://chu-donka.guineecare.gn/metrics
```

---

## 6. Monitoring

### 6.1 Health checks (built-in)

| Endpoint | Fréquence | Alert si |
|----------|-----------|----------|
| `GET /health` | 30s | ≠ 200 |
| `GET /health/live` | 10s | ≠ 200 |
| `GET /health/ready` | 60s | ≠ 200 |

Exemple Prometheus scrape config (si Prometheus externe) :

```yaml
scrape_configs:
  - job_name: 'guineecare'
    scheme: https
    metrics_path: /metrics
    bearer_token: '<METRICS_TOKEN>'
    static_configs:
      - targets: ['chu-donka.guineecare.gn:443']
```

### 6.2 Métriques clés à surveiller

| Métrique | Source | Seuil alerte |
|----------|--------|--------------|
| `http_requests_total` | `/metrics` | — |
| `http_request_duration_seconds` P95 | `/metrics` | > 2s |
| `http_requests_total{status=~"5.."}` | `/metrics` | > 0.1% du trafic |
| DB connections actives | `pg_stat_activity` | > 80 |
| Disk usage `%` | `df -h` | > 85% |
| Memory usage `%` | `free -m` | > 90% |
| Backup status | `scripts/backup.sh --verify` | Échec 2 jours consécutifs |

### 6.3 Log aggregation

Les logs backend sont en JSON structuré (v0.7.0+) —可直接 parsables par Loki, ELK, ou Datadog.

Exemple de requête Loki pour les erreurs backend :

```
{container="guineecare-backend"} |= "ERROR" | json | level == "ERROR"
```

---

## 7. Procédures d'incident

### 7.1 P0 — Site indisponible

**Symptômes** : `curl https://chu-donka.guineecare.gn/health` échoue ou timeout.

**Diagnostic** :
```bash
# 1. Status des conteneurs
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production ps

# 2. Logs backend (dernières 5 min)
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production logs --since 5m backend

# 3. Logs nginx
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production logs --since 5m nginx

# 4. Connexion DB
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production exec postgres pg_isready -U guineecare
```

**Actions** :
- Si backend down → `restart backend`
- Si postgres down → `restart postgres`, attendre healthy, puis `restart backend`
- Si disk full → `docker system prune -af --volumes` (⚠️  vérifier d'abord les volumes)
- Si memory full → identifier le conteneur gourmand avec `docker stats`

### 7.2 P1 — Dégradation lente

**Symptômes** : temps de réponse > 5s, taux d'erreur 5xx > 1%.

**Actions** :
```bash
# 1. Vérifier la charge
docker stats --no-stream

# 2. Connexions DB
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production exec postgres \
    psql -U guineecare -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# 3. Requêtes lentes
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production exec postgres \
    psql -U guineecare -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query
        FROM pg_stat_activity
        WHERE state = 'active' AND now() - pg_stat_activity.query_start > interval '5 seconds';"

# 4. Si overload → augmenter replicas backend (nécessite docker swarm/k8s)
```

### 7.3 P1 — Fuite de secret

Si `AUTH_SECRET` ou `DB_PASSWORD` est compromis :

1. **Rotation immédiate** du secret (voir section 5.7).
2. **Révocation des tokens** : `DELETE FROM revoked_jtis;` (force tous les users à se reconnecter).
3. **Audit log** : consulter `/api/v1/audit?event=login&from=<date>` pour identifier les connexions suspectes.
4. **Communication** aux utilisateurs concernés.

### 7.4 P2 — Restauration après perte de données

```bash
# 1. Stop backend (éviter écrasement)
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production stop backend

# 2. Identifier le backup à restaurer
bash scripts/backup.sh --list

# 3. Vérifier le backup
bash scripts/backup.sh --verify

# 4. Restaurer
bash scripts/restore.sh --latest

# 5. Vérifier l'intégrité
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production exec postgres \
    psql -U guineecare -c "SELECT COUNT(*) FROM patients; SELECT COUNT(*) FROM users;"

# 6. Restart backend
docker compose -f docker-compose.yml -f docker-compose.prod.yml \
    --env-file .env.production start backend
```

---

## 8. Maintenance planifiée

### 8.1 Fenêtres de maintenance

- **Quotidienne** : 02:00–02:30 UTC (backup DB, pas d'impact utilisateur).
- **Hebdomadaire** : dimanche 03:00–04:00 UTC (renouvellement cert TLS, patches sécurité).
- **Mensuelle** : premier samedi du mois 01:00–03:00 UTC (mises à jour applicatives).

### 8.2 Communication

Pour toute maintenance impactante :
1. Prévenir la direction du CHU Donka **48h à l'avance**.
2. Afficher une bannière dans l'app (notification système v0.7).
3. Page de maintenance sur `https://chu-donka.guineecare.gn/maintenance` (TODO v1.1).

---

## 9. Contacts

| Rôle | Nom | Contact |
|------|-----|---------|
| Tech lead GuinéeCare | (à compléter) | tech@guineecare.gn |
| Ops CHU Donka | (à compléter) | ops@chu-donka.gn |
| Direction CHU Donka | (à compléter) | direction@chu-donka.gn |
| Support ministériel | (à compléter) | sante-numerique@sante.gov.gn |

---

## 10. Checklist go-live

Avant la mise en production :

- [ ] Serveur provisionné selon les specs (section 1).
- [ ] DNS `chu-donka.guineecare.gn` pointe vers le serveur.
- [ ] Certificats TLS Let's Encrypt valides (vérifier `certbot certificates`).
- [ ] `.env.production` configuré avec tous les secrets générés (pas de `CHANGE_ME_*`).
- [ ] `bash scripts/deploy.sh --check-only` passe sans erreur.
- [ ] `bash scripts/deploy.sh` réussit.
- [ ] Super-admin créé via CLI ou HTTP bootstrap.
- [ ] Login testé depuis un navigateur sur le réseau CHU Donka.
- [ ] `/health`, `/health/ready`, `/metrics` répondent 200.
- [ ] TLS vérifié : TLSv1.2 ou 1.3 uniquement.
- [ ] Headers de sécurité présents (HSTS, CSP, X-Frame-Options).
- [ ] Cron de renouvellement Let's Encrypt en place.
- [ ] Backup manuel testé : `bash scripts/backup.sh && bash scripts/backup.sh --verify`.
- [ ] Restore testé en staging.
- [ ] Monitoring Prometheus / Uptime Kuma configuré.
- [ ] Contacts (section 9) renseignés.
- [ ] Personnel CHU Donka formé (voir `docs/formation/conduite-du-changement.md`).
- [ ] Page de maintenance prête.
- [ ] Procédure de rollback documentée (git checkout previous tag + redeploy).

---

## 11. Rollback

En cas d'échec d'une mise à jour :

```bash
cd /opt/guineecare

# 1. Identifier la dernière version stable
git tag --sort=-v:refname | head -5

# 2. Revenir à la version précédente
git checkout v0.10.0  # ou autre tag stable

# 3. Redéployer
bash scripts/deploy.sh

# 4. Si la migration a cassé le schéma, restaurer le backup pré-déploiement
bash scripts/restore.sh --latest
```

> ⚠️  **Toujours** faire un backup manuel avant chaque mise à jour :
> ```bash
> bash scripts/backup.sh
> ```
