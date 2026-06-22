# Fiche rapide — Manipulateur en radiologie

> Public : manipulateur en radiologie, technicien d'imagerie médicale
> Module(s) : Imaging, Patients
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

### 1. Consulter la file d'attente imagerie
1. Après connexion, le tableau de bord imagerie affiche : demandes en attente, examens planifiés du jour, comptes rendus à valider.
2. Cliquer sur **File d'attente** pour voir la liste détaillée.
3. Repérer les demandes urgentes (étiquette rouge).

> **Astuce** : regrouper les examens d'un même type (radios thorax du matin) pour optimiser les passages.

### 2. Consulter une demande d'imagerie
1. File d'attente → cliquer sur une demande (ex. patient « Sylla Ibrahima »).
2. Vérifier le type d'examen (radio thorax, échographie, scanner, IRM), l'indication clinique, le prescripteur.
3. Noter les contre-indications éventuelles (grossesse, allergie produit de contraste, insuffisance rénale).

### 3. Programmer un examen dans le planning
1. Demande d'imagerie → **Planifier**.
2. Choisir la salle, la date et le créneau horaire disponible.
3. **Enregistrer**. Le créneau apparaît dans le planning imagerie et notifie le patient (si SMS activé).

> **Attention** : pour les examens avec produit de contraste, programmer une créneau avec bilan rénal préalable.

### 4. Réaliser un examen et saisir un compte rendu
1. Examen planifié → **Démarrer l'examen** (statut `in_progress`).
2. Réaliser les acquisitions selon protocole.
3. Cliquer **Compte rendu** → saisir le texte (technique, résultats, conclusion) → **Enregistrer**. Le statut passe à `completed`.

> **Astuce** : utiliser les modèles de comptes rendus pré-remplis (radio thorax normale, écho abdominale normale) pour gagner du temps.

### 5. Valider un compte rendu
1. Compte rendu saisi → **Valider** (par le manipulateur ou le radiologue selon protocole).
2. Le statut passe à `validated`, le prescripteur est notifié.
3. Le CR est verrouillé — toute modification laissera une trace d'audit.

> **Attention** : un CR contenant une conclusion critique (nodule suspect, fracture déplacée) doit être téléphoné au prescripteur.

### 6. Filtrer les demandes par type d'examen
1. File d'attente → filtre **Type d'examen** (radio, écho, scanner, IRM, mammographie).
2. La liste se met à jour.
3. Utile pour planifier les salles et le personnel par modalité.

### 7. Filtrer les demandes par statut
1. File d'attente → filtre **Statut** (en attente, planifié, en cours, complété, validé).
2. Permet de suivre les examens en cours de réalisation.
3. Combiner avec un filtre date pour le reporting hebdomadaire.

### 8. Consulter l'historique des examens d'un patient
1. Menu **Patients** → rechercher le patient (ex. « Camara Kadiatou »).
2. DPI → onglet **Imagerie** → tous les examens passés s'affichent par date.
3. Cliquer sur un examen pour voir le compte rendu et les images associées.

> **Astuce** : comparer les examens successifs (radio thorax J0 vs J3) pour suivre l'évolution d'une pathologie.

### 9. Imprimer un compte rendu validé
1. Compte rendu validé → bouton **Imprimer** (ou Ctrl+P).
2. Le navigateur génère une mise en page correcte grâce aux styles d'impression.
3. Tamponner et remettre au patient ou transmettre au service prescripteur.

> **Attention** : ne jamais imprimer un compte rendu non validé — il pourrait être modifié ensuite.

### 10. Signaler une contre-indication
1. Demande d'imagerie → **Signaler contre-indication**.
2. Type (grossesse suspectée, allergie produit de contraste, insuffisance rénale, pacemaker).
3. **Enregistrer**. L'alerte remonte au prescripteur pour décision (annulation, examen alternatif, prémédication).

> **Astuce** : pour toute femme en âge de procréer, vérifier la date des dernières règles avant une radio pelvienne ou abdominale.

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
| Panne de la modalité | Signaler au biomédical, basculer les examens sur une autre salle |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Administrateur** : poste 4012 (8h-17h, lundi au vendredi)
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
