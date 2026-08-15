"""Routes d'administration des tâches Celery — v2.9.2

Permet à un SUPER_ADMIN de :
- lister les tâches planifiées
- déclencher manuellement une tâche (prune audit, backup, retry SMS, push DHIS2)
- consulter le statut du worker (broker, last execution)

Ces routes sont SUPER_ADMIN uniquement (pas de permission RBAC dédiée —
tâches sensibles de maintenance système).
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.rbac.dependencies import require_role
from app.modules.users.models import User

logger = logging.getLogger("guineecare.tasks.routes")

router = APIRouter(prefix="/tasks", tags=["tasks"])


AVAILABLE_TASKS = {
    "prune_audit_logs": "app.tasks.maintenance_tasks.prune_audit_logs",
    "backup_database": "app.tasks.maintenance_tasks.backup_database",
    "retry_sms_pending": "app.tasks.maintenance_tasks.retry_sms_pending",
    "push_dhis2_monthly": "app.tasks.reporting_tasks.push_dhis2_monthly",
    "send_quality_alerts_digest": "app.tasks.reporting_tasks.send_quality_alerts_digest",
}

# Une purge manuelle est une action destructive. On impose une fenêtre
# explicite et conservatrice afin qu'une valeur absente/négative ne puisse
# jamais devenir silencieusement une purge large.
MIN_MANUAL_AUDIT_RETENTION_DAYS = 30
MAX_MANUAL_AUDIT_RETENTION_DAYS = 3650


def _task_kwargs(task_name: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Valide les arguments d'un déclenchement manuel avant exécution."""
    kwargs: dict[str, Any] = {}

    if task_name == "prune_audit_logs":
        if "retention_days" not in payload:
            raise HTTPException(
                status_code=422,
                detail="retention_days est obligatoire pour une purge manuelle des audit logs",
            )

        raw_retention = payload["retention_days"]
        if isinstance(raw_retention, bool):
            raise HTTPException(status_code=422, detail="retention_days doit être un entier")
        try:
            retention_days = int(raw_retention)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="retention_days doit être un entier") from None

        if not MIN_MANUAL_AUDIT_RETENTION_DAYS <= retention_days <= MAX_MANUAL_AUDIT_RETENTION_DAYS:
            raise HTTPException(
                status_code=422,
                detail=(
                    "retention_days doit être compris entre "
                    f"{MIN_MANUAL_AUDIT_RETENTION_DAYS} et {MAX_MANUAL_AUDIT_RETENTION_DAYS} jours"
                ),
            )
        kwargs["retention_days"] = retention_days

    elif task_name == "retry_sms_pending" and "max_age_hours" in payload:
        try:
            kwargs["max_age_hours"] = int(payload["max_age_hours"])
        except (ValueError, TypeError):
            pass
    elif task_name == "push_dhis2_monthly" and "period" in payload:
        if isinstance(payload["period"], str) and payload["period"]:
            kwargs["period"] = payload["period"]

    return kwargs


@router.get("")
def list_tasks(
    current_user: User = Depends(require_role("SUPER_ADMIN")),
) -> dict[str, Any]:
    """Liste les tâches planifiées disponibles et leur statut.

    SUPER_ADMIN uniquement.
    """
    from app.tasks.celery_app import celery_app

    return {
        "tasks": [
            {
                "name": name,
                "path": path,
                "async_enabled": celery_app is not None,
            }
            for name, path in AVAILABLE_TASKS.items()
        ],
        "celery_available": celery_app is not None,
        "broker_url_configured": bool(__import__("os").environ.get("CELERY_BROKER_URL") or __import__("os").environ.get("REDIS_URL")),
    }


@router.post("/trigger/{task_name}")
def trigger_task(
    task_name: str,
    payload: dict | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN")),
) -> dict[str, Any]:
    """Déclenche une tâche manuellement.

    Args (body JSON, optionnel) :
        - retention_days (pour prune_audit_logs)
        - max_age_hours (pour retry_sms_pending)
        - period (pour push_dhis2_monthly, format YYYYMM)

    Returns:
        {"task": name, "status": "submitted"|"sync_executed", "result": ...}
    """
    if task_name not in AVAILABLE_TASKS:
        raise HTTPException(
            status_code=404,
            detail=f"Tâche inconnue: {task_name}. Disponibles: {list(AVAILABLE_TASKS.keys())}",
        )

    task_path = AVAILABLE_TASKS[task_name]
    payload = payload or {}
    kwargs = _task_kwargs(task_name, payload)

    # Log de l'action (audit) uniquement après validation complète du payload.
    # Une requête refusée ne doit jamais être enregistrée comme tâche déclenchée.
    try:
        from app.modules.audit.service import audit_log
        audit_log(
            db=db,
            action="system.task_trigger",
            resource_type="task",
            resource_id=task_name,
            user=current_user,
            status_code=200,
            payload={"task": task_name, "args": payload},
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Audit log task trigger échoué: %s", exc)

    # Exécution (synchrone si Celery absent, async sinon)
    from app.tasks.celery_app import submit_task, celery_app

    try:
        result = submit_task(task_path, **kwargs)
        return {
            "task": task_name,
            "status": "sync_executed" if celery_app is None else "submitted",
            "result": result,
        }
    except Exception as exc:
        logger.error("Trigger task %s échec: %s", task_name, exc)
        raise HTTPException(status_code=500, detail=f"Erreur exécution tâche: {exc}")
