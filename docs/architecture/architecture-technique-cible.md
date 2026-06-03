# Architecture technique cible

## Choix recommandé MVP

Architecture modular monolith avec backend FastAPI, frontend React/TypeScript, PostgreSQL, Redis, MinIO, Docker Compose et observabilité Prometheus/Grafana/Loki.

## Cible nationale

Architecture Kubernetes, séparation progressive des services critiques, API Gateway, stockage objet S3 compatible, sauvegardes automatisées, monitoring centralisé et data warehouse santé.

## Principes

- Multi-hôpital via `facility_id`.
- RBAC et habilitations.
- Audit métier et technique.
- API versionnée `/api/v1`.
- Documentation OpenAPI.
- Jobs asynchrones pour notifications, PDF, exports et reporting.
