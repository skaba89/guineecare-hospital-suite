# Onboarding Nouvel Hôpital — GuinéeCare Hospital Suite

**Version :** v2.3.0 (Phase 8)
**Date :** 2026-07-05
**Public :** Équipe technique de l'hôpital / clinique / ONG qui installe GuinéeCare pour la première fois
**Durée estimée :** 1-3 jours selon la complexité réseau

## Prérequis

### Côté hôpital
- ✅ 1 serveur (VPS, machine virtuelle ou serveur physique) avec :
  - **CPU :** 2 vCPU minimum (4 recommandé)
  - **RAM :** 4 Go minimum (8 Go recommandé pour >50 utilisateurs)
  - **Disque :** 40 Go SSD minimum (100 Go pour >1000 patients/mois)
  - **OS :** Ubuntu 22.04 LTS ou Debian 12 (recommandé)
  - **Accès :** root ou utilisateur sudo
- ✅ 1 nom de domaine (FQDN) : `chu-votre-hopital.gn` ou `clinique-votre-structure.com`
- ✅ 1 adresse IP publique fixe (ou reverse-proxy qui termine TLS)
- ✅ Accès Internet sortant (pour Docker Hub, GitHub Container Registry, mises à jour)
- ✅ 1 certificat TLS (Let's Encrypt gratuit ou commercial) — voir §3
- ✅ 1 administrateur technique désigné (contact opérationnel)

### Côté équipe GuinéeCare (vous)
- ✅ Accès au code source GitHub (`github.com/skaba89/guineecare-hospital-suite`)
- ✅ Image Docker `ghcr.io/skaba89/guineecare-backend:vX.Y.Z` publiée
- ✅ Image Docker `ghcr.io/skaba89/guineecare-frontend:vX.Y.Z` publiée
- ✅ Liste des fonctionnalités à activer (modules : patients, urgences, maternité, pharmacie, labo, imagerie, facturation, etc.)

## Procédure étape par étape

### Étape 1 — Préparation du serveur (30 min)

```bash
# 1.1 Connexion SSH
ssh root@votre-serveur

# 1.2 Mise à jour système
apt update && apt upgrade -y

# 1.3 Installation Docker + Docker Compose v2
curl -fsSL https://get.docker.com | sh
apt install -y docker-compose-plugin git ufw fail2ban

# 1.4 Configuration firewall (ufw)
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP (redirect HTTPS)
ufw allow 443/tcp     # HTTPS
ufw enable

# 1.5 Création utilisateur non-root pour l'application
useradd -m -s /bin/bash guineecare
usermod -aG docker guineecare

# 1.6 Bascule vers l'utilisateur guineecare
su - guineecare
```

### Étape 2 — Récupération du code (10 min)

```bash
# 2.1 Cloner le dépôt
cd /home/guineecare
git clone https://github.com/skaba89/guineecare-hospital-suite.git
cd guineecare-hospital-suite

# 2.2 Vérifier la dernière version stable
git tag --list 'v*' | sort -V | tail -5
git checkout v2.3.0  # ou la dernière version stable
```

### Étape 3 — Configuration TLS (30 min)

```bash
# 3.1 Installer Certbot (Let's Encrypt)
sudo apt install -y certbot

# 3.2 Générer le certificat (le serveur doit être joignable sur http://votre-fqdn)
sudo certbot certonly --standalone -d votre-fqdn.gn

# 3.3 Copier les certificats dans le dossier tls/
mkdir -p tls
sudo cp /etc/letsencrypt/live/votre-fqdn.gn/fullchain.pem tls/
sudo cp /etc/letsencrypt/live/votre-fqdn.gn/privkey.pem   tls/
sudo chown guineecare:guineecare tls/*.pem
chmod 600 tls/*.pem

# 3.4 Renouvellement automatique (crontab)
echo "0 3 * * * /usr/bin/certbot renew --quiet --post-hook 'docker compose -f /home/guineecare/guineecare-hospital-suite/docker-compose.yml -f /home/guineecare/guineecare-hospital-suite/docker-compose.prod.yml restart nginx'" | sudo tee /etc/cron.d/certbot-renew
```

### Étape 4 — Configuration environnement (20 min)

```bash
# 4.1 Copier le template
cp .env.production.template .env.production

# 4.2 Éditer .env.production avec les valeurs de l'hôpital
nano .env.production
```

**Variables à renseigner obligatoirement :**

| Variable | Valeur | Commentaire |
|----------|--------|-------------|
| `ENVIRONMENT` | `production` | Ne pas changer |
| `AUTH_SECRET` | Générer avec `python -c "import secrets; print(secrets.token_urlsafe(48))"` | Clé JWT — 64 chars min |
| `DB_PASSWORD` | Générer avec `python -c "import secrets; print(secrets.token_urlsafe(24))"` | Mot de passe PostgreSQL |
| `DATABASE_URL` | `postgresql+psycopg2://guineecare:DB_PASSWORD@postgres:5432/guineecare` | Remplacer `DB_PASSWORD` |
| `REDIS_PASSWORD` | Générer avec `python -c "import secrets; print(secrets.token_urlsafe(24))"` | Mot de passe Redis |
| `PUBLIC_URL` | `https://votre-fqdn.gn` | FQDN réel |
| `CORS_ORIGINS` | `["https://votre-fqdn.gn"]` | Même FQDN |
| `TRUSTED_PROXIES` | `127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16` | IP proxy de confiance |
| `SEED_DEMO_DATA` | `false` | **OBLIGATOIRE false** en production |
| `LOG_LEVEL` | `INFO` | DEBUG pour diagnostiquer |

```bash
# 4.3 Valider la configuration
bash scripts/deploy.sh --check-only
# Doit afficher : "✓ Env file OK"
```

### Étape 5 — Premier déploiement (15 min)

```bash
# 5.1 Pull des images + démarrage
bash scripts/deploy.sh

# 5.2 Suivi des logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f backend

# 5.3 Vérification santé
curl -k https://votre-fqdn.gn/health
# Attendu : {"status":"ok","service":"guineecare-backend","timestamp":"..."}

curl -k https://votre-fqdn.gn/health/ready
# Attendu : {"status":"ok","checks":{"database":"ok (X ms)"},"timestamp":"..."}
```

### Étape 6 — Création du super-admin hôpital (10 min)

```bash
# 6.1 Créer le super-admin via CLI (mot de passe interactif)
docker compose -f docker-compose.yml -f docker-compose.prod.yml exec backend \
  python -m app.cli create-superuser \
    --email admin@votre-hopital.gn \
    --first-name "Admin" \
    --last-name "Hôpital" \
    --facility-id <facility-id-créé-par-le-seed>

# 6.2 Se connecter sur https://votre-fqdn.gn avec les identifiants créés
# 6.3 Changer IMMÉDIATEMENT le mot de passe
# 6.4 Activer 2FA (Settings → Sécurité → Activer 2FA)
```

### Étape 7 — Création de l'établissement et des utilisateurs (1-2h)

```bash
# Via l'interface web (admin connecté) :
# 1. Admin → Établissements → Nouveau
#    - Nom : "CHU Votre Hôpital"
#    - Code : "CHU-VOTRE"
#    - Type : "CHU" / "Clinique privée" / "Centre de santé" / "Hôpital régional"
#    - Adresse : ...
#
# 2. Admin → Utilisateurs → Nouveau (pour chaque rôle) :
#    - Médecin (DOCTOR)
#    - Infirmier (NURSE)
#    - Sage-femme (MIDWIFE)
#    - Pharmacien (PHARMACIST)
#    - Technicien labo (LAB_TECH)
#    - Caissier (CASHIER)
#    - Administrateur établissement (ADMIN)
#
# 3. Admin → Départements → Créer les services :
#    - Urgences, Médecine interne, Chirurgie, Pédiatrie, Maternité, etc.
```

### Étape 8 — Configuration SMS (optionnel, 30 min)

Si l'hôpital veut envoyer des SMS (rappels RDV, résultats labo) :

```bash
# Via l'interface web → Notifications SMS → Administration
# 1. Ajouter un provider (Orange / MTN / Moov Guinée)
# 2. Configurer les credentials (API key, sender ID)
# 3. Créer des règles de routage par catégorie (RDV, LAB, BILLING)
# 4. Tester avec un numéro interne
```

### Étape 9 — Sauvegarde automatique (15 min)

```bash
# 9.1 Configurer cron backup quotidien à 02:00
echo "0 2 * * * /home/guineecare/guineecare-hospital-suite/scripts/backup.sh >> /var/log/guineecare-backup.log 2>&1" | sudo tee /etc/cron.d/guineecare-backup

# 9.2 Tester un backup immédiatement
bash scripts/backup.sh
# Doit créer : /backups/guineecare_YYYYMMDD_HHMMSS.dump

# 9.3 Vérifier l'intégrité
bash scripts/backup.sh --verify /backups/guineecare_*.dump

# 9.4 Planifier un test de restauration mensuel (procédure docs/deploiement/RUNBOOK_CHU_DONKA.md §6.4)
```

### Étape 10 — Monitoring (optionnel, 1h)

```bash
# 10.1 Configurer Uptime Kuma (gratuit) ou Pingdom sur :
#    - https://votre-fqdn.gn/health (liveness — toutes les 1 min)
#    - https://votre-fqdn.gn/health/ready (readiness — toutes les 5 min)
#    - Alerte email/SMS si statut != 200 pendant > 2 min

# 10.2 Metrics Prometheus (optionnel) :
#    - /metrics est protégé par METRICS_TOKEN
#    - Configurer Prometheus pour scraper avec ce token
```

### Étape 11 — Formation utilisateurs (1-2 jours)

| Rôle | Durée | Support |
|------|-------|---------|
| Médecins | 2h | `docs/formation/fiches-rapides/fiche-medecin.md` |
| Infirmiers | 1h30 | `docs/formation/fiches-rapides/fiche-infirmier.md` |
| Sages-femmes | 1h30 | `docs/formation/fiches-rapides/fiche-sage-femme.md` |
| Pharmaciens | 1h | `docs/formation/fiches-rapides/fiche-pharmacien.md` |
| Labo | 1h | `docs/formation/fiches-rapides/fiche-laboratoire.md` |
| Caissiers | 1h | `docs/formation/fiches-rapides/fiche-caissier.md` |
| Administrateur | 1 jour | `docs/deploiement/guide-administrateur.md` |

### Étape 12 — Validation finale (30 min)

```bash
# 12.1 Checklist go-live
# Voir docs/deploiement/CHECKLIST_PRE_PRODUCTION.md

# 12.2 Test end-to-end :
# - Login admin → créer patient → admission → consultation → prescription → labo → facturation → sortie
# - Test SMS (si configuré)
# - Test impression PDF (prescription, facture, résultat labo)
# - Test backup/restore sur un environnement de test

# 12.3 Mise en production
#    - Annoncer la date aux utilisateurs
#    - Démarrer le cron de backup
#    - Activer le monitoring
#    - Documenter les contacts d'urgence
```

## Modes de déploiement alternatifs

### Mode SaaS cloud (Render + Neon)

Pour un hôpital qui ne veut pas gérer de serveur :

1. Créer un compte Render (https://render.com)
2. Créer une DB Neon PostgreSQL (https://neon.tech)
3. Forker le dépôt GitHub
4. Connecter Render au fork
5. Configurer les variables d'environnement (voir `docs/deploiement/guide-render-neon.md`)
6. Déployer

**Coût :** ~30-50 USD/mois pour un hôpital moyen (Render Starter + Neon free tier)

### Mode cloud privé (VPS Hetzner/DigitalOcean)

Pour un hôpital qui veut contrôler ses données :

1. Louer un VPS (Hetzner CX22 ~5 EUR/mois, DigitalOcean Droplet 4 Go ~24 USD/mois)
2. Suivre la procédure §1 à §12 ci-dessus

**Coût :** ~10-30 USD/mois + nom de domaine (~15 USD/an)

### Mode on-premise (serveur local hôpital)

Pour un hôpital avec contraintes réseau (pas d'Internet stable) :

1. Installer Docker sur un serveur local (voir §1)
2. Suivre la procédure §2 à §12
3. **Spécifique on-premise :**
   - Pas de TLS Let's Encrypt → certificat auto-signé ou interne
   - Pas d'accès Internet → mirror Docker local ou import manuel des images
   - Backup sur disque externe USB + rotation manuelle

**Coût :** 1 serveur (~500-1500 USD investissement initial) + électricité

### Mode démo Render (gratuit)

Pour démonstrations au Ministère ou formations :

1. Utiliser l'instance publique : `https://guineecare.onrender.com`
2. Comptes : `admin@guineecare.com` / `admin123` (et 7 autres — voir README.md)
3. ⚠️ **Données réinitialisées toutes les 24-48h** (free tier Render)
4. ⚠️ **Ne pas stocker de vraies données patients** sur cette instance

## Support et maintenance

| Situation | Contact | Délai |
|-----------|---------|-------|
| Bug critique (indisponibilité) | Voir `RUNBOOK_CHU_DONKA.md` §contacts | < 1h |
| Bug mineur (UX, typo) | Issue GitHub | < 1 semaine |
| Demande fonctionnelle | Issue GitHub | Backlog |
| Formation complémentaire | Équipe GuinéeCare | Planifiée |

## Voir aussi

- `docs/deploiement/RUNBOOK_CHU_DONKA.md` — Runbook opérations
- `docs/deploiement/guide-vps-production.md` — Guide VPS Hetzner
- `docs/deploiement/guide-render-neon.md` — Guide Render + Neon
- `docs/deploiement/guide-administrateur.md` — Guide administrateur quotidien
- `docs/deploiement/CHECKLIST_PRE_PRODUCTION.md` — Checklist pré-go-live
- `docs/formation/quickstart-utilisateur.md` — Onboarding nouvel utilisateur
