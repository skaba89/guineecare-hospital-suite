# Formation et conduite du changement — GuinéeCare Hospital Suite

> Version applicative : **v1.1.0** — Pilote CHU Donka
> Public : équipe projet, formation, direction médicale, super-utilisateurs
> Dernière mise à jour : 2026-06-21

---

## 1. Objectifs

Le déploiement de GuinéeCare au CHU Donka ne se résume pas à l'installation
d'un logiciel : il modifie en profondeur les circuits administratifs,
cliniques et financiers de l'hôpital. La conduite du changement vise à
accompagner cette transformation pour atteindre cinq objectifs :

1. **Favoriser l'adoption terrain** — faire en sorte que 80 % des
   utilisateurs actifs se connectent au moins une fois par semaine à la
   fin du premier mois de pilote, et 95 % à la fin du troisième mois.
2. **Former les utilisateurs par rôle** — chaque utilisateur doit maîtriser
   son périmètre fonctionnel (10 parcours métiers distincts, de l'agent
   d'admission au caissier) avant de prendre sa première activité réelle
   dans l'application.
3. **Créer des super-utilisateurs dans chaque service** — un relais
   local identifié et formé (médecin référent, infirmier superviseur,
   pharmacien chef de service) capable de dépanner ses collègues au
   quotidien sans remonter systématiquement vers l'équipe projet.
4. **Réduire la résistance au changement** — anticiper les freins
   culturels (peur de l'ordinateur, défiance envers la traçabilité,
   habitudes papier ancrées depuis des décennies) par un discours
   pédagogique transparent sur les bénéfices et les limites de l'outil.
5. **Stabiliser le démarrage pilote** — limiter les incidents bloquants
   lors des deux premières semaines d'exploitation réelle, période
   critique où les utilisateurs sont les plus vulnérables et où une
   mauvaise expérience peut discréditer durablement le projet.

---

## 2. Publics à former

La plateforme touche dix profils métiers distincts, chacun avec ses
propres parcours, son propre vocabulaire et ses propres contraintes
réglementaires. La formation doit être segmentée : un agent d'admission
n'a pas besoin de savoir utiliser le module bloc opératoire, et un
pharmacien n'a pas à connaître le détail du triage obstétrical.

| Profil | Module(s) prioritaire(s) | Durée formation |
|--------|---------------------------|-----------------|
| Agent d'admission | Patients, Admissions, File d'attente | 1 jour |
| Médecin | DPI clinique, Labo, Imagerie, Bloc, Hospitalisation | 2 jours |
| Infirmier | Constantes, Soins, Hospitalisation, Urgences | 1,5 jour |
| Sage-femme | Maternité, CPoN, Accouchements, Néonatalogie | 1,5 jour |
| Pharmacien | Pharmacie, Stock, Dispensation | 1 jour |
| Technicien laboratoire | Labo, Prélèvements, Validation résultats | 1 jour |
| Manipulateur radiologie | Imagerie, Demandes, Comptes rendus | 1 jour |
| Caissier | Facturation, Caisse, Paiements, Reçus | 1 jour |
| Direction | Reporting, KPI, Audit, Pilotage national | 0,5 jour |
| Administrateur | Users, RBAC, Facilities, Audit, Configuration | 2 jours |

**Total** : ~12 jours de formation, à organiser en deux vagues pour ne
pas immobiliser tout l'hôpital en même temps. Chaque session ne dépasse
pas 8 participants pour garantir la qualité des exercices pratiques.

---

## 3. Dispositif de formation

Le dispositif combine cinq formats complémentaires pour s'adapter aux
différents rythmes d'apprentissage et à la disponibilité variable des
soignants.

### 3.1 Formation en salle (sessions initiales)

Sessions de 4 à 8 personnes, animées par un formateur de l'équipe projet
ou un super-utilisateur déjà formé. Chaque session suit le canevas
suivant :

- **Tour de table** (15 min) — prénom, fonction, expérience
  informatique, attentes.
- **Démonstration guidée** (45 min) — le formateur parcourt le ou les
  modules concernés en expliquant chaque étape.
- **Exercices pratiques** (90 min) — chaque participant reproduit les
  gestes sur un environnement de formation isolé, avec données de démo.
- **Questions / réponses** (30 min) — clarification des points flous.
- **Évaluation rapide** (15 min) — 10 questions QCM pour mesurer la
  compréhension globale.

### 3.2 Cas pratiques et parcours de recette

Pour chaque rôle, un parcours de recette est défini dans
[`parcours-recette-par-role.md`](parcours-recette-par-role.md). Il liste
les 5 à 10 actions critiques que l'utilisateur doit savoir réaliser
sans assistance. Le formateur valide chaque action pendant la session,
et signe une fiche de validation conservée par la direction.

### 3.3 Fiches rapides par rôle

Des fiches A4 recto-verso, une par rôle, sont imprimées et distribuées
à chaque utilisateur. Elles résument les 10 actions les plus courantes,
avec capture d'écran et raccourcis clavier. Les fiches sont aussi
disponibles dans `docs/formation/fiches-rapides/` :

- [`fiche-admission.md`](fiches-rapides/fiche-admission.md)
- [`fiche-medecin.md`](fiches-rapides/fiche-medecin.md)
- [`fiche-infirmier.md`](fiches-rapides/fiche-infirmier.md)
- [`fiche-sage-femme.md`](fiches-rapides/fiche-sage-femme.md)
- [`fiche-pharmacien.md`](fiches-rapides/fiche-pharmacien.md)
- [`fiche-laboratoire.md`](fiches-rapides/fiche-laboratoire.md)
- [`fiche-radiologie.md`](fiches-rapides/fiche-radiologie.md)
- [`fiche-caissier.md`](fiches-rapides/fiche-caissier.md)
- [`fiche-direction.md`](fiches-rapides/fiche-direction.md)
- [`fiche-administrateur.md`](fiches-rapides/fiche-administrateur.md)

### 3.4 Assistance au démarrage (hotline + sur site)

Pendant les deux premières semaines d'exploitation réelle :

- **Sur site** : un formateur est présent physiquement à l'accueil des
  urgences, à la pharmacie centrale et au laboratoire aux heures de
  pointe (8h-12h, lundi au vendredi).
- **Hotline niveau 1** : numéro direct local (sans frais) pour signaler
  un blocage. Réponse sous 15 min, 8h-20h.
- **Hotline niveau 2** : pour les problèmes applicatifs non résolus au
  niveau 1, escalade à l'équipe projet (Conakry). Réponse sous 2h.
- **Hotline niveau 3** : pour les incidents techniques (serveur, base de
  données, réseau), escalade à l'administrateur système. Réponse sous 4h.

### 3.5 Support continu

Au-delà des deux premières semaines :

- **Permanence hebdomadaire** : un formateur passe une demi-journée par
  semaine dans chaque service pilote pendant les deux premiers mois.
- **Boîte aux letches** : un formulaire de feedback est intégré à
  l'application (menu **Aide → Envoyer un retour**). Chaque retour est
  trié et traité par l'équipe projet (voir section 6 ci-dessous).
- **Session de rattrapage** : une session mensuelle est ouverte aux
  nouveaux arrivants et aux utilisateurs en difficulté, sans inscription
  préalable.

---

## 4. Calendrier de montée en compétence

Le pilote est découpé en quatre phases sur trois mois :

| Phase | Semaine | Objectif | Activités |
|-------|---------|----------|-----------|
| **Pré-pilote** | S-2 à S-1 | Préparer | Formation des super-utilisateurs, validation des fiches, vérification de l'infrastructure, dry-run complet |
| **Démarrage** | S1 à S2 | Stabiliser | Assistance sur site intensive, hotline niveau 1-2 active, relevé quotidien des incidents, points de synchronisation 8h et 17h |
| **Consolidation** | S3 à S6 | Étendre | Baisse progressive de l'assistance sur site, montée en charge des modules secondaires (imagerie, bloc opératoire), première session de rattrapage |
| **Autonomie** | S7 à S12 | Pérenniser | Fin de l'assistance sur site, hotline niveau 2-3 uniquement, revue mensuelle des indicateurs d'adoption, plan de formation continue |

À la fin de la phase d'autonomie (S12), un bilan quantitatif et
qualitatif est présenté à la direction médicale et au Ministère de la
Santé pour décider de l'extension à d'autres établissements (CHU Ignace
Deen, hôpitaux régionaux).

---

## 5. Gestion de la résistance au changement

Le passage du papier au numérique rencontre inévitablement des freins
qu'il faut savoir désamorcer. Les freins les plus fréquents observés
lors de déploiements comparables en Afrique de l'Ouest sont les
suivants :

### 5.1 Freins culturels

- **« L'ordinateur, ce n'est pas pour moi »** — particulièrement
  fréquent chez les agents administratifs plus âgés. Réponse : toujours
  commencer par des gestes simples (recherche patient, consultation
  d'un résultat), valoriser chaque petit succès, ne jamais utiliser le
  clavier à la place de l'utilisateur pendant une session.
- **« Le papier, c'est plus rapide »** — vrai pour une opération
  isolée, faux sur une journée complète. Réponse : chronométrer les
  deux méthodes sur un parcours réel (ex : admission complète +
  recherche du dossier 1 h plus tard) et montrer l'écart.
- **« Si le système plante, on est bloqués »** — légitime, surtout en
  contexte de coupure électrique. Réponse : expliquer la stratégie de
  continuité (backup quotidien, onduleurs sur les postes critiques,
  procédure papier de secours pour les urgences vitales).

### 5.2 Freins organisationnels

- **Surcharge de travail ponctuelle** — pendant les premières semaines,
  la double saisie (papier + numérique) est inévitable le temps que tout
  le monde soit à l'aise. Réponse : alléger les autres tâches
  administratives pendant la période, valoriser l'effort, accepter un
  délai de tolérance.
- **Peur de la traçabilité** — certains soignants craignent que chaque
  action enregistrée puisse être utilisée contre eux. Réponse : rappeler
  que le journal d'audit sert d'abord à la qualité des soins et à la
  protection médico-légale du soignant (preuve de ce qui a été fait et
  quand), pas à la surveillance individuelle.
- **Hiérarchie et perte de pouvoir** — un chef de service peut voir
  d'un mauvais œil que ses juniors maîtrisent l'outil avant lui.
  Réponse : proposer une session de formation dédiée aux cadres avant
  les sessions collectives, pour qu'ils restent référents de leur
  service.

### 5.3 Freins techniques

- **Coupures électriques fréquentes** — réponse : onduleurs sur postes
  critiques, generateur de secours pour la salle serveur, sauvegarde
  automatique toutes les 5 minutes en cas de session interrompue.
- **Bande passante limitée** — réponse : application responsive et
  légère (~250 KB bundle initial), cache navigateur agressif, mode
  dégradé possible sur connexion 3G.
- **Pannes de poste** — réponse : au moins un poste de secours par
  service, procédure de bascule documentée dans le runbook.

---

## 6. Boucle de feedback (v1.1.0)

La version v1.1.0 introduit un canal de feedback intégré à
l'application : tout utilisateur authentifié peut soumettre un retour
(bug, suggestion, question, praise) via le menu **Aide → Envoyer un
retour** ou directement depuis l'icône feedback présente sur chaque
page. Ces retours alimentent une boucle structurée :

1. **Soumission** — l'utilisateur remplit un court formulaire (catégorie
   obligatoire, message obligatoire, sujet et URL optionnels).
   L'`user_agent` et la date sont capturés automatiquement.
2. **Tri** — chaque jour ouvré, l'équipe projet consulte
   `GET /api/v1/feedback` (filtrable par `category`, `status`,
   `facility_id`) et qualifie chaque entrée : bug confirmé, demande
   légitime, doublon, hors périmètre.
3. **Traitement** — les bugs confirmés entrent dans le backlog de
   développement avec une priorité (low/normal/high/urgent). Les
   suggestions sont examinées en revue de produit hebdomadaire.
4. **Clôture** — chaque entrée est clôturée avec un message de réponse
   (`admin_response`) visible par l'utilisateur. Les entrées résolues
   sont conservées pour analyse ultérieure.
5. **Reporting mensuel** — un tableau de bord agrège les indicateurs
   clés : nombre de retours par catégorie, délai moyen de résolution,
   taux de satisfaction (positive vs bug).

Cette boucle est essentielle pour trois raisons : (1) elle donne une
voix aux utilisateurs, ce qui réduit la frustration ; (2) elle capte
des bugs que les tests n'ont pas détectés ; (3) elle produit des
données objectives pour piloter l'évolution du produit post-pilote
(voir [`EVOLUTIONS_POST_PILOTE.md`](../post-pilot/EVOLUTIONS_POST_PILOTE.md)).

---

## 7. Métriques d'adoption

Cinq indicateurs sont suivis hebdomadairement pendant tout le pilote :

| Indicateur | Cible S4 | Cible S12 | Source |
|------------|----------|-----------|--------|
| Utilisateurs actifs / semaine | 60 % | 90 % | Audit log (login distincts) |
| Patients créés / jour | 50 | 150 | `patients.created_at` |
| Admissions saisies / jour | 20 | 60 | `admissions.created_at` |
| Feedbacks soumis / semaine | 10 | 5 | `user_feedback` |
| Taux de résolution feedback < 7 j | 50 % | 80 % | `user_feedback.resolved_at` |

Les chiffres sont extraits chaque lundi matin par l'administrateur et
envoyés à la direction médicale et à l'équipe projet. Un dashboard de
pilotage est en cours de développement (prévu v1.2).

---

## 8. Rôles et responsabilités

| Rôle | Qui | Responsabilité |
|------|-----|----------------|
| Sponsor projet | Direction médicale CHU Donka | Arbitrage, légitimité |
| Chef de projet | Équipe GuinéeCare | Planification, coordination |
| Formateur | Équipe GuinéeCare + super-utilisateurs | Sessions, fiches, hotline |
| Super-utilisateur | 1 par service (référent) | Relais local, dépannage N1 |
| Administrateur | Direction informatique CHU Donka | Comptes, RBAC, infrastructure |
| Utilisateur final | Agents, soignants, administratifs | Utilisation quotidienne |

---

## 9. Risques et mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Refus d'utilisation | Moyenne | Élevé | Formation, écoute, valorisation |
| Panne serveur prolongée | Faible | Critique | Backup, onduleurs, runbook |
| Fuite de données patient | Faible | Critique | RBAC, TLS, audit log |
| Surcharge helpdesk | Élevée | Moyen | Super-utilisateurs, fiches |
| Dérive fonctionnelle | Moyenne | Moyen | Boucle feedback priorisée |

---

## 10. Suite logique

Une fois le pilote stabilisé (fin S12), deux chantiers s'ouvrent en
parallèle :

- **Extension multi-sites** — déploiement sur 3 à 5 établissements
  supplémentaires (CHU Ignace Deen, hôpitaux régionaux de Kankan,
  Labé, Nzérékoré). Voir la roadmap dans
  [`docs/deploiement/deploiement-national.md`](../deploiement/deploiement-national.md).
- **Évolutions post-pilote** — les retours utilisateurs collectés via
  la boucle feedback de v1.1 alimentent le backlog v1.2+. Voir
  [`docs/post-pilot/EVOLUTIONS_POST_PILOTE.md`](../post-pilot/EVOLUTIONS_POST_PILOTE.md)
  pour la liste détaillée des évolutions envisagées : impression PDF
  des documents cliniques, internationalisation complète EN/FR,
  dashboard de pilotage, mode hors-ligne, application mobile, etc.

Pour la conduite du changement proprement dite, l'accent sera mis à
partir de v1.2 sur la **formation continue** des nouveaux arrivants et
sur la **montée en autonomie** des super-utilisateurs, qui deviendront
progressivement les formateurs de leur propre service.
