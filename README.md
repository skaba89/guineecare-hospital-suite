# GuinéeCare Hospital Suite

Plateforme hospitalière complète pour la Guinée, inspirée des meilleurs SIH modernes : dossier patient informatisé, maternité, urgences, hospitalisation, pharmacie, laboratoire, imagerie, facturation, bloc opératoire, RH, qualité, reporting national et architecture technique industrielle.

## Objectif

Construire une suite hospitalière modulaire, sécurisée, multi-hôpitaux et interopérable, capable de servir un hôpital pilote puis un déploiement régional et national.

## Organisation documentaire

- `docs/00_CAHIER_DES_CHARGES_GLOBAL.md`
- `docs/01_MODULES_COMPLETS_HOPITAUX.md`
- `docs/lots/lot-01-...md` à `lot-16-...md`
- `docs/architecture/architecture-technique-cible.md`
- `docs/roadmap/roadmap-mvp.md`
- `docs/budget/budget-indicatif.md`
- `docs/gouvernance/gouvernance-projet.md`
- `docs/deploiement/deploiement-national.md`
- `docs/formation/conduite-du-changement.md`

## Lots fonctionnels

- Lot 01 — Socle technique, sécurité, référentiels
- Lot 02 — Patient, admission, rendez-vous, file d’attente
- Lot 03 — DPI clinique
- Lot 04 — Maternité, grossesse, accouchement, néonatalogie
- Lot 05 — Urgences, triage et prise en charge immédiate
- Lot 06 — Hospitalisation, lits, soins et prescriptions
- Lot 07 — Pharmacie, stock, médicaments et dispensation
- Lot 08 — Laboratoire, prélèvements, analyses et résultats
- Lot 09 — Imagerie médicale, radiologie et comptes rendus
- Lot 10 — Facturation hospitalière, caisse, paiements et prise en charge
- Lot 11 — Bloc opératoire, anesthésie, chirurgie et stérilisation
- Lot 12 — Ressources humaines hospitalières, plannings, gardes et habilitations
- Lot 13 — Qualité, risques, événements indésirables et pilotage hospitalier
- Lot 14 — Reporting national, statistiques sanitaires, interopérabilité et pilotage ministériel
- Lot 15 — Architecture technique cible, DevOps, sécurité, déploiement national et exploitation
- Lot 16 — Roadmap de réalisation, MVP, budget indicatif, équipe projet et cahier des charges final

## Stack cible recommandée

- Backend : FastAPI, Python, SQLAlchemy, Alembic
- Frontend : React / TypeScript / Vite ou Next.js
- Base : PostgreSQL
- Cache / jobs : Redis + Celery ou Dramatiq
- Stockage documents : MinIO / S3 compatible
- Observabilité : Prometheus, Grafana, Loki
- Déploiement : Docker Compose pour pilote, Kubernetes pour national
- Interopérabilité : API REST, préparation HL7/FHIR/DHIS2

## Statut

Version documentaire initiale : 2026-06-02
