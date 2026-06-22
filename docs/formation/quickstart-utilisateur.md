# Guide de prise en main rapide — GuinéeCare Hospital Suite

> Public : tout nouvel utilisateur (tous rôles confondus)
> Durée de lecture : 10 minutes
> Objectif : être capable de se connecter, de naviguer et de réaliser
> sa première action dans l'application en moins de 15 minutes.

---

## 1. Pré-requis

- Un compte utilisateur vous a été remis par l'administrateur (email +
  mot de passe temporaire).
- Vous disposez d'un poste de travail connecté au réseau interne du
  CHU Donka, avec un navigateur récent (Chrome, Firefox, Edge — version
  2023 ou ultérieure).
- Votre mot de passe temporaire doit être changé à la première
  connexion (12 caractères minimum, incluant majuscule, minuscule,
  chiffre et caractère spécial).

## 2. Se connecter

1. Ouvrez votre navigateur à l'adresse **https://chu-donka.guineecare.gn**
   (notez le `https` — la connexion est chiffrée).
2. Saisissez votre email et votre mot de passe.
3. Cliquez sur **Se connecter**.
4. Si c'est votre première connexion, le système vous demande de
   changer votre mot de passe. Choisissez un mot de passe robuste et
   mémorisable (évitez les dates de naissance, prénoms d'enfants).
5. Vous arrivez sur le **Tableau de bord** — votre page d'accueil.

## 3. Naviguer dans l'application

La barre latérale gauche (menu) contient tous les modules auxquels
vous avez accès. Selon votre rôle, certains modules n'apparaîtront pas
— c'est normal, c'est le contrôle d'accès basé sur les rôles (RBAC).

En haut à droite, vous trouvez :

- **L'icône cloche** 🔔 — vos notifications (résultats de labo
  disponibles, nouvelles admissions, alertes).
- **L'icône retour** 💬 — pour envoyer un feedback à l'équipe projet
  (bug, suggestion, question, praise).
- **Votre nom** — un menu déroulant pour accéder à vos préférences
  (langue, thème clair/sombre, taille de pagination, fréquence de
  rafraîchissement du tableau de bord) et vous déconnecter.

## 4. Réaliser sa première action

### Cas A : agent d'admission

1. Cliquez sur **Patients** dans le menu.
2. Cliquez sur **Nouveau patient** (bouton en haut à droite).
3. Remplissez le formulaire (nom, prénom, date de naissance, sexe,
   adresse, téléphone). Les champs marqués d'un astérisque `*` sont
   obligatoires.
4. Cliquez sur **Enregistrer**. Le numéro de dossier patient (format
   `PAT-YYYYMMDDHHMMSS`) est généré automatiquement.
5. Le patient apparaît dans la liste. Vous pouvez maintenant créer
   une admission pour ce patient (menu **Admissions** → **Nouvelle
   admission**).

### Cas B : médecin

1. Cliquez sur **Patients** dans le menu.
2. Recherchez le patient (par nom, numéro de dossier, ou téléphone).
3. Cliquez sur le patient pour ouvrir son Dossier Patient Informatisé
   (DPI).
4. Le DPI contient plusieurs onglets : **Admissions**, **Constantes**,
   **Diagnostic**, **Ordonnances**, **Labo**, **Imagerie**, **Notes
   cliniques**.
5. Pour saisir une consultation, ouvrez l'onglet **Notes cliniques**
   → **Nouvelle note**.

### Cas C : infirmier

1. Cliquez sur **Hospitalisation** dans le menu.
2. Le **Bed-board** affiche tous les lits de votre service, avec leur
   état (libre, occupé, en nettoyage).
3. Cliquez sur un lit occupé pour ouvrir le DPI du patient.
4. Onglet **Constantes** → **Nouvelle mesure** (tension, température,
   pouls, poids, taille). Les constantes sont datées et horodatées
   automatiquement.

### Cas D : pharmacien

