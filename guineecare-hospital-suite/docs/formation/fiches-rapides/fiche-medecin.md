# Fiche rapide — Médecin

> Public : médecin (généraliste ou spécialiste)
> Module(s) : Patients, Clinical, Laboratory, Imaging, Surgery, Hospitalization
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

### 1. Consulter le tableau de bord médecin
1. Après connexion, le tableau de bord affiche les KPI temps réel : patients du jour, hospitalisés de mon service, résultats labo en attente.
2. Vérifier les alertes (cloche 🔔) : résultats critiques, allergies patient.
3. Cliquer sur un KPI pour accéder à la liste correspondante.

> **Astuce** : régler la fréquence de rafraîchissement dans **Préférences** (30 s par défaut) pour suivre les évolutions.

### 2. Ouvrir le DPI complet d'un patient
1. Menu **Patients** → rechercher (ex. « Bangoura Mamadou ») ou coller un numéro `PAT-`.
2. Cliquer sur la ligne patient → DPI complet avec onglets.
3. Vérifier en en-tête les alertes (allergies, antécédents actifs).

### 3. Saisir une note clinique
1. DPI patient → onglet **Notes cliniques** → **Nouvelle note**.
2. Titre court (ex. « Consultation cardiologique »), type (consultation, visite, J5), texte libre.
3. **Enregistrer** (Ctrl+S). La note est horodatée et signée de votre nom.

### 4. Saisir des constantes
1. DPI patient → onglet **Constantes** → **Nouvelle mesure**.
2. Renseigner TA (ex. 130/85), T° (37,2 °C), pouls (78), poids (68 kg), taille (1,70 m).
3. **Enregistrer**. Les valeurs s'affichent dans le graphique d'évolution.

> **Astuce** : pour rattraper une saisie manquée, modifier le champ **Date/Heure** avant d'enregistrer.

### 5. Ajouter un antécédent et une allergie
1. DPI → onglet **Antécédents** → **Nouveau** (HTA, diabète, chirurgie, etc.).
2. Pour les allergies : onglet **Allergies** → **Nouvelle allergie** (ex. « Pénicilline »).
3. **Enregistrer**. L'allergie est signalée en alerte en en-tête du DPI.

> **Attention** : une allergie grave (choc anaphylactique) doit être saisie immédiatement et confirmée à l'infirmier.

### 6. Créer un diagnostic (CIM-10)
1. DPI → onglet **Diagnostic** → **Nouveau diagnostic**.
2. Saisir le code ou le texte (ex. « I10 » ou « HTA essentielle ») — l'autocomplétion propose les codes CIM-10.
3. Statut (actif, résolu, chronique) → **Enregistrer**.

### 7. Créer une prescription médicamenteuse
1. DPI → onglet **Ordonnances** → **Nouvelle prescription**.
2. Ajouter les lignes : DCI (ex. « amoxicilline »), dosage (500 mg), forme (gélule), posologie (1 gélule × 3/j pendant 7 j).
3. **Enregistrer**. La prescription est visible par le pharmacien.

> **Attention** : le système signale interactions et allergies — ne pas ignorer les alertes rouges.

### 8. Créer une demande de laboratoire
1. DPI → onglet **Labo** → **Nouvelle demande**.
2. Cocher les analyses (NFS, glycémie, sérologie VIH, CRP, etc.) et le degré d'urgence.
3. **Enregistrer**. La demande apparaît dans la file d'attente laboratoire.

### 9. Créer une demande d'imagerie
1. DPI → onglet **Imagerie** → **Nouvelle demande**.
2. Type d'examen (radio thorax, échographie, scanner), indication clinique, urgence.
3. **Enregistrer**. La demande est visible par le manipulateur en radiologie.

### 10. Valider une sortie d'hospitalisation
1. DPI patient hospitalisé → onglet **Admissions** → admission en cours.
2. Cliquer **Valider la sortie** → date/heure, destination, diagnostic de sortie.
3. **Enregistrer**. Le lit est libéré et l'admission passe à `closed`.

> **Astuce** : joindre une lettre de sortie (note clinique) pour le médecin traitant ou le service de référence.

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
| Résultat labo non visible | Vérifier le statut `validated` côté laboratoire |

## Contacts utiles

- **Hotline niveau 1** : numéro affiché en salle de pause
- **Administrateur** : poste 4012 (8h-17h, lundi au vendredi)
- **Super-utilisateur de mon service** : <nom à remplir>
- **Envoyer un feedback** : icône 💬 en haut à droite de l'application
