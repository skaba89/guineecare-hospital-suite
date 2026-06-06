# Modele de donnees SaaS Enterprise

## Objectif

Ajouter une couche SaaS au-dessus du SIH MVP sans casser les modules hospitaliers existants.

## Entites cibles

### tenants

Representent les organisations clientes.

Champs cibles :

- id
- code
- name
- tenant_type
- country
- status
- created_at

### subscription_plans

Representent les offres commerciales.

Champs cibles :

- id
- code
- name
- monthly_price
- max_facilities
- max_users
- is_active
- created_at

### tenant_subscriptions

Representent l'abonnement actif d'un tenant.

Champs cibles :

- id
- tenant_id
- plan_code
- status
- started_at
- ended_at

### feature_flags

Permettent d'activer ou desactiver des modules par tenant.

Champs cibles :

- id
- tenant_id
- feature_code
- is_enabled
- created_at

## Modules controlables par feature flag

- emergency
- maternity
- pharmacy
- laboratory
- imaging
- operating_room
- billing
- reporting
- quality
- hr
- national_dashboard
- interoperability

## Strategie d'isolation

Phase 1 : ajouter tenant_id progressivement sur les tables critiques.

Phase 2 : appliquer un filtrage applicatif obligatoire par tenant.

Phase 3 : ajouter PostgreSQL Row Level Security pour les environnements enterprise.

## Regle enterprise

Aucune donnee patient ou facture ne doit etre accessible sans contexte tenant valide.