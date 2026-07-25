# Fiche rapide — Infirmier

> Public : infirmier (IDE), infirmier de bloc, infirmier d'urgence
> Module(s) : Hospitalization, Clinical, Emergency, Pharmacy, Quality
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

### 1. Consulter le tableau de bord infirmier
1. Après connexion, vérifier les KPI : lits occupés dans mon service, prescriptions à administrer, soins planifiés du jour.
2. Cliquer sur **Hospitalisation** pour ouvrir le bed-board.
3. Repérer les lits nécessitant une intervention (alerte rouge).

> **Astuce** : rafraîchir manuellement avec F5 avant chaque tournée pour avoir l'état réel.

### 2. Ouvrir le bed-board de mon service
1. Menu **Hospitalisation** → le bed-board affiche tous les lits avec leur état (libre, occupé, nettoyage).
2. Filtrer par service (ex. « Médecine A — 1er étage ») si nécessaire.
3. Les lits occupés affichent le nom du patient (ex. « Sylla Fatoumata ») et le médecin référent.

### 3. Ouvrir le DPI d'un patient hospitalisé
1. Au bed-board, cliquer sur un lit occupé.
2. Le DPI s'ouvre directement à l'onglet **Hospitalisation**.
3. Vérifier les alertes en en-tête (allergies, isolement, biais de chute).

### 4. Saisir des constantes
1. DPI → onglet **Constantes** → **Nouvelle mesure**.
2. Saisir TA, T°, pouls, fréquence respiratoire, SpO₂, poids selon protocole.
3. **Enregistrer** (Ctrl+S). Les constantes sont horodatées et alimentent le graphique.

> **Attention** : les valeurs critiques (TA < 90/60, SpO₂ < 90 %, FC > 130) déclenchent une alerte automatique au médecin.

### 5. Saisir un soin
1. DPI → onglet **Soins** → **Nouveau soin**.
2. Type (pansement, injection, perfusion, sondage), site, observation libre.
3. **Enregistrer**. Le soin est horodaté et signé.

### 6. Administrer un médicament prescrit
1. DPI → onglet **Ordonnances** → prescriptions du jour.
2. Sélectionner la ligne à administrer → **Administrer**.
3. Confirmer l'heure réelle d'administration et la voie. Le statut passe à `administré`.

> **Attention** : vérifier les 5 bons (bon patient, bon médicament, bonne dose, bonne voie, bonne heure) avant de cliquer.

### 7. Consulter les prescriptions en cours
1. Bed-board ou DPI → onglet **Ordonnances**.
2. Filtrer par **À administrer aujourd'hui** pour la tournée.
3. Repérer les prescriptions en attente (statut `prescrit` non administré).

### 8. Saisir une note de transmission
1. DPI → onglet **Notes cliniques** → **Nouvelle note**.
2. Type **Transmission** → décrire l'état du patient, les événements du poste, les points à surveiller.
3. **Enregistrer**. La note est visible par l'équipe suivante à la relève.

> **Astuce** : structurer la note en SBAR (Situation, Briefing, Assessment, Recommendation) pour une relève efficace.

### 9. Effectuer un triage d'urgence
1. Menu **Urgences** → **Triage** → **Nouveau triage**.
2. Évaluer les constantes vitales et la plainte → le système propose un niveau (1 à 5).
3. Valider ou ajuster le niveau → **Enregistrer**. La couleur s'affiche dans la file d'attente.

### 10. Signaler un incident qualité
1. Menu **Qualité** → **Nouvel incident**.
2. Type (chute, erreur médicamenteuse, événement indésirable), description, gravité.
3. **Enregistrer**. L'incident est tracé et transmis au responsable qualité.

> **Astuce** : le signalement est non-punitif — déclarez même les événements sans préjudice pour améliorer la sécurité.

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
| Soin administré non visible | Rafraîchir, vérifier le statut en ordonnance |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Administrateur** : poste 4012 (8h-17h, lundi au vendredi)
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