1. Cliquez sur **Pharmacie** dans le menu.
2. Onglet **Stock** — consultez les quantités disponibles par produit.
3. Onglet **Dispensation** — pour délivrer un médicament à un patient
   (recherche patient → recherche produit → quantité → validation).
4. Le stock est décrémenté automatiquement. Les seuils d'alerte
   déclenchent une notification au pharmacien en chef.

## 5. Personnaliser son espace

Cliquez sur votre nom en haut à droite → **Préférences**. Vous pouvez :

- Changer la langue (français ou anglais).
- Basculer en thème sombre (utile en garde de nuit).
- Ajuster la taille de pagination (5, 10, 20, 50, 100, 200).
- Régler la fréquence de rafraîchissement automatique du tableau de
  bord (0 = désactivé, 30 s par défaut, jusqu'à 600 s).

Vos préférences sont sauvegardées sur votre compte — elles vous
suivent sur n'importe quel poste.

## 6. Consulter ses items récents

Le menu **Mon profil → Items récents** affiche les 20 derniers
patients, demandes de labo, ordonnances d'imagerie, etc. que vous avez
consultés. C'est un raccourci pratique pour reprendre le travail après
une interruption.

## 7. Envoyer un feedback

Vous avez repéré un bug ? Vous avez une idée d'amélioration ? Cliquez
sur l'icône retour 💬 en haut à droite :

1. **Catégorie** (obligatoire) : bug, suggestion, question, praise.
2. **Priorité** : low, normal, high, urgent (par défaut normal).
3. **Sujet** (optionnel) : un titre court.
4. **Message** (obligatoire) : décrivez ce que vous avez vu ou ce que
   vous souhaitez. Soyez précis — mentionnez le patient concerné si
   pertinent (numéro de dossier uniquement, pas de nom par souci de
   confidentialité).
5. **URL de la page** (auto-rempli) : pour aider l'équipe à reproduire.

Tous les retours sont lus par l'équipe projet sous 48 h ouvrées. Vous
recevrez une réponse dans l'application (notification) quand votre
retour sera traité.

## 8. Que faire en cas de problème ?

| Problème | Action |
|----------|--------|
| Mot de passe oublié | Contactez l'administrateur (poste 4012) |
| Compte bloqué (5 échecs) | Attendez 15 min OU contactez l'administrateur |
| Page blanche / erreur 500 | Rafraîchissez (F5). Si persistant, envoyez un feedback de type bug |
| Impossible de trouver un patient | Vérifiez l'orthographe, essayez par numéro de dossier |
| Données non enregistrées | Vérifiez votre connexion réseau, ne fermez pas la page |
| Application inaccessible | Vérifiez que vous êtes sur https://chu-donka.guineecare.gn (pas http) |

En cas de blocage complet, appelez la **hotline niveau 1** au numéro
affiché dans la salle de pause de votre service.

## 9. Règles d'or

1. **Ne partagez jamais votre mot de passe** — chaque action est
   tracée à votre nom (audit log). Si quelqu'un d'autre utilise votre
   compte, vous êtes responsable.
2. **Verrouillez votre session** quand vous vous éloignez du poste
   (Ctrl+L ou menu → Verrouiller).
3. **Déconnectez-vous** en fin de journée (menu → Déconnexion).
4. **Ne supprimez jamais** un patient ou une admission — utilisez les
   statuts (annulé, fermé) pour préserver l'historique.
5. **Signalez tout bug** via le canal feedback — ne le gardez pas pour
   vous, d'autres rencontrent peut-être le même.

## 10. Aller plus loin

- Consultez la **fiche rapide** spécifique à votre rôle (voir
  [`fiches-rapides/`](fiches-rapides/)) pour les 10 actions les plus
  courantes.
- Lisez la **FAQ** ([`faq-utilisateurs.md`](faq-utilisateurs.md)) pour
  les questions fréquentes.
- Référez-vous au **parcours de recette** de votre rôle
  ([`parcours-recette-par-role.md`](parcours-recette-par-role.md))
  pour la liste des actions critiques à maîtriser.

Bienvenue sur GuinéeCare !
