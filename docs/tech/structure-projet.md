# Structure projet recommandée

## Objectif

Définir une organisation claire du code pour passer de la documentation à une vraie application maintenable.

## Monorepo cible

Racine du projet :

- backend : API, règles métier, base de données, sécurité.
- frontend : interface web pour les utilisateurs hospitaliers.
- infrastructure : Docker, Kubernetes, reverse proxy, monitoring.
- docs : documentation fonctionnelle, technique et projet.
- scripts : installation, sauvegarde, restauration, déploiement.

## Backend recommandé

Le backend doit être modulaire, avec un module par domaine métier :

- auth
- facilities
- users
- patients
- admissions
- clinical
- emergency
- hospitalization
- pharmacy
- laboratory
- billing
- reporting

Chaque module doit contenir :

- models
- schemas
- repository
- service
- routes
- permissions
- tests

## Frontend recommandé

Le frontend doit être organisé par parcours utilisateur :

- auth
- dashboard
- patients
- admissions
- clinical
- emergency
- hospitalization
- pharmacy
- laboratory
- billing
- reporting

## Principes de qualité

- Séparer logique métier et accès base.
- Ajouter des tests par module.
- Documenter les API.
- Garder une convention de nommage stable.
- Garder les écrans simples et adaptés au terrain hospitalier.
