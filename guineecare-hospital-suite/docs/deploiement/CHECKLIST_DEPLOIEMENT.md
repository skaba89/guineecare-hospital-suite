# Checklist Déploiement — GuinéeCare Hospital Suite

**Version :** v2.3.0 (Phase 8)
**Usage :** À suivre À CHAQUE déploiement (nouveau tag ou mise à jour)

## Pré-déploiement (T-1h)

- [ ] Tag Git créé (`git tag v2.X.Y && git push origin v2.X.Y`)
- [ ] CI `deploy-release.yml` déclenchée automatiquement
- [ ] Tests backend passent dans la CI (gate)
- [ ] Build frontend passent dans la CI (gate)
- [ ] Images Docker poussées sur GHCR :
  - `ghcr.io/skaba89/guineecare-backend:v2.X.Y`
  - `ghcr.io/skaba89/guineecare-frontend:v2.X.Y`
- [ ] Release notes lues et validées (`CHANGELOG.md`)
- [ ] Backup pré-déploiement créé :
  ```bash
  bash scripts/backup.sh
  # Renommer pour le repérer
  mv /backups/guineecare_*.dump /backups/guineecare_PRE_DEPLOY_v2.X.Y.dump
  ```
- [ ] Fenêtre de maintenance annoncée (email)

## Déploiement (T)

- [ ] Connexion SSH au serveur
- [ ] `cd /home/guineecare/guineecare-hospital-suite`
- [ ] `git pull origin main && git checkout v2.X.Y`
- [ ] Vérifier `.env.production` (pas de `CHANGE_ME_*`)
- [ ] `bash scripts/deploy.sh`
  - [ ] Pull images GHCR OK
  - [ ] Migrations Alembic appliquées (`alembic upgrade head`)
  - [ ] Backend healthy (wait-for-healthy)
  - [ ] Frontend accessible
  - [ ] Nginx rechargé
  - [ ] Smoke tests passent

## Post-déploiement (T+5min)

- [ ] `curl https://votre-fqdn.gn/health` → `{"status":"ok"}`
- [ ] `curl https://votre-fqdn.gn/health/ready` → `{"status":"ok","checks":{"database":"ok"}}`
- [ ] Login admin OK
- [ ] Page d'accueil charge
- [ ] Création d'un patient test OK
- [ ] Audit log enregistre l'action
- [ ] Vérifier la version dans `/api/v1` :
  ```bash
  curl https://votre-fqdn.gn/api/v1 | jq .version
  # Doit afficher : "2.X.Y"
  ```
- [ ] Vérifier qu'aucune erreur 500 dans les logs des 5 dernières minutes :
  ```bash
  docker compose logs backend --since 5m | grep '"level":"ERROR"' | head
  ```

## Post-déploiement (T+1h)

- [ ] Utilisateurs notifiés de la fin de maintenance
- [ ] Monitoring vérifié (Uptime Kuma → all green)
- [ ] Backup post-déploiement créé
- [ ] Si incident → rollback (voir `RUNBOOK_CHU_DONKA.md` §8)

## Rollback (si incident)

```bash
# 1. Restaurer le backup pré-déploiement si migrations cassées
bash scripts/restore.sh /backups/guineecare_PRE_DEPLOY_v2.X.Y.dump

# 2. Revenir à la version précédente
git checkout v2.X.Y-1
docker compose -f docker-compose.yml -f docker-compose.prod.yml pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 3. Vérifier
curl https://votre-fqdn.gn/api/v1 | jq .version
```

## Voir aussi
- `docs/deploiement/CHECKLIST_PRE_PRODUCTION.md` — Checklist go-live (nouvel hôpital)
- `docs/deploiement/CHECKLIST_DEMO.md` — Checklist démo
- `docs/deploiement/RUNBOOK_CHU_DONKA.md` — Runbook complet
