# Fiche rapide — Caissier

> Public : caissier, agent de recouvrement
> Module(s) : Billing, Patients
> Version : v1.1.0 — juin 2026
> À imprimer recto-verso et à garder à portée de main au poste de travail.

---

## Connexion

| Étape | Action | Raccourci |
|-------|--------|-----------|
| 1 | Ouvrir le navigateur à l'adresse https://chu-donka.guineecare.gn | — |
| 2 | Saisir email et mot de passe | — |
| 3 | Cliquer **Se connecter** | Entrée |

En cas d'oubli mot de passe : appeler l'administrateur (poste 4012).
Après 5 échecs : compte verrouillé 15 minutes.

## Actions essentielles

### 1. Consulter le tableau de bord caisse
1. Après connexion, le tableau de bord affiche : encaissements du jour, nombre de paiements, solde caisse courant.
2. Vérifier les alertes (factures impayées anciennes, échéances proches).
3. Cliquer sur un KPI pour ouvrir la liste correspondante.

> **Astuce** : relever le solde d'ouverture de caisse en début de poste et le comparer au fond de caisse physique.

### 2. Créer une facture pour un patient
1. Menu **Facturation** → **Nouvelle facture**.
2. Rechercher le patient (ex. « Diallo Fodé ») → saisir les lignes (consultation, acte, médicament) avec quantité et prix unitaire.
3. **Enregistrer**. La facture est générée avec un n° unique et un total calculé.

> **Attention** : vérifier la catégorie tarifaire du patient (général, ASS, exonéré) avant de saisir les lignes.

### 3. Ajouter une ligne à une facture existante
1. Ouvrir la facture → **Ajouter une ligne**.
2. Sélectionner l'acte ou le produit, quantité, prix unitaire.
3. **Enregistrer**. Le total est recalculé automatiquement.

### 4. Encaisser un paiement (espèces)
1. Ouvrir la facture impayée → **Encaisser**.
2. Mode **Espèces**, saisir le montant reçu et le montant rendu (monnaie).
3. **Valider**. Le paiement est enregistré, un reçu est généré (imprimable).

> **Astuce** : compter les billets devant le patient et confirmer le montant à voix haute.

### 5. Encaisser un paiement (mobile money)
1. Ouvrir la facture → **Encaisser**.
2. Mode **Mobile money** (Orange Money, MTN Money, Moov Money), saisir la référence de transaction.
3. **Valider**. Le paiement est enregistré avec la référence tracée.

> **Attention** : ne jamais valider un paiement mobile money sans avoir reçu la confirmation SMS ou le reçu marchand.

### 6. Consulter l'historique des paiements d'un patient
1. Menu **Patients** → rechercher le patient (ex. « Touré Aïssatou »).
2. DPI → onglet **Facturation** → tous les paiements s'affichent par date.
3. Cliquer sur un paiement pour voir le détail (mode, montant, reçu).

### 7. Imprimer un reçu
1. Paiement enregistré → bouton **Imprimer le reçu** (ou Ctrl+P).
2. Le navigateur génère un reçu mise en page (en-tête CHU Donka, n° reçu, détail, montant, caissier).
3. Imprimer en deux exemplaires (patient + archive caisse).

### 8. Clôturer la caisse en fin de journée
1. Menu **Facturation** → **Clôturer la caisse**.
2. Le système calcule le total encaissé (espèces + mobile money), à rapprocher du fond de caisse physique.
3. Saisir l'écart éventuel et le motif → **Valider**. La caisse est clôturée, un rapport est généré.

> **Attention** : tout écart > 5 000 GNF doit être justifié par écrit et signalé au responsable financier.

### 9. Filtrer les factures par statut
1. Menu **Facturation** → filtre **Statut** (payée, impayée, partielle, annulée).
2. La liste se met à jour.
3. Combiner avec un filtre date pour suivre les impayés anciens.

### 10. Annuler une facture erronée
1. Ouvrir la facture → **Annuler**.
2. Motif obligatoire (erreur de saisie, doublon, patient exonéré).
3. **Valider**. L'annulation est tracée avec auteur et horodatage. Si la facture était payée, un remboursement doit être initié.

> **Attention** : ne jamais annuler une facture payée sans accord du responsable financier.

### 11. Consulter les tarifs applicables
1. Menu **Facturation** → **Tarifs**.
2. La liste affiche les actes et produits avec leur prix par catégorie (général, ASS, exonéré).
3. Filtrer par catégorie pour vérifier un tarif avant facturation.

> **Astuce** : en cas de doute sur un tarif, ne pas facturer « au pif » — vérifier dans la grille tarifaire ou appeler le responsable financier.

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
| Page blanche | F5 (rafraîchir) |
| Données non enregistrées | Vérifier connexion, ne pas fermer la page |
| Compte bloqué | Attendre 15 min ou appeler admin (poste 4012) |
| Application inaccessible | Vérifier https://, appeler hotline niveau 1 |
| Paiement encaissé deux fois | Ne pas rendre la monnaie — signaler au responsable financier pour régularisation |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Administrateur** : poste 4012 (8h-17h, lundi au vendredi)
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
