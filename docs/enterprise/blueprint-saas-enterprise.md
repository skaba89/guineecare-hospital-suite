# Blueprint SaaS Enterprise

## Objectif

Faire evoluer GuineeCare d'un SIH MVP vers une plateforme SaaS hospitaliere enterprise-ready.

## Capacites SaaS cibles

### Multi-tenant

- Organisation cliente.
- Groupe hospitalier.
- Etablissement.
- Service.
- Utilisateur.
- Role.
- Permission.
- Donnees isolees par tenant.

### Plans commerciaux

- Starter.
- Professional.
- Enterprise.
- National.

Chaque plan controle :

- nombre d'etablissements ;
- nombre d'utilisateurs ;
- modules actifs ;
- stockage documentaire ;
- support ;
- reporting avance ;
- interopérabilite ;
- SLA.

### Feature flags

Les modules doivent pouvoir etre actives ou desactives par organisation :

- patients ;
- admissions ;
- urgences ;
- maternite ;
- pharmacie ;
- laboratoire ;
- imagerie ;
- facturation ;
- reporting ;
- audit ;
- API publique ;
- IA.

### Securite enterprise

- JWT + refresh token.
- RBAC avance.
- ABAC futur.
- MFA futur.
- Journalisation des actions sensibles.
- Politique de mot de passe.
- Blocage compte apres tentatives.
- Sessions actives.
- Chiffrement TLS.
- Secrets manager.

### Observabilite

- Logs applicatifs.
- Logs de securite.
- Metriques techniques.
- Metriques metier.
- Healthchecks.
- Monitoring Prometheus.
- Dashboards Grafana.
- Alerting.

### Donnees et gouvernance

- Audit complet.
- Historique des actions.
- Retention des donnees.
- Sauvegarde.
- Restauration.
- Export controle.
- Traçabilite.
- Qualite des donnees.

### API et integrations

- API REST versionnee.
- Documentation OpenAPI.
- Webhooks.
- Connecteurs futurs : assurance, ministere, laboratoire externe, pharmacie centrale, mobile money.

## Architecture cible

```text
Frontend Web / Mobile
        |
API Gateway / Reverse Proxy
        |
Backend FastAPI modulaire
        |
PostgreSQL multi-tenant
        |
Object Storage documents
        |
Observabilite + Audit + Monitoring
```

## Roadmap enterprise

1. Stabilisation MVP local.
2. Multi-tenant applicatif.
3. Abonnements et plans.
4. Feature flags.
5. Audit logs generalises.
6. Observabilite.
7. CI/CD enterprise.
8. Deploiement cloud.
9. Haute disponibilite.
10. Version nationale.
