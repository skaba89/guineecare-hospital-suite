# Fiche rapide — Administrateur

> Public : administrateur (ADMIN), responsable informatique
> Module(s) : Users, RBAC, Facilities, Departments, Audit, Feedback, Health
> Version : v1.1.0 — juin 2026
> À imprimer recto-verso et à garder à portée de main au poste de travail.

---

## Connexion

| Étape | Action | Raccourci |
|-------|--------|-----------|
| 1 | Ouvrir le navigateur à l'adresse https://chu-donka.guineecare.gn | — |
| 2 | Saisir email et mot de passe | — |
| 3 | Cliquer **Se connecter** | Entrée |

En cas d'oubli mot de passe : utiliser le compte de secours (procédure papier).
Après 5 échecs : compte verrouillé 15 minutes (y compris ADMIN).

## Actions essentielles

### 1. Créer un nouvel utilisateur
1. Menu **Utilisateurs** → **Nouvel utilisateur**.
2. Saisir email, nom, prénom, rôle, établissement, service. Mot de passe temporaire généré automatiquement.
3. **Enregistrer**. L'utilisateur doit changer son mot de passe à la première connexion.

> **Astuce** : communiquer le mot de passe temporaire en main propre (jamais par email) et faire signer un reçu.

### 2. Modifier le rôle d'un utilisateur
1. Menu **Utilisateurs** → rechercher l'utilisateur → ouvrir sa fiche.
2. Changer le rôle dans le menu déroulant → **Enregistrer**.
3. La modification est tracée dans le journal d'audit avec auteur et horodatage.

> **Attention** : un changement de rôle peut retirer des permissions — prévenir l'utilisateur pour éviter les surprises.

### 3. Activer / désactiver un utilisateur
1. Fiche utilisateur → bouton **Activer** ou **Désactiver**.
2. Confirmer. Un utilisateur désactivé ne peut plus se connecter mais son historique est conservé.
3. Cas typique : départ en retraite, mutation, congé longue durée.

> **Astuce** : désactiver plutôt que supprimer — la suppression est interdite pour préserver la traçabilité.

### 4. Débloquer un compte verrouillé
1. Menu **Utilisateurs** → filtrer par **Verrouillé**.
2. Ouvrir la fiche → **Débloquer**. Le compte est immédiatement utilisable.
3. Vérifier avec l'utilisateur la cause des échecs (mauvais mot de passe, clavier en majuscules).

### 5. Réinitialiser le mot de passe d'un utilisateur
1. Fiche utilisateur → **Réinitialiser le mot de passe**.
2. Un mot de passe temporaire est généré (16 caractères aléatoires).
3. Communiquer en main propre → l'utilisateur devra le changer à la prochaine connexion.

> **Attention** : ne jamais réinitialiser sans vérification d'identité de la demandeur (appelant).

### 6. Créer un rôle personnalisé
1. Menu **RBAC** → **Rôles** → **Nouveau rôle**.
2. Nommer le rôle (ex. « Cadre de santé »), décrire le périmètre.
3. **Enregistrer** puis attribuer les permissions (action 7).

### 7. Attribuer / retirer une permission à un rôle
1. Menu **RBAC** → ouvrir le rôle → onglet **Permissions**.
2. Cocher / décocher les permissions par module (patients:read, patients:write, billing:validate, etc.).
3. **Enregistrer**. La modification est effective immédiatement pour tous les utilisateurs de ce rôle.

> **Attention** : tester les changements de permissions sur un compte test avant de propager à un rôle en production.

### 8. Consulter la matrice RBAC
1. Menu **RBAC** → **Matrice**.
2. La vue d'ensemble affiche tous les rôles × toutes les permissions.
3. Vérifier la cohérence (pas de permission critique à un rôle non-soignant, pas de permission manquante à un rôle soignant).

### 9. Créer un nouvel établissement
1. Menu **Établissements** → **Nouvel établissement**.
2. Saisir nom, type (CHU, hôpital régional, centre de santé), adresse, contact.
3. **Enregistrer**. L'établissement est visible dans la liste et peut recevoir des utilisateurs.

### 10. Créer un nouveau département
1. Menu **Départements** → **Nouveau département**.
2. Sélectionner l'établissement, saisir le nom (ex. « Pédiatrie »), le code, le type (clinique, médico-tech).
3. **Enregistrer**. Le département est visible et peut être associé aux admissions et lits.

### 11. Consulter et filtrer le journal d'audit
1. Menu **Audit** → **Journal complet**.
2. Filtrer par utilisateur, action (login, create, update, delete), date ou plage de dates.
3. Cliquer sur une ligne pour voir le détail (avant/après pour les modifications).

> **Astuce** : pour une investigation de sécurité, filtrer par action `delete` sur les 7 derniers jours.

### 12. Exporter l'audit
1. Journal filtré → bouton **Exporter** (CSV ou PDF).
2. Choisir le périmètre et la période.
3. **Télécharger**. L'export est horodaté et signé de votre nom.

### 13. Lister et résoudre les feedbacks
1. Menu **Feedback** → filtrer par catégorie, statut ou priorité.
2. Ouvrir un feedback → changer le statut (en cours, résolu, wontfix) → saisir une réponse.
3. **Enregistrer**. L'utilisateur reçoit une notification dans l'application.

### 14. Vérifier l'état de santé de l'application
1. Ouvrir `https://chu-donka.guineecare.gn/health` dans un onglet (page publique, sans auth).
2. Vérifier que les composants sont verts : API, base de données, Redis.
3. Pour `/health/ready` (readiness) et `/health/live` (liveness), vérifier aussi en cas d'incident.

> **Astuce** : bookmarquer les trois URLs dans le navigateur du poste admin pour un accès rapide en cas d'incident.

### 15. Lancer un backup manuel
1. SSH sur le serveur → exécuter `bash scripts/backup.sh` (backup manuel).
2. Vérifier la présence du fichier dans `backups/` avec `bash scripts/backup.sh --list`.
3. Vérifier l'intégrité avec `bash scripts/backup.sh --verify <fichier>`.

> **Attention** : avant une opération critique (montée de version, migration), toujours lancer un backup manuel en plus du backup automatique quotidien.

## Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| Ctrl+L | Verrouiller la session |
| Ctrl+S | Enregistrer (dans un formulaire) |
| Ctrl+F | Rechercher (dans une liste) |
| F5 | Rafraîchir la page |
| Échap | Fermer une fenêtre modale |

## Que faire en cas de problème ?

| Problème | Solution |
|----------|----------|
| Page blanche | F5 (rafraîchir), vérifier `/health` |
| Compte ADMIN bloqué | Utiliser le compte de secours (procédure papier) |
| Application inaccessible | Vérifier https://, vérifier nginx + backend, appeler hotline niveau 2 |
| Base de données inaccessible | Vérifier `docker ps`, logs backend, relancer si besoin |
| Backup échec | Vérifier espace disque, retry, alerter le SUPER_ADMIN |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Hotline niveau 2 / SUPER_ADMIN** : adresse fournie par l'équipe projet
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
