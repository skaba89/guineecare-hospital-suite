# Dossier de présentation institutionnelle — GuinéeCare Hospital Suite

## 1. Résumé exécutif

GuinéeCare Hospital Suite est une plateforme numérique hospitalière moderne destinée à renforcer la gestion des établissements de santé en Guinée.

L’objectif est de fournir une solution nationale, progressive et souveraine permettant de digitaliser les principaux processus hospitaliers : accueil patient, admissions, urgences, maternité, pharmacie, laboratoire, facturation, suivi d’activité, audit et pilotage.

La plateforme est pensée pour répondre aux besoins des hôpitaux publics, cliniques privées, centres de santé, maternités, directions régionales de santé et institutions nationales.

## 2. Problèmes adressés

Le système hospitalier fait face à plusieurs difficultés opérationnelles :

- dossiers patients dispersés ou papier ;
- suivi limité des admissions et sorties ;
- traçabilité insuffisante des actes ;
- faible visibilité sur les stocks pharmacie ;
- processus laboratoire non unifiés ;
- facturation manuelle ou peu contrôlée ;
- manque de tableaux de bord consolidés ;
- difficulté de pilotage au niveau établissement, régional et national.

## 3. Proposition de valeur

GuinéeCare propose une plateforme intégrée qui permet de :

- centraliser les données patients ;
- fluidifier les admissions et les urgences ;
- suivre les stocks et mouvements pharmacie ;
- gérer les examens de laboratoire ;
- améliorer la facturation et la transparence financière ;
- tracer les actions sensibles ;
- fournir des tableaux de bord pour les directions ;
- préparer une interconnexion avec les systèmes nationaux de santé.

## 4. Modules disponibles dans le socle actuel

### Authentification et sécurité

- Connexion utilisateur.
- Jetons JWT.
- Rôles et permissions.
- Accès protégé aux routes sensibles.

### Gestion des établissements

- Création et consultation des établissements.
- Organisation par services.
- Base pour une architecture multi-établissements.

### Patients

- Création patient.
- Numéro patient.
- Consultation des dossiers simples.

### Admissions

- Création admission.
- Affectation service.
- Clôture admission.

### Urgences

- Création passage urgence.
- Priorité.
- Orientation.

### Pharmacie

- Référentiel produits.
- Stock disponible.
- Entrées et sorties de stock.

### Laboratoire

- Référentiel examens.
- Demandes laboratoire.
- Saisie résultats.
- Validation résultats.

### Facturation

- Tarifs.
- Factures.
- Paiements.
- Reçus.

### Audit et activité

- Journalisation des actions métier.
- Traçabilité progressive des opérations sensibles.

## 5. Vision cible SaaS entreprise

La plateforme doit évoluer vers un SaaS entreprise hospitalier avec :

- multi-tenant ;
- multi-établissements ;
- séparation des données par organisation ;
- portail d’administration ;
- gouvernance des accès ;
- audit complet ;
- reporting national ;
- déploiement cloud ou souverain ;
- intégration future avec DHIS2, SNIS, mobile money, assurance santé et identifiant patient national.

## 6. Bénéfices pour l’État

Pour le ministère et les institutions publiques, la plateforme permet :

- une meilleure visibilité sur l’activité hospitalière ;
- un suivi des flux patients ;
- une meilleure maîtrise des recettes et paiements ;
- une traçabilité renforcée ;
- une amélioration de la qualité des soins ;
- une réduction des pertes liées aux stocks ;
- une base de pilotage pour les politiques publiques de santé.

## 7. Bénéfices pour les hôpitaux

Pour les établissements de santé, la plateforme apporte :

- gain de temps administratif ;
- meilleure coordination entre services ;
- suivi simplifié des patients ;
- réduction des erreurs ;
- contrôle des stocks ;
- meilleure organisation de la facturation ;
- accès à des indicateurs opérationnels.

## 8. Architecture technique

Le socle technique repose sur :

- Backend FastAPI ;
- Frontend React TypeScript ;
- Base PostgreSQL ;
- Docker Compose pour la démo ;
- Alembic pour les migrations ;
- JWT pour l’authentification ;
- RBAC pour les droits ;
- API REST versionnée `/api/v1`.

## 9. Sécurité et conformité

La plateforme est conçue autour des principes suivants :

- accès par rôle ;
- séparation des permissions ;
- audit des actions sensibles ;
- préparation multi-tenant ;
- préparation Row-Level Security PostgreSQL ;
- journalisation technique et métier ;
- déploiement possible dans une infrastructure souveraine.

## 10. Déploiement progressif proposé

### Phase 1 — Démonstration pilote

- Déploiement local ou serveur de démonstration.
- Présentation des modules principaux.
- Validation fonctionnelle avec un établissement pilote.

### Phase 2 — Pilote hospitalier

- Déploiement dans un hôpital de référence.
- Formation des utilisateurs.
- Ajustement des workflows réels.
- Collecte des retours terrain.

### Phase 3 — Extension régionale

- Déploiement dans plusieurs établissements.
- Consolidation des indicateurs.
- Gouvernance régionale.

### Phase 4 — Plateforme nationale

- Reporting national.
- Interconnexion avec les systèmes publics.
- Déploiement multi-régions.
- Pilotage centralisé.

## 11. Démonstration recommandée

Le scénario de démonstration doit montrer :

1. connexion administrateur ;
2. consultation du dashboard ;
3. création d’un patient ;
4. admission du patient ;
5. passage aux urgences ;
6. mouvement de stock pharmacie ;
7. demande laboratoire ;
8. création facture ;
9. paiement ;
10. consultation de l’audit.

## 12. Message institutionnel

GuinéeCare Hospital Suite n’est pas seulement un logiciel hospitalier. C’est une base de modernisation du système de santé, capable de soutenir la transformation numérique des hôpitaux et de fournir à l’État une meilleure capacité de pilotage, de transparence et de planification.
