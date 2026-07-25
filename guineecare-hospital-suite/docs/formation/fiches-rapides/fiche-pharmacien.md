# Fiche rapide — Pharmacien

> Public : pharmacien, préparateur en pharmacie
> Module(s) : Pharmacy, Patients, Billing
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

### 1. Consulter le tableau de bord pharmacie
1. Après connexion, le tableau de bord affiche : stock critique, ruptures imminentes, dispensations du jour.
2. Vérifier les alertes rouges (produits sous le seuil d'alerte).
3. Cliquer sur une alerte pour ouvrir la fiche produit concerné.

> **Astuce** : traiter les alertes critiques en début de poste pour anticiper les commandes.

### 2. Consulter le stock par produit
1. Menu **Pharmacie** → onglet **Stock**.
2. La liste affiche les produits avec quantité, seuil d'alerte, péremption proche.
3. Cliquer sur un produit (ex. « amoxicilline 500 mg ») pour voir son historique de mouvements.

### 3. Rechercher un produit par nom ou DCI
1. Onglet **Stock** → champ de recherche.
2. Taper la DCI (ex. « paracétamol ») ou le nom commercial → **Entrée**.
3. Toutes les formes (comprimé, sirop, suppositoire) s'affichent.

> **Astuce** : utiliser des mots-clés courts (« artéméther », « Coartem ») pour gagner du temps.

### 4. Filtrer les produits en rupture de stock
1. Onglet **Stock** → filtre **Statut** → **Rupture**.
2. La liste ne contient que les produits à quantité zéro.
3. Générer un bon de commande à partir de la liste filtrée.

### 5. Filtrer les produits en seuil d'alerte
1. Onglet **Stock** → filtre **Statut** → **Seuil d'alerte**.
2. La liste contient les produits dont la quantité ≤ seuil d'alerte.
3. Anticiper la commande pour éviter la rupture.

### 6. Réceptionner une livraison
1. Menu **Pharmacie** → **Réceptions** → **Nouvelle réception**.
2. Sélectionner le fournisseur, le n° de bon de commande, la date.
3. Saisir les lignes (produit, quantité, lot, péremption) → **Valider**. Le stock est incrémenté et le mouvement est tracé.

> **Attention** : vérifier la conformité des lots et dates de péremption avant de valider la réception.

### 7. Créer un mouvement de stock manuel (ajustement)
1. Fiche produit → **Nouveau mouvement**.
2. Type (entrée, sortie, perte, casse), quantité, motif (obligatoire).
3. **Enregistrer**. Le mouvement est tracé dans l'historique avec auteur et horodatage.

### 8. Dispenser un médicament à un patient
1. Menu **Pharmacie** → **Dispensation** → **Nouvelle dispensation**.
2. Rechercher le patient (ex. « Touré Ousmane ») → sélectionner la prescription à dispenser.
3. Vérifier quantités → **Valider**. Le stock est décrémenté et la dispensation est tracée.

> **Astuce** : en cas de dispensation partielle (stock insuffisant), le système garde la ligne restante pour une dispensation ultérieure.

### 9. Vérifier une prescription avant dispensation
1. Ouvrir la prescription du patient dans la dispensation.
2. Le système affiche les allergies du patient et les interactions médicamenteuses.
3. En cas d'alerte rouge, ne pas dispenser — appeler le prescripteur pour modification.

> **Attention** : une interaction contre-indiquée (ex. kétorolac + anticoagulant) impose un retour au prescripteur.

### 10. Signaler une rupture de stock imminente
1. Menu **Pharmacie** → **Alertes** → **Nouvelle alerte**.
2. Produit concerné, quantité restante, délai estimé de rupture.
3. **Enregistrer**. L'alerte remonte à l'ADMIN et à la direction pour décision.

### 11. Exporter l'inventaire de stock
1. Onglet **Stock** → bouton **Exporter**.
2. Choisir le format (CSV ou PDF) et le périmètre (tout le stock ou un filtre).
3. **Télécharger**. L'export est horodaté et signé de votre nom.

> **Astuce** : générer l'inventaire mensuel le 1er du mois pour la direction.

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
| Stock négatif après dispensation | Vérifier les mouvements, signaler à l'admin |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Administrateur** : poste 4012 (8h-17h, lundi au vendredi)
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
