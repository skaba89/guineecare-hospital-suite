# Architecture SaaS entreprise — GuinéeCare Hospital Suite

## Vision

GuinéeCare Hospital Suite évolue d’un MVP hospitalier vers une plateforme SaaS entreprise pour hôpitaux, cliniques, maternités, groupes hospitaliers et institutions publiques de santé.

## Capacités cibles

- Multi-tenant par organisation, groupe hospitalier et établissement.
- Authentification JWT avec évolution future vers SSO/OIDC.
- RBAC avec permissions fines par module.
- Audit logs sur toutes les actions sensibles.
- API versionnée `/api/v1`.
- Frontend React moderne avec layout, router, pages métier et composants réutilisables.
- Observabilité : logs, métriques, traces, alertes.
- CI/CD backend et frontend.
- Déploiement Docker local, puis Kubernetes/cloud/souverain.
- PostgreSQL avec migrations Alembic strictes.
- Préparation HL7/FHIR, DHIS2/SNIS, mobile money et assurance santé.

## Niveaux SaaS

### Tenant

Client SaaS ou organisation de santé : ministère, groupe hospitalier, réseau de cliniques, ONG, partenaire institutionnel.

### Groupe

Réseau d’établissements rattachés à une même entité.

### Établissement

CHU, hôpital régional, hôpital préfectoral, clinique, centre de santé ou maternité.

### Service

Unité médicale, administrative ou technique.

## Sécurité entreprise

- Isolation logique par tenant.
- Permissions par rôle et par module.
- Audit centralisé.
- Préparation Row-Level Security PostgreSQL.
- Expiration des tokens.
- Rotation future des secrets.
- Politique de session.
- Journalisation des accès sensibles.

## Modules actuels

- Authentification.
- Utilisateurs.
- RBAC.
- Établissements.
- Services.
- Patients.
- Admissions.
- Urgences.
- Pharmacie.
- Laboratoire.
- Facturation.
- Activité / audit.

## Modules entreprise à ajouter

- Rendez-vous.
- Hospitalisation avancée.
- Maternité avancée.
- Imagerie.
- Bloc opératoire.
- Portail patient.
- Portail ministère.
- Reporting national.
- Gestion assurance.
- Mobile money.
- Notifications.
- Paramétrage tenant.

## Roadmap technique

### Phase 1 — Stabilisation démo

- Login local stable.
- Docker Compose stable.
- Seed idempotent.
- Scripts `start-demo` et `reset-demo`.
- Healthchecks backend, frontend et base.

### Phase 2 — SaaS frontend

- React Router complet.
- Layout entreprise.
- Sidebar, header, breadcrumbs.
- Pages métier séparées.
- Page audit.
- UX responsive.

### Phase 3 — Audit métier

- Patient créé.
- Admission créée/clôturée.
- Urgence créée/triée/orientée.
- Produit créé.
- Mouvement de stock.
- Demande laboratoire.
- Résultat laboratoire.
- Validation résultat.
- Facture créée.
- Paiement enregistré.
- Utilisateur créé.
- Rôle/permission modifiés.

### Phase 4 — Multi-tenant

- Modèle `Tenant`.
- Liaison tenant → établissements.
- Liaison utilisateur → tenant.
- Filtrage tenant dans toutes les routes.
- Préparation RLS.

### Phase 5 — Production

- Désactivation de `create_all()`.
- Migrations Alembic uniquement.
- Configuration `.env` stricte.
- Logs structurés.
- Monitoring.
- Sauvegarde/restauration.
- Kubernetes.

## Principe produit

Le produit doit rester simple pour les équipes hospitalières, mais robuste pour les directions, les DSI, les ministères et les déploiements nationaux.