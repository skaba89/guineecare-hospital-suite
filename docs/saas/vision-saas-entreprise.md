# Vision SaaS entreprise — GuinéeCare Hospital Suite

## Objectif

Faire évoluer GuinéeCare Hospital Suite d'un MVP hospitalier vers une plateforme SaaS entreprise moderne, multi-établissements, sécurisée, auditable, extensible et prête pour un déploiement national ou privé.

## Principes directeurs

- Architecture modulaire par domaine métier.
- Multi-tenant par établissement, groupe hospitalier ou organisation.
- Sécurité forte avec JWT, RBAC, permissions fines et audit complet.
- Expérience utilisateur moderne, rapide et responsive.
- API versionnée et documentée.
- Déploiement Docker local, puis Kubernetes/cloud.
- Observabilité avec logs, métriques, traces et alertes.
- Migrations de base versionnées avec Alembic.
- CI/CD backend et frontend.
- Préparation future aux intégrations nationales : DHIS2, HL7/FHIR, assurance, paiement mobile.

## Cibles SaaS

### Établissement unique

Déploiement pour un hôpital, une clinique ou un centre médical.

### Groupe hospitalier

Plusieurs établissements sous une même organisation avec consolidation financière, administrative et clinique.

### Plateforme nationale

Déploiement progressif régional puis national avec reporting ministériel et gouvernance centralisée.

## Modules entreprise prioritaires

- Organisations et tenants.
- Établissements et services.
- Utilisateurs, rôles, permissions.
- Patients et identités.
- Admission, urgences, hospitalisation.
- Pharmacie et stocks.
- Laboratoire.
- Facturation et paiements.
- Audit logs.
- Notifications.
- Reporting et dashboards.
- Paramétrage avancé.
- Connecteurs externes.

## Exigences non fonctionnelles

- Haute disponibilité progressive.
- Sauvegarde et restauration documentées.
- Journalisation des actions sensibles.
- Chiffrement des secrets.
- Séparation des environnements.
- Tests automatisés.
- Traçabilité des migrations.
- Performance mesurable.
- UX responsive.

## Roadmap courte

1. Corriger et stabiliser le login local.
2. Stabiliser Docker local et scripts de démo.
3. Ajouter React Router.
4. Ajouter une page Audit.
5. Brancher les audit logs sur les actions métier.
6. Ajouter un vrai module organisation/tenant.
7. Renforcer Alembic et supprimer progressivement `create_all()` en préproduction.
8. Ajouter observabilité et monitoring.
9. Préparer une démo entreprise propre.
