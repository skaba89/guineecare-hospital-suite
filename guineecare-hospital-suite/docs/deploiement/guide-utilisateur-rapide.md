# Guide Utilisateur Rapide — GuinéeCare Hospital Suite

**Version :** v2.3.0 (Phase 8)
**Public :** Tout utilisateur de GuinéeCare (médecin, infirmier, sage-femme, pharmacien, labo, caissier, direction)
**Objectif :** Démarrer en 10 minutes avec l'interface

## 1. Connexion

1. Ouvrez votre navigateur sur l'URL fournie par votre administrateur (ex: `https://votre-hopital.gn`)
2. Saisissez votre **email** et **mot de passe** fournis par l'administrateur
3. Cliquez sur **Se connecter**
4. Si vous avez activé la 2FA, saisissez le code TOTP de votre application (Google Authenticator, Authy)

> 🔒 **Première connexion :** Changez immédiatement votre mot de passe (12+ caractères, majuscule + minuscule + chiffre + spécial). Activez la 2FA dans **Mon profil → Sécurité**.

## 2. Interface — 4 zones principales

```
┌─────────────────────────────────────────────────┐
│ Topbar : titre de page + langue FR/EN + statut  │
├──────────┬──────────────────────────────────────┤
│          │                                      │
│ Sidebar  │   Contenu de la page                 │
│ gauche   │                                      │
│          │                                      │
│ - Soins  │                                      │
│ - Urgenc.│                                      │
│ - Services│                                     │
│ - Admin  │                                      │
│ - Système│                                      │
│          │                                      │
├──────────┴──────────────────────────────────────┤
│ Footer : (votre profil, déconnexion)            │
└─────────────────────────────────────────────────┘
```

- **Sidebar gauche :** navigation entre modules (s'adapte à votre rôle)
- **Topbar :** titre de la page courante, bascule langue FR/EN, statut temps réel
- **Contenu :** tableaux, formulaires, graphiques selon la page
- **Toast (bas droite) :** notifications succès/erreur (4s)

## 3. Actions courantes par rôle

### Médecin (DOCTOR)

| Action | Où | Comment |
|--------|-----|---------|
| Voir mes patients | `/patients` | Recherche par nom, numéro, ID |
| Ouvrir un dossier | Clic sur un patient | Affiche démographie, admissions, notes cliniques, labo, imagerie |
| Créer une consultation | `/admissions` → Nouvelle | Type = CONSULTATION |
| Prescrire | Dossier patient → Onglet Clinical → Note PRESCRIPTION | |
| Commander un examen labo | `/lab` → Nouvelle commande | Sélectionner les tests |
| Commander une imagerie | `/imaging` → Nouvelle commande | Spécifier la région |
| Voir urgences | `/emergency` | File d'attente + triage |

### Infirmier (NURSE)

| Action | Où |
|--------|-----|
| Voir les patients | `/patients` |
| Saisir constantes vitales | Dossier patient → Onglet Clinical → Mesures |
| Administrer médicaments | Dossier patient → Onglet Clinical → Notes |
| Suivre les admissions | `/admissions` |
| Urgences — triage | `/emergency/triage` |

### Sage-femme (MIDWIFE)

| Action | Où |
|--------|-----|
| Suivi grossesse | `/maternity` |
| Créer une consultation prénatale | `/maternity` → Nouvelle consultation |
| Enregistrer un accouchement | `/maternity` → Nouvel accouchement |

### Pharmacien (PHARMACIST)

| Action | Où |
|--------|-----|
| Voir le stock | `/pharmacy` |
| Dispenser une prescription | `/pharmacy` → Prescriptions à valider |
| Gérer le stock | `/pharmacy` → Stock → Mouvements |
| Alerte seuil | `/pharmacy` → Produits en rupture |

### Technicien laboratoire (LAB_TECH)

| Action | Où |
|--------|-----|
| Voir les commandes en attente | `/lab` |
| Saisir un résultat | `/lab` → Commande → Saisir résultat |
| Valider un résultat | `/lab` → Résultats à valider |

### Caissier (CASHIER)

| Action | Où |
|--------|-----|
| Voir les factures | `/billing` |
| Encaisser un paiement | `/billing` → Facture → Paiement |
| Imprimer un reçu | `/billing` → Reçu PDF |

## 4. Recherche globale (Ctrl+K)

Appuyez sur **Ctrl+K** (ou **Cmd+K** sur Mac) pour ouvrir la recherche globale :
- Rechercher un patient par nom ou numéro
- Rechercher une facture par ID
- Rechercher une admission
- Accès rapide à n'importe quelle page

## 5. Tableaux — tris et filtres

- **Tri :** cliquez sur l'en-tête de colonne (flèche ▲/▼)
- **Recherche :** champ "Recherche" en haut du tableau
- **Filtre statut :** liste déroulante (si applicable)
- **Pagination :** bas du tableau — navigation ←/→
- **Réinitialiser filtres :** bouton en haut à droite

## 5. Dossier patient — onglets

Quand vous ouvrez un patient (`/patients/{id}`), vous voyez :

| Onglet | Contenu | Rôles |
|--------|---------|-------|
| **Démographie** | Identité, contact, assurance | Tous |
| **Admissions** | Historique des admissions | DOCTOR, NURSE, ADMIN |
| **Clinical** | Notes, prescriptions, diagnostics | DOCTOR, NURSE |
| **Mesures** | Constantes vitales (TA, T°, FC, FR, SpO2, poids, taille) | DOCTOR, NURSE |
| **Laboratoire** | Résultats d'examens | DOCTOR, NURSE, LAB_TECH |
| **Imagerie** | Comptes rendus (radio, échographie, scanner) | DOCTOR, NURSE |
| **Hospitalisation** | Séjours, lits | DOCTOR, NURSE |
| **Maternité** | Grossesses, accouchements | DOCTOR, MIDWIFE |
| **Facturation** | Factures, paiements | DOCTOR (lecture), CASHIER, ADMIN |

## 6. Impression PDF

Sur chaque document important, un bouton **PDF** permet d'imprimer :
- Prescriptions
- Résultats de laboratoire
- Comptes rendus d'imagerie
- Factures
- Reçus de paiement

> 💡 **Astuce :** Utilisez `Ctrl+P` pour imprimer le dossier patient complet (sans sidebar ni topbar — optimisé impression).

## 7. Notifications

- **Cloche 🔔** (topbar) : notifications en temps réel
- **SMS** : si configuré par votre administrateur, vous recevez des SMS pour :
  - Rappels de rendez-vous
  - Résultats de laboratoire prêts
  - Alerte stock pharmacie
- **Email** : si configuré

## 8. Langue FR/EN

Bouton 🌐 en haut à droite pour basculer FR/EN. Tous les labels, messages d'erreur et notifications sont traduits.

## 9. Problèmes fréquents

### "Session expirée"

Votre token JWT a expiré (60 min). Reconnectez-vous. Si le problème persiste, votre compte a peut-être été désactivé — contactez l'administrateur.

### "403 — Accès interdit"

Vous n'avez pas la permission pour cette action. Exemples :
- CASHIER ne peut pas accéder à `/clinical`
- PHARMACIST ne peut pas valider un résultat labo
- DOCTOR ne peut pas accéder à `/billing`

### "429 — Trop de requêtes"

Vous avez dépassé le rate limit (5 logins/min, 30 refreshs/min). Attendez 1 minute.

### Page blanche

1. Rafraîchissez (F5)
2. Videez le cache navigateur (Ctrl+Shift+R)
3. Déconnectez/reconnectez
4. Si persistant : contactez l'administrateur avec l'heure exacte et l'URL

### Données lentes à charger

1. Vérifiez votre connexion Internet
2. Le backend peut être en charge — réessayez dans 1 min
3. Si persistant : signalez à l'administrateur

## 10. Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| `Ctrl+K` | Recherche globale |
| `Ctrl+P` | Imprimer / PDF |
| `Esc` | Fermer modale / drawer mobile |
| `Tab` | Navigation clavier (focus visible bleu) |

## 11. Sécurité — bonnes pratiques

- ✅ **Ne partagez jamais votre mot de passe**
- ✅ **Verrouillez votre session** (fermez le navigateur en quittant)
- ✅ **Activez la 2FA** (Mon profil → Sécurité)
- ✅ **Déconnectez-vous** sur un poste partagé
- ✅ **Signalez** tout comportement suspect à l'administrateur
- ❌ **N'écrivez jamais** votre mot de passe sur un post-it
- ❌ **N'envoyez jamais** d'identifiants par email ou SMS

## 12. Aide et support

| Besoin | Contact |
|--------|---------|
| Mot de passe oublié | Administrateur de votre établissement |
| Nouvel utilisateur | Administrateur |
| Bug interface | Administrateur → Issue GitHub |
| Formation complémentaire | Voir `docs/formation/fiches-rapides/` |
| Fiche par rôle | `docs/formation/fiches-rapides/fiche-{votre-role}.md` |

## Voir aussi

- `docs/formation/quickstart-utilisateur.md` — Onboarding détaillé
- `docs/formation/fiches-rapides/` — Fiches par rôle (9 fiches)
- `docs/deploiement/guide-administrateur.md` — Guide administrateur (si vous êtes ADMIN)
