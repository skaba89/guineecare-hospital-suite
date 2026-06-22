# Fiche rapide — Agent d'admission

> Public : agent d'admission, secrétaire médical
> Module(s) : Patients, Admissions, File d'attente
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

### 1. Créer un nouveau patient
1. Menu **Patients** → bouton **Nouveau patient**.
2. Remplir les champs obligatoires (`*`) : nom, prénom, date de naissance, sexe, téléphone.
3. Cliquer **Enregistrer**. Le numéro `PAT-YYYYMMDDHHMMSS` est généré automatiquement.

> **Astuce** : si la date de naissance est inconnue, saisir le 1er janvier d'une année approximative et cocher **Date approximative**.

### 2. Rechercher un patient par nom
1. Menu **Patients** → champ de recherche en haut de la liste.
2. Taper le nom (ex. « Diallo ») puis **Entrée**.
3. Cliquer sur la ligne du patient pour ouvrir son DPI.

> **Attention** : plusieurs « Diallo » peuvent exister — vérifier la date de naissance et le sexe avant d'ouvrir.

### 3. Rechercher un patient par numéro de dossier
1. Menu **Patients** → coller le numéro `PAT-...` dans le champ de recherche.
2. Le patient unique apparaît. Cliquer pour ouvrir le DPI.

> **Astuce** : le numéro `PAT-` figure sur le carnet de patient et la convocation.

### 4. Ouvrir le DPI d'un patient
1. Cliquer sur la ligne du patient dans la liste.
2. Le DPI s'ouvre avec les onglets : Admissions, Constantes, Diagnostic, Ordonnances, Labo, Imagerie, Notes cliniques.
3. Vérifier en haut le nom, la date de naissance et le sexe.

### 5. Créer une admission programmée
1. Ouvrir le DPI du patient → onglet **Admissions** → **Nouvelle admission**.
2. Sélectionner le service (ex. Médecine interne), le type **Programmée**, la date prévue.
3. Cliquer **Enregistrer**. L'admission apparaît dans la liste des admissions.

### 6. Créer une admission urgente
1. DPI patient → **Admissions** → **Nouvelle admission**.
2. Type **Urgente**, service d'accueil (ex. Urgences réanimation), motif (ex. « douleur thoracique »).
3. **Enregistrer**. Le statut `urgent` est attribué et le service d'urgence est notifié.

> **Attention** : pour les urgences vitales, appeler aussi le 4011 (permanence des urgences) en parallèle.

### 7. Filtrer les admissions par statut
1. Menu **Admissions** → liste des admissions.
2. Ouvrir le filtre **Statut** → choisir (en attente, en cours, clôturée).
3. La liste se met à jour automatiquement.

### 8. Clôturer une admission
1. Ouvrir l'admission depuis le menu **Admissions** ou le DPI patient.
2. Cliquer **Clôturer l'admission** → saisir la date/heure de sortie et la destination (domicile, transfert, décès).
3. **Enregistrer**. Le statut passe à `closed`, le lit est libéré.

### 9. Consulter la file d'attente
1. Menu **File d'attente** (ou **Tableau de bord**).
2. La liste affiche les patients en attente avec leur ordre et leur heure d'arrivée.
3. Vérifier les niveaux de priorité (couleurs : rouge, orange, vert).

### 10. Appeler un patient depuis la file d'attente
1. Dans la file d'attente, repérer le patient suivant (ex. « Camara Aïssata »).
2. Cliquer **Appeler**. Le statut passe à `in_consultation` et le patient est retiré de la file.
3. Annoncer le nom du patient dans la salle d'attente via le guichet.

> **Astuce** : utilisez **Ctrl+F** pour retrouver un nom précis dans une file d'attente longue.

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
| Doublon patient créé | Ne pas supprimer, appeler admin pour fusion |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Administrateur** : poste 4012 (8h-17h, lundi au vendredi)
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
