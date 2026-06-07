# Architecture SaaS entreprise — GuinéeCare Hospital Suite

## Objectif

Faire évoluer GuinéeCare Hospital Suite vers une plateforme SaaS entreprise moderne pour hôpitaux, cliniques, groupes hospitaliers et déploiements nationaux.

## Capacités cibles

- Multi-tenant par établissement, organisation ou groupe hospitalier.
- Authentification JWT avec évolution possible vers SSO/OIDC.
- RBAC avec permissions fines par module.
- Audit logs sur toutes les actions sensibles.
- API versionnée `/api/v1`.
- Frontend React moderne avec layout, router, pages métier et composants réutilisables.
- Observabilité : logs, métriques, traces, alertes.
- CI/CD backend et frontend.
- Déploiement Docker local puis Kubernetes/cloud.
- Base PostgreSQL avec migrations Alembic.
- Préparation HL7/FHIR, DHIS2, paiements mobiles et assurance santé.

## Architecture cible

```text
Frontend React/Vite
        |
API Gateway / Reverse Proxy
        |
Backend FastAPI modulaire
        |
PostgreSQL + object storage + queue + monitoring
```

## Modules SaaS à ajouter

### Organisation et multi-tenant

- Organisations.
- Établissements.
- Utilisateurs par organisation.
- Rôles par organisation.
- Isolation des données par tenant.

### Administration SaaS

- Gestion des abonnements.
- Limites d’usage.
- Facturation SaaS.
- Paramètres organisation.
- Journal d’activité.

### Sécurité entreprise

- Audit logs complets.
- Politique mot de passe.
- Sessions actives.
- Verrouillage compte.
- Permissions fines.
- Préparation SSO.

### Exploitation

- Healthchecks.
- Backups.
- Restauration.
- Monitoring.
- Alertes.
- Runbooks.

## Roadmap SaaS recommandée

1. Stabilisation Docker et login local.
2. Audit logs API et page frontend.
3. React Router et layout enterprise.
4. Multi-tenancy logique avec organisation_id.
5. Paramètres organisation.
6. Monitoring et logs structurés.
7. Environnement staging.
8. Déploiement Kubernetes.
9. Facturation SaaS et plans.
10. Intégrations nationales et interopérabilité.
