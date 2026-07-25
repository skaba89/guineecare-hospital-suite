# Fiche rapide — Technicien de laboratoire

> Public : technicien de laboratoire, biologiste
> Module(s) : Laboratory, Patients
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

### 1. Consulter la file d'attente laboratoire
1. Après connexion, le tableau de bord labo affiche : demandes en attente, prélèvements en cours, résultats à valider.
2. Cliquer sur **File d'attente** pour voir la liste détaillée par ordre d'arrivée.
3. Repérer les demandes urgentes (étiquette rouge).

> **Astuce** : traiter en priorité les urgences (code rouge) et les prélèvements du matin avant la tournée du technicien.

### 2. Consulter une demande de laboratoire
1. File d'attente → cliquer sur une demande (ex. patient « Condé Mariama »).
2. Vérifier les analyses demandées (NFS, glycémie, sérologie VIH, etc.), le prescripteur et le service.
3. Noter les remarques (à jeun, urgence, échantillon spécial).

### 3. Créer un prélèvement
1. Demande de labo → **Créer prélèvement**.
2. Saisir la date/heure du prélèvement, le type d'échantillon (sang, urine, LCR), le n° de tube.
3. **Enregistrer**. Le prélèvement est horodaté et lié à la demande.

> **Attention** : étiqueter immédiatement le tube avec le n° patient et vérifier l'identité à 3 critères.

### 4. Saisir un résultat d'analyse
1. Prélèvement → **Saisir résultats**.
2. Pour chaque analyse : valeur numérique, unité (g/L, mmol/L, UI/L), valeurs de référence.
3. Les valeurs hors normes sont surlignées automatiquement → **Enregistrer**.

> **Astuce** : pour les résultats texte (frottis, culture), utiliser le champ texte libre structuré.

### 5. Valider un résultat
1. Résultats saisis → **Valider** (technicien) ou soumettre pour validation biologiste si requis.
2. Le statut passe à `validated`, le prescripteur est notifié.
3. Le résultat est verrouillé — toute modification laissera une trace d'audit.

> **Attention** : un résultat critique (K+ > 6,5, glycémie < 0,4) doit être téléphoné au prescripteur en plus de la validation informatique.

### 6. Rejeter un prélèvement non conforme
1. Prélèvement → **Rejeter**.
2. Motif obligatoire (échantillon hémolysé, insuffisant, mauvais tube, étiquetage incorrect).
3. **Enregistrer**. Le statut passe à `rejected`, le prescripteur est notifié pour re-demande.

### 7. Filtrer les demandes par statut
1. File d'attente → filtre **Statut** (en attente, prélevé, en cours, validé, rejeté).
2. La liste se met à jour.
3. Utile pour suivre les demandes en cours de traitement.

### 8. Filtrer les demandes par analyse
1. File d'attente → filtre **Analyse** (NFS, glycémie, sérologie VIH, etc.).
2. Permet de regrouper les prélèvements similaires pour gain de temps.
3. Combiner avec un filtre date pour planifier une série d'analyses.

### 9. Consulter l'historique des résultats d'un patient
1. Menu **Patients** → rechercher le patient (ex. « Camara Boubacar »).
2. DPI → onglet **Labo** → tous les résultats passés s'affichent par date.
3. Cliquer sur un résultat pour voir le détail (valeurs, prescripteur, valideur).

> **Astuce** : comparer les résultats successifs pour suivre l'évolution d'un paramètre (ex. HbA1c, charge virale).

### 10. Imprimer un résultat validé
1. Résultat validé → bouton **Imprimer** (ou Ctrl+P).
2. Le navigateur génère une mise en page correcte grâce aux styles d'impression.
3. Tamponner et remettre au patient ou transmettre au service prescripteur.

> **Attention** : ne jamais imprimer un résultat non validé — il pourrait être modifié ensuite.

### 11. Signaler une anomalie
1. Menu **Qualité** → **Nouvel incident**.
2. Type (échantillon hémolysé, erreur de saisie, panne d'analyseur), description, gravité.
3. **Enregistrer**. L'anomalie remonte au responsable qualité.

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
| Résultat saisi par erreur | Ne pas supprimer — ajouter un correctif et signaler |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Administrateur** : poste 4012 (8h-17h, lundi au vendredi)
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
