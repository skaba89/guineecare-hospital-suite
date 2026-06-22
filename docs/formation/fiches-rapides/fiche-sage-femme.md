# Fiche rapide — Sage-femme

> Public : sage-femme (maïeuticienne)
> Module(s) : Maternity, Patients, Clinical, Laboratory, Quality
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

### 1. Consulter le tableau de bord maternité
1. Après connexion, le tableau de bord maternité affiche : grossesses en suivi, accouchements du jour, CPoN prévues.
2. Vérifier les alertes (grossesses à risque, rendez-vous manqués).
3. Cliquer sur un KPI pour ouvrir la liste correspondante.

> **Astuce** : en début de poste, repérer les CPoN du jour et les accouchements attendus.

### 2. Créer un dossier de grossesse
1. Menu **Maternité** → **Nouveau dossier grossesse**.
2. Rechercher la patiente (ex. « Cissé Aminata ») → la sélectionner.
3. Renseigner DDR, parité, gestité, terme estimé → **Enregistrer**. Le dossier est lié au DPI de la patiente.

> **Attention** : vérifier qu'il n'existe pas déjà un dossier grossesse actif pour cette patiente (doublon).

### 3. Réaliser une consultation prénatale (CPoN)
1. Ouvrir le dossier grossesse → **Nouvelle CPoN**.
2. Saisir le terme (SA), poids, TA, hauteur utérine, mouvements actifs, bruits du cœur fœtal.
3. Cocher les examens prévus (TPI, TdR, moustiquaire) → **Enregistrer**.

### 4. Saisir une échographie obstétricale
1. Dossier grossesse → onglet **Échographies** → **Nouvelle écho**.
2. Type (1er, 2e ou 3e trimestre), terme, biométrie (BIP, PC, PA, LF), poids estimé.
3. **Enregistrer**. Les courbes de croissance sont mises à jour automatiquement.

### 5. Enregistrer un accouchement
1. Dossier grossesse → **Accouchement** → **Nouvel accouchement**.
2. Date/heure, voie (voie basse, césarienne, instrumentalisée), lieu, aide opératoire.
3. Saisir complications éventuelles (hémorragie, éclampsie, dystocie) → **Enregistrer**.

> **Attention** : toute complication maternelle doit aussi être signalée comme incident qualité (action 10).

### 6. Saisir les données du nouveau-né
1. Écran accouchement → section **Nouveau-né**.
2. Saisir sexe, poids (ex. 3 200 g), taille, périmètre crânien, score APGAR à 1, 5 et 10 min.
3. **Enregistrer**. Un dossier patient est généré automatiquement pour le nouveau-né.

### 7. Programmer une CPoN post-natale
1. Dossier grossesse → **CPoN post-natale** → **Nouveau RDV**.
2. Date prévue (J6-J10 post-accouchement), type (CPoN1), rappel SMS si activé.
3. **Enregistrer**. Le rendez-vous apparaît dans le planning maternité.

### 8. Consulter l'historique des grossesses
1. Ouvrir le DPI de la patiente → onglet **Maternité**.
2. Toutes les grossesses passées s'affichent avec leur issue (accouchement, fausse couche, GEU).
3. Cliquer sur une grossesse pour en voir le détail (CPoN, écho, accouchement).

> **Astuce** : comparer les termes et poids de naissance pour dépister une récidive (macrosomie, prématurité).

### 9. Détecter une grossesse à risque
1. Ouvrir le dossier grossesse — les alertes automatiques s'affichent en bannière rouge.
2. Critères : âge < 16 ou > 40, parité ≥ 5, antécédent de césarienne, HTA, diabète, anémie sévère.
3. En cas d'alerte, cliquer **Référer** pour orienter vers un gynéco-obstétricien.

### 10. Référer une patiente vers un spécialiste
1. Dossier grossesse → **Référence** → **Nouvelle référence**.
2. Service cible (gynéco-obstétrique, néonatologie, chirurgie), motif, urgence.
3. **Enregistrer**. La référence est tracée et notifiée au service cible.

### 11. Signaler un incident maternel ou néonatal
1. Menu **Qualité** → **Nouvel incident**.
2. Type (maternel, néonatal, événement indésirable), description, gravité.
3. **Enregistrer**. L'incident remonte au responsable qualité et à la direction.

> **Astuce** : un incident maternel grave (décès, HPP sévère) doit faire l'objet d'une RMM (revue morbidité-mortalité).

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
| Nouveau-né non lié à la mère | Appeler admin pour vérifier le rattachement |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Administrateur** : poste 4012 (8h-17h, lundi au vendredi)
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
