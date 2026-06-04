# Index documentaire — GuinéeCare Hospital Suite

## Documents principaux

- README.md
- SECURITY.md
- CHANGELOG.md
- docs/00_CAHIER_DES_CHARGES_GLOBAL.md
- docs/01_MODULES_COMPLETS_HOPITAUX.md
- docs/architecture/architecture-technique-cible.md
- docs/deploiement/deploiement-national.md
- docs/formation/conduite-du-changement.md
- docs/roadmap/roadmap-mvp.md
- docs/securite/auth-rbac.md
- docs/tests/recette-api-mvp.md

## Lots disponibles dans le dépôt

- Lot 01 — Socle technique, sécurité et référentiels
- Lot 02 — Patient, admission, rendez-vous et file d’attente
- Lot 03 — Dossier Patient Informatisé clinique
- Lot 04 — Maternité
- Lot 05 — Urgences et triage
- Lot 06 — Hospitalisation, lits et soins
- Lot 07 — Pharmacie, stock et dispensation
- Lot 08 — Laboratoire et résultats
- Lot 09 — Imagerie médicale et radiologie
- Lot 10 — Facturation, caisse et paiements
- Lot 11 — Bloc opératoire
- Lot 12 — Personnel et planning
- Lot 13 — Qualité et pilotage hospitalier
- Lot 14 — Reporting national et pilotage ministériel
- Lot 15 — Architecture, DevOps et exploitation
- Lot 16 — Roadmap, MVP, équipe projet et cahier des charges final

## Documents techniques MVP

- docs/backlog/mvp-backlog.md
- docs/backlog/sprints-mvp.md
- docs/api/api-conventions.md
- docs/data-model/mvp-data-model.md
- docs/developpement/lancement-local.md
- docs/tests/plan-tests-e2e-mvp.md
- docs/tests/parcours-utilisateurs-mvp.md
- docs/tests/recette-api-mvp.md

## État actuel

Le dépôt contient maintenant un socle backend FastAPI avec PostgreSQL, Auth JWT, RBAC, utilisateurs, établissements, services, patients, admissions, urgences, pharmacie, laboratoire et facturation MVP.

## Prochaine étape recommandée

Ajouter Alembic, renforcer les tests d'intégration et démarrer le frontend React avec login, dashboard et pages MVP.
