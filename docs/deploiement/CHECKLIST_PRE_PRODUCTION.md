# Checklist Pré-Production — GuinéeCare Hospital Suite

**Version :** v2.3.0 (Phase 8)
**Usage :** À valider AVANT chaque mise en production (nouvel hôpital ou montée de version)

## 1. Serveur et infrastructure

- [ ] Serveur accessible en SSH avec utilisateur non-root
- [ ] OS à jour (`apt update && apt upgrade`)
- [ ] Docker 24+ installé
- [ ] Docker Compose v2 installé
- [ ] Firewall (ufw) configuré : 22, 80, 443 uniquement
- [ ] fail2ban actif (protection brute-force SSH)
- [ ] Espace disque ≥ 40 Go (100 Go pour >1000 patients/mois)
- [ ] RAM ≥ 4 Go (8 Go recommandé)
- [ ] CPU ≥ 2 vCPU (4 recommandé)
- [ ] Swap désactivé ou ≥ RAM (évite OOM kill)
- [ ] Timezone configuré (`timedatectl set-timezone Africa/Conakry`)

## 2. DNS et TLS

- [ ] Nom de domaine (FQDN) acheté et configuré
- [ ] Enregistrement A pointant vers l'IP publique du serveur
- [ ] Certificat TLS généré (Let's Encrypt ou commercial)
- [ ] Certificats copiés dans `tls/fullchain.pem` et `tls/privkey.pem`
- [ ] Permissions : `chmod 600 tls/*.pem`
- [ ] Renouvellement automatique configuré (cron)
- [ ] Test : `curl -vI https://votre-fqdn.gn` → TLSv1.3

## 3. Configuration environnement

- [ ] `.env.production` créé depuis `.env.production.template`
- [ ] `ENVIRONMENT=production`
- [ ] `AUTH_SECRET` généré (≥ 48 chars) — PAS `CHANGE_ME_*`
- [ ] `DB_PASSWORD` généré (≥ 24 chars) — PAS `CHANGE_ME_*`
- [ ] `REDIS_PASSWORD` généré — PAS `CHANGE_ME_*`
- [ ] `DATABASE_URL` construit avec `DB_PASSWORD`
- [ ] `PUBLIC_URL` = FQDN réel (https://votre-fqdn.gn)
- [ ] `CORS_ORIGINS` = `["https://votre-fqdn.gn"]` (PAS `["*"]`)
- [ ] `TRUSTED_PROXIES` configuré (IP du reverse-proxy)
- [ ] `METRICS_TOKEN` défini (token fort ≥ 32 chars)
- [ ] `BOOTSTRAP_TOKEN` défini (ou vide pour désactiver)
- [ ] `SEED_DEMO_DATA=false` (OBLIGATOIRE)
- [ ] `LOG_LEVEL=INFO` (DEBUG pour diagnostiquer uniquement)
- [ ] `TOKEN_EXPIRE_MINUTES=60`
- [ ] `SMS_FERNET_KEY` généré (si SMS activé)
- [ ] `bash scripts/deploy.sh --check-only` → "✓ Env file OK"

## 4. Sécurité

- [ ] 2FA activé sur tous les comptes ADMIN et SUPER_ADMIN
- [ ] Mots de passe ≥ 12 caractères (complexité vérifiée)
- [ ] Pas de compte partagé (1 utilisateur = 1 compte)
- [ ] Compte `admin@guineecare.com` désactivé (compte seed démo)
- [ ] Headers de sécurité vérifiés : `curl -I https://votre-fqdn.gn/health`
  - [ ] `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
  - [ ] `Content-Security-Policy: default-src 'self'; ...`
  - [ ] `X-Frame-Options: DENY`
  - [ ] `X-Content-Type-Options: nosniff`
  - [ ] `Permissions-Policy: camera=(), microphone=(), ...`
- [ ] `/metrics` protégé par `METRICS_TOKEN` (test : `curl -I https://votre-fqdn.gn/metrics` → 401)
- [ ] `/docs` et `/redoc` accessibles uniquement depuis IP allowlistées
- [ ] Rate limiting actif (test : 6 logins en 1 min → 429 au 6e)
- [ ] Audit log fonctionnel (login → vérifier entrée `auth.login` dans `/audit`)

## 5. Base de données

- [ ] Migration Alembic à jour : `alembic current` → head
- [ ] Backup initial créé : `bash scripts/backup.sh`
- [ ] Backup vérifié : `bash scripts/backup.sh --verify /backups/guineecare_*.dump`
- [ ] Test de restauration sur environnement de test réussi
- [ ] Cron backup quotidien configuré (`/etc/cron.d/guineecare-backup`)
- [ ] Rétention backups : 30 jours (configuré dans `BACKUP_DIR`)
- [ ] Index PostgreSQL créés (vérifier `pg_stat_user_indexes`)

## 6. Application

- [ ] Backend démarre : `curl https://votre-fqdn.gn/health` → `{"status":"ok"}`
- [ ] Backend ready : `curl https://votre-fqdn.gn/health/ready` → `{"status":"ok","checks":{"database":"ok"}}`
- [ ] Frontend accessible : `curl -I https://votre-fqdn.gn` → 200
- [ ] Login admin fonctionne (compte créé via CLI, PAS admin@guineecare.com)
- [ ] Tous les modules chargent (patients, admissions, urgences, maternité, pharmacie, labo, imagerie, facturation)
- [ ] Création d'un patient test réussie
- [ ] Audit log enregistre l'action `patient.read`
- [ ] Impression PDF fonctionne (prescription, facture, résultat labo)
- [ ] SMS fonctionne (si configuré) — test d'envoi

## 7. Monitoring

- [ ] Uptime Kuma (ou équivalent) configuré sur `/health` (1 min)
- [ ] Alerte email/SMS si statut != 200 pendant > 2 min
- [ ] Prometheus scraping `/metrics` (si METRICS_TOKEN configuré)
- [ ] Log rotation configuré (docker json-file max-size=10m, max-file=3)
- [ ] Vérifier que les logs JSON sont bien produits en prod :
  ```bash
  docker compose logs backend --tail 5 | jq .
  ```

## 8. Performance

- [ ] Temps de réponse `/health/ready` < 200ms
- [ ] Temps de réponse `/patients?page=1` < 1s (avec données seed)
- [ ] Pas d'erreur 500 dans les logs au démarrage
- [ ] Latence DB < 50ms (`/health/ready` affiche la latence)
- [ ] CPU < 50% au repos
- [ ] RAM < 70% au repos

## 9. Documentation et formation

- [ ] Liste des utilisateurs et rôles documentée
- [ ] Contacts d'urgence à jour (RUNBOOK §10)
- [ ] Procédure de restauration testée et documentée
- [ ] Utilisateurs formés (voir `docs/formation/fiches-rapides/`)
- [ ] Administrateur formé (voir `docs/deploiement/guide-administrateur.md`)
- [ ] Guide utilisateur rapide distribué (`docs/deploiement/guide-utilisateur-rapide.md`)

## 10. Conformité

- [ ] Notice d'information patient disponible (en cours de rédaction — voir `docs/securite/CHECKLIST_CONFORMITE_GUINEE_v2.2.md`)
- [ ] Politique de rétention des données définie
- [ ] Procédure de notification de violation (72h) établie
- [ ] DPO désigné (ou rôle attribué)
- [ ] Audit log mensuel exporté et archivé (5 ans)

## 11. Procédure de rollback

- [ ] Tag Git de la version précédente identifié
- [ ] Backup pré-déploiement créé
- [ ] Procédure de rollback testée :
  ```bash
  # 1. Restaurer le backup pré-déploiement si migrations cassées
  bash scripts/restore.sh /backups/guineecare_PRE_DEPLOY.dump
  # 2. Revenir à la version précédente
  git checkout v2.X.Y
  # 3. Redémarrer
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --no-deps backend
  ```

## 12. Go-live

- [ ] Toutes les cases ci-dessus validées ✅
- [ ] Fenêtre de maintenance annoncée (email + affiche)
- [ ] Utilisateurs notifiés de la date et heure
- [ ] Support disponible (équipe technique joignable)
- [ ] Monitoring activé avant l'annonce
- [ ] Backup post-go-live planifié (1h après)

## Sign-off

| Rôle | Nom | Date | Signature |
|------|-----|------|-----------|
| Administrateur technique | | | |
| Responsable hôpital | | | |
| Équipe GuinéeCare | | | |

---

## Voir aussi
- `docs/deploiement/onboarding-nouvel-hopital.md` — Procédure complète d'installation
- `docs/deploiement/RUNBOOK_CHU_DONKA.md` — Runbook opérations
- `docs/deploiement/CHECKLIST_DEPLOIEMENT.md` — Checklist déploiement (technique)
- `docs/deploiement/CHECKLIST_DEMO.md` — Checklist démo ( Ministers / partenaires)
- `docs/securite/CHECKLIST_CONFORMITE_GUINEE_v2.2.md` — Conformité données médicales
