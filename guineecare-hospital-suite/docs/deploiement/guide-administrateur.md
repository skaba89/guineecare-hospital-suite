# Guide Administrateur — GuinéeCare Hospital Suite

**Version :** v2.3.0 (Phase 8)
**Public :** Administrateur établissement (rôle `ADMIN`) ou super-admin national (`SUPER_ADMIN`)
**Objectif :** Opérer GuinéeCare au quotidien — utilisateurs, rôles, établissements, audit, sauvegardes

## Rôles et responsabilités

| Rôle | Périmètre | Ce que vous pouvez faire |
|------|-----------|--------------------------|
| `SUPER_ADMIN` | National (tous établissements) | Tout : créer établissements, gérer tous les utilisateurs, voir tous les audits |
| `ADMIN` | Votre établissement | Gérer les utilisateurs de votre établissement, voir les audits de votre établissement |

> ⚠️ **Important :** En tant qu'ADMIN, vous ne voyez QUE les données de votre établissement. Vous ne pouvez pas créer de `SUPER_ADMIN` (réservé au niveau national).

## Tâches quotidiennes

### 1. Tableau de bord administrateur

Au login, vous arrivez sur le tableau de bord. Pour l'administration, allez sur :
- **Utilisateurs** (`/users`) — gérer les comptes
- **Rôles & Permissions** (`/rbac`) — voir la matrice (lecture seule pour ADMIN)
- **Établissements** (`/facilities`) — voir votre établissement
- **Services** (`/departments`) — gérer les départements
- **Audit** (`/audit`) — consulter le journal d'audit
- **Activité** (`/activity`) — flux d'activité (SUPER_ADMIN uniquement)

### 2. Gestion des utilisateurs

#### Créer un nouvel utilisateur

1. `/users` → bouton **Nouveau**
2. Remplir :
   - **Email** (obligatoire, unique)
   - **Prénom / Nom**
   - **Rôle** (parmi les 8 disponibles)
   - **Établissement** (le vôtre par défaut)
   - **Mot de passe** (12+ caractères, majuscule + minuscule + chiffre + spécial)
3. Valider — l'utilisateur reçoit son mot de passe (à transmettre sécurisément)

#### Désactiver un utilisateur (départ employé)

1. `/users` → ligne de l'utilisateur → **Éditer**
2. Décocher **Actif**
3. Sauvegarder

> 🔒 **Sécurité (v2.2.0) :** La désactivation enregistre `last_disabled_at`. Tous les tokens JWT émis avant cette date sont invalidés immédiatement — l'utilisateur ne peut plus se connecter même avec un token valide.

#### Réinitialiser un mot de passe oublié

1. `/users` → ligne → **Éditer**
2. Nouveau mot de passe (12+ caractères)
3. L'ancien mot de passe est définitivement perdu (hachage bcrypt non réversible)
4. Le hash du mot de passe est journalisé dans l'audit comme `[REDACTED]`

### 3. Gestion des services (départements)

1. `/departments` → **Nouveau**
2. Nom (ex: "Médecine Interne"), Code (ex: "MED"), Type (medical/surgical/etc.)
3. Lier à votre établissement

### 4. Audit et traçabilité

#### Consulter le journal d'audit

1. `/audit` — filtres : date, utilisateur, action, type de ressource
2. Chaque entrée contient :
   - **Horodatage** (UTC)
   - **Utilisateur** (email + rôle)
   - **Action** (ex: `patient.read`, `user.update`, `auth.login`)
   - **Ressource** (type + ID)
   - **IP + User-Agent** (traçabilité réseau)
   - **Statut HTTP** (200, 403, 500, etc.)

#### Événements audités (depuis v2.2.0)

| Action | Quand | Niveau |
|--------|-------|--------|
| `auth.login` | Login réussi | Toujours |
| `auth.login_failed` | Login échoué | Toujours |
| `auth.login_locked` | Compte verrouillé (5 échecs) | Toujours |
| `auth.logout` | Logout | Toujours |
| `patient.read` | Lecture dossier patient | Toujours (v2.2.0) |
| `fhir.patient.read` | Lecture FHIR d'un patient | Toujours (v2.2.0) |
| `user.update` | Modification utilisateur | Toujours |
| `user.create` | Création utilisateur | Toujours |
| `facility.update` | Modification établissement | Toujours |
| `rbac.role.create` | Création rôle | SUPER_ADMIN |
| `audit.read` | Lecture du journal | Toujours |

#### Exporter le journal d'audit (périodique)

Pour conformité, exporter mensuellement :

