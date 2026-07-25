# Fiche rapide — Tâches planifiées ⚙️

> Public : SUPER_ADMIN, ADMIN
> Module(s) : Système → Tâches planifiées
> Version : v2.9.2 — juillet 2026
> À imprimer recto-verso et à garder à portée de main au poste de travail.

---

## Accès

| Étape | Action |
|-------|--------|
| 1 | Se connecter en SUPER_ADMIN ou ADMIN |
| 2 | Dans la sidebar, section **SYSTÈME**, cliquer sur **Tâches planifiées** |
| 3 | La page `/tasks-admin` s'affiche avec 3 indicateurs en haut |

## Les 5 tâches disponibles

| Tâche | Planification | Risque |
|-------|---------------|--------|
| 🗑️ Purge audit log | Quotidien 03h00 UTC | ⚠️ Destructrice |
| 💾 Backup database | Quotidien 04h00 UTC | Sécuritaire |
| 📤 Retry SMS pending | 5 minutes | Sécuritaire |
| 📊 Push DHIS2 mensuel | 5 du mois 06h00 UTC | Sécuritaire |
| 🚨 Digest qualité | Quotidien 06h30 UTC | Sécuritaire |

## Déclencher une tâche manuellement

1. Sur la carte de la tâche, cliquer sur **▶ Exécuter maintenant**
2. Une boîte de confirmation s'affiche (⚠️ pour les tâches destructives)
3. Pour `prune_audit_logs` : un prompt demande la rétention en jours (défaut 365)
4. Pour `push_dhis2_monthly` : un prompt demande la période YYYYMM (défaut = mois précédent)
5. Cliquer **OK** — le résultat s'affiche en vert dans la carte

## Historique des exécutions

Le tableau en bas de page affiche les **20 dernières exécutions** (issues du journal d'audit) :
- Date et heure
- Tâche exécutée
- Statut (✓ succès / ✗ échec)
- Détails (paramètres passés)

## Statut de l'infrastructure

| Indicateur | Vert | Orange | Rouge |
|------------|------|--------|-------|
| Worker Celery | Actif | Synchrone (fallback) | — |
| Broker Redis | Configuré | — | Non configuré |
| Tâches disponibles | 5 | — | < 5 |

> ⚠️ **Mode synchrone** : si Worker Celery = "Synchrone", les tâches s'exécutent dans le processus API. C'est fonctionnel mais bloquant (la requête HTTP dure le temps de l'exécution). Pour activer le mode async, configurer Redis + Celery worker.

---

> 📖 Documentation complète : `docs/formation/GUIDE_UTILISATEUR_v2.9.2.md` section 2
> 📞 Support : tech@guineecare.gn — poste 4012
