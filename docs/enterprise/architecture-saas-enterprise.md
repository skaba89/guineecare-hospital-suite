# Architecture SaaS Enterprise

## Objectif

Definir l'architecture cible pour transformer le MVP en plateforme SaaS enterprise.

## Couches principales

### 1. Frontend web

- React.
- TypeScript.
- Layout enterprise.
- Router.
- Gestion session.
- Dashboard par role.
- Pages metier modulaires.

### 2. API backend

- FastAPI.
- API versionnee.
- Modules metier isoles.
- RBAC.
- Audit logs.
- Multi-tenant.
- Feature flags.

### 3. Donnees

- PostgreSQL.
- Schemas/migrations Alembic.
- Index metier.
- Sauvegardes.
- Retention.
- Archivage.

### 4. Observabilite

- Logs structures.
- Healthchecks.
- Metriques Prometheus futures.
- Dashboards Grafana futurs.
- Alertes techniques.

### 5. Integration

- API publique.
- Webhooks futurs.
- Connecteurs laboratoire.
- Connecteurs paiement.
- Connecteurs ministeriels.

## Multi-tenant cible

Mode recommande au depart : tenant_id dans les tables critiques.

Tables a etendre progressivement :

- users ;
- facilities ;
- departments ;
- patients ;
- admissions ;
- emergency_visits ;
- pharmacy_products ;
- pharmacy_stock ;
- lab_tests ;
- lab_orders ;
- invoices ;
- payments ;
- activity_entries.

## Environnements

- local : developpement.
- demo : demonstration client.
- staging : recette.
- production : clients reels.

## Strategie de croissance

### Phase 1

Stabiliser le monolithe modulaire.

### Phase 2

Ajouter multi-tenant, audit et plans.

### Phase 3

Ajouter observabilite, integrations et automatisations.

### Phase 4

Decoupler certains modules si necessaire : reporting, notifications, fichiers, interoperabilite.