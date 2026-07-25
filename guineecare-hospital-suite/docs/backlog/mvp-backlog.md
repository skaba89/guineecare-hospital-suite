# Backlog MVP — GuinéeCare Hospital Suite

## Objectif du backlog

Structurer les premiers développements de la plateforme autour d'un MVP exploitable dans un hôpital pilote.

## Epic 1 — Socle plateforme

### User Stories

- En tant qu'administrateur, je veux créer un établissement afin de structurer les données par hôpital.
- En tant qu'administrateur, je veux créer les services afin d'organiser les parcours patients.
- En tant qu'administrateur, je veux créer les utilisateurs afin de donner accès à la plateforme.
- En tant qu'administrateur, je veux attribuer des rôles afin de contrôler les droits.
- En tant qu'auditeur, je veux consulter les journaux d'activité afin de tracer les actions sensibles.

### Critères d'acceptation

- Création d'un établissement.
- Création des services.
- Création d'un utilisateur.
- Attribution d'un rôle.
- Vérification des permissions.
- Journalisation des actions sensibles.

## Epic 2 — Patient et admission

### User Stories

- En tant qu'agent d'accueil, je veux créer un patient afin de l'identifier dans le système.
- En tant qu'agent d'accueil, je veux rechercher un patient afin d'éviter les doublons.
- En tant qu'agent d'admission, je veux créer une admission afin de démarrer un parcours de soin.
- En tant que service, je veux voir la file d'attente afin de prendre les patients dans l'ordre.

### Critères d'acceptation

- Patient créé avec identifiant unique.
- Recherche par nom, téléphone ou numéro patient.
- Admission liée à un établissement et un service.
- File d'attente visible par service.

## Epic 3 — DPI clinique de base

### User Stories

- En tant que médecin, je veux consulter la synthèse patient afin de voir l'historique utile.
- En tant que médecin, je veux saisir une observation afin de documenter la consultation.
- En tant qu'infirmier, je veux saisir les constantes afin de suivre l'état du patient.
- En tant que médecin, je veux saisir un diagnostic afin de structurer le dossier.

### Critères d'acceptation

- Synthèse patient disponible.
- Observation créée et historisée.
- Constantes affichées dans la timeline.
- Diagnostic relié à l'admission.

## Epic 4 — Urgences

### User Stories

- En tant qu'agent d'urgence, je veux créer un passage urgence.
- En tant qu'infirmier, je veux effectuer le triage.
- En tant que médecin, je veux voir les patients prioritaires.
- En tant que médecin, je veux orienter le patient après prise en charge.

### Critères d'acceptation

- Passage urgence créé.
- Priorité affectée.
- File triée par priorité.
- Orientation finale enregistrée.

## Epic 5 — Hospitalisation

### User Stories

- En tant que médecin, je veux demander une hospitalisation.
- En tant qu'agent, je veux affecter un lit.
- En tant qu'infirmier, je veux suivre les soins du séjour.
- En tant que médecin, je veux clôturer le séjour.

### Critères d'acceptation

- Séjour ouvert.
- Lit réservé puis occupé.
- Mouvements historisés.
- Sortie enregistrée.

## Epic 6 — Pharmacie

### User Stories

- En tant que pharmacien, je veux gérer le catalogue produits.
- En tant que pharmacien, je veux suivre les stocks.
- En tant que pharmacien, je veux gérer les lots et péremptions.
- En tant que pharmacien, je veux dispenser un produit.

### Critères d'acceptation

- Produit créé.
- Entrée stock créée.
- Sortie stock tracée.
- Alerte rupture visible.

## Epic 7 — Laboratoire

### User Stories

- En tant que médecin, je veux demander un examen.
- En tant que laboratoire, je veux recevoir l'échantillon.
- En tant que technicien, je veux saisir un résultat.
- En tant que biologiste, je veux valider le résultat.

### Critères d'acceptation

- Demande créée.
- Échantillon suivi.
- Résultat saisi.
- Résultat validé visible dans le dossier patient.

## Epic 8 — Facturation

### User Stories

- En tant qu'agent facturation, je veux créer une facture.
- En tant que caissier, je veux encaisser un paiement.
- En tant que caissier, je veux imprimer un reçu.
- En tant que comptable, je veux clôturer la caisse.

### Critères d'acceptation

- Facture créée.
- Paiement enregistré.
- Reçu généré.
- Caisse clôturée.

## Epic 9 — Reporting hôpital

### User Stories

- En tant que directeur, je veux voir les indicateurs de l'hôpital.
- En tant que statisticien, je veux exporter un rapport mensuel.
- En tant que responsable, je veux contrôler les anomalies.

### Critères d'acceptation

- Dashboard hôpital disponible.
- Export rapport disponible.
- Contrôles qualité visibles.