```bash
# Sur le serveur, via psql
docker compose exec postgres psql -U guineecare -d guineecare \
  -c "COPY (SELECT * FROM audit_logs WHERE created_at >= '2026-01-01' AND created_at < '2026-02-01' ORDER BY created_at) TO STDOUT WITH CSV HEADER" \
  > audit_janvier_2026.csv

# Stocker dans un lieu sécurisé (rétention 5 ans recommandée pour données de santé)
```

## Tâches hebdomadaires

### 1. Vérifier les sauvegardes

```bash
# Sur le serveur
ls -lh /backups/guineecare_*.dump | tail -7
# Doit afficher 7 backups (un par jour)

# Tester l'intégrité du dernier
bash scripts/backup.sh --verify /backups/guineecare_$(date +%Y%m%d)*.dump
```

### 2. Vérifier les logs d'erreur

```bash
# Erreurs 500 des 7 derniers jours
docker compose logs backend --since 168h | grep -E '"level":"ERROR"' | head -50

# Tentatives de connexion échouées
docker compose logs backend --since 168h | grep "auth.login_failed" | head -20
```

### 3. Vérifier l'espace disque

```bash
df -h /var/lib/docker/volumes
# Alert si > 80% utilisé

# Nettoyer les vieux backups (> 30 jours)
find /backups -name "guineecare_*.dump" -mtime +30 -delete
```

## Tâches mensuelles

### 1. Rotation des mots de passe administrateurs

Politique recommandée :
- ADMIN : rotation tous les 90 jours
- SUPER_ADMIN : rotation tous les 60 jours
- 2FA obligatoire pour ADMIN et SUPER_ADMIN

### 2. Test de restauration backup

Une fois par mois, restaurer un backup sur un environnement de test :

```bash
# Sur serveur de test
bash scripts/restore.sh /backups/guineecare_20260101_020000.dump
# Vérifier que les données sont cohérentes
```

### 3. Revue des accès

- Liste des utilisateurs actifs (`/users?is_active=true`)
- Désactiver les comptes inactifs > 90 jours
- Vérifier les rôles attribués (pas d'ADMIN sans justification)

## Procédures d'incident

### Incident P0 — Indisponibilité totale

1. Vérifier `/health` et `/health/ready`
2. Si backend down : `docker compose restart backend`
3. Si DB down : `docker compose restart postgres`
4. Si toujours down : voir `RUNBOOK_CHU_DONKA.md` §7.1
5. Communiquer aux utilisateurs (email, SMS)

### Incident P1 — Données corrompues

1. **NE PAS modifier les données** — appeler le support
2. Lancer un backup immédiat : `bash scripts/backup.sh`
3. Documenter les symptômes (capture écran, message d'erreur)
4. Préparer la restauration du dernier backup valide

### Incident P2 — Performance dégradée

1. Vérifier `/metrics` (CPU, RAM, latence DB)
2. Identifier les requêtes lentes :
   ```sql
   SELECT query, mean_exec_time, calls
   FROM pg_stat_statements
   ORDER BY mean_exec_time DESC LIMIT 10;
   ```
3. Redémarrer les workers backend si nécessaire

### Sécurité — Compte compromis

1. **Désactiver immédiatement** le compte (`/users` → Éditer → Actif = off)
2. Le `last_disabled_at` (v2.2.0) invalide tous les tokens existants
3. Vérifier l'audit des dernières 24h pour ce compte
4. Changer le mot de passe
5. Réactiver avec un nouveau mot de passe fort
6. Documenter l'incident (post-mortem)

## Conformité données médicales (Guinée)

Voir `docs/securite/CHECKLIST_CONFORMITE_GUINEE_v2.2.md` pour la checklist complète.

Points clés pour l'administrateur :
- ✅ Ne jamais partager votre compte admin
- ✅ Activer 2FA sur tous les comptes ADMIN et SUPER_ADMIN
- ✅ Auditer les accès sensibles (dossiers patients) mensuellement
- ✅ Exporter et archiver le journal d'audit mensuellement
- ✅ Signaler toute violation de données dans les 72h (procédure à définir avec le DPO)
- ✅ Former les nouveaux utilisateurs aux bonnes pratiques sécurité

## Voir aussi

- `docs/securite/MATRICE_RBAC_v2.2.md` — Matrice complète des rôles et permissions
- `docs/deploiement/onboarding-nouvel-hopital.md` — Procédure complète d'installation
- `docs/deploiement/RUNBOOK_CHU_DONKA.md` — Runbook technique détaillé
- `docs/formation/fiches-rapides/fiche-administrateur.md` — Fiche rapide administrateur
