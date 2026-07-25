"""Celery app — v2.9.2

Tâches asynchrones planifiées pour GuinéeCare :
- prune_audit_logs : purge des audit_logs > 365 jours (RGPD Art. 25)
- backup_database : dump PostgreSQL automatique (rotation 30 jours)
- retry_sms_pending : retry des SMS en échec (v1.4.0 SMS service)
- push_dhis2_monthly : push automatique du dataset DHIS2 mensuel

Configuration via env vars :
- CELERY_BROKER_URL (défaut: REDIS_URL ou memory://)
- CELERY_RESULT_BACKEND (défaut: REDIS_URL ou memory://)
- AUDIT_LOG_RETENTION_DAYS (défaut: 365)
- BACKUP_RETENTION_DAYS (défaut: 30)

En dev/test : broker en mémoire (sans Redis), tâches exécutées en synchrone
via `celery_app.conf.task_always_eager = True` ou appelables directement
via leur fonction (voir `tasks.run_prune_audit_logs()` etc.).

Worker en production :
    celery -A app.tasks.celery_app worker --loglevel=info
    celery -A app.tasks.celery_app beat --loglevel=info

Docker : image `guineecare-worker` (voire docker-compose.prod.yml).
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger("guineecare.celery")

# --- Broker / backend ---
_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "").strip()
_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "").strip()

# Fallback sur REDIS_URL si pas de broker explicite
if not _BROKER_URL:
    _BROKER_URL = os.environ.get("REDIS_URL", "").strip()
if not _RESULT_BACKEND:
    _RESULT_BACKEND = os.environ.get("REDIS_URL", "").strip()

# En l'absence totale de Redis, on reste en mémoire (dev/test)
if not _BROKER_URL:
    _BROKER_URL = "memory://"
if not _RESULT_BACKEND:
    _RESULT_BACKEND = "cache+memory://"

try:
    from celery import Celery  # type: ignore

    _CELERY_AVAILABLE = True
except ImportError:
    _CELERY_AVAILABLE = False
    logger.info(
        "Celery non installé — les tâches seront exécutables en synchrone "
        "uniquement. Pour activer le worker: pip install celery[redis]>=5.3"
    )


if _CELERY_AVAILABLE:
    celery_app = Celery(
        "guineecare",
        broker=_BROKER_URL,
        backend=_RESULT_BACKEND,
        include=[
            "app.tasks.maintenance_tasks",
            "app.tasks.reporting_tasks",
        ],
    )

    celery_app.conf.update(
        # Sérialisation JSON (sécurité — pas de pickle)
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        # Concurrency : 1 worker synchrone suffit pour le pilote
        # (évite la concurrence sur les write DB)
        worker_concurrency=int(os.environ.get("CELERY_CONCURRENCY", "1")),
        # Retry policy par défaut
        task_default_retry_delay=60,
        task_default_max_retries=3,
        # Ne pas beat par défaut — activé uniquement via `celery beat`
        beat_schedule={
            # 1. Pruning audit log — quotidien à 03h00 UTC
            "prune-audit-logs-daily": {
                "task": "app.tasks.maintenance_tasks.prune_audit_logs",
                "schedule": "0 3 * * *",
            },
            # 2. Backup database — quotidien à 04h00 UTC
            "backup-database-daily": {
                "task": "app.tasks.maintenance_tasks.backup_database",
                "schedule": "0 4 * * *",
            },
            # 3. Retry SMS pending — toutes les 5 minutes
            "retry-sms-pending-5min": {
                "task": "app.tasks.maintenance_tasks.retry_sms_pending",
                "schedule": "*/5 * * * *",
            },
            # 4. DHIS2 monthly push — le 5 du mois à 06h00 UTC
            "push-dhis2-monthly": {
                "task": "app.tasks.reporting_tasks.push_dhis2_monthly",
                "schedule": "0 6 5 * *",
            },
        },
    )

    # En dev/test, exécution synchrone (pas de worker requis)
    if os.environ.get("ENVIRONMENT", "local") in ("local", "test", "dev"):
        celery_app.conf.task_always_eager = True
        celery_app.conf.task_eager_propagates = True

else:
    # Stub minimal quand Celery n'est pas installé — permet aux tests de
    # fonctionner et au code d'appeler les tâches en synchrone.
    celery_app = None  # type: ignore[assignment]


def submit_task(task_path: str, *args, **kwargs):
    """Soumet une tâche Celery (ou l'exécute synchrone si Celery absent).

    Utilisé par le code applicatif pour découpler l'appel au worker :
        from app.tasks.celery_app import submit_task
        submit_task("app.tasks.maintenance_tasks.prune_audit_logs")
    """
    if celery_app is None:
        # Pas de Celery → import et exécution synchrone directe
        import importlib
        module_path, func_name = task_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        return func(*args, **kwargs)
    return celery_app.send_task(task_path, args=args, kwargs=kwargs)
