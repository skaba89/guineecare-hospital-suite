"""Routes Dashboard Qualité v1.4.0 — seuils, alertes, dashboard agrégé.

Sous-module monté sous `/api/v1/quality/*` (préfixe partagé avec le module qualité existant).

Permissions RBAC :
- `quality.read` : consultation dashboard, alertes, seuils.
- `quality.manage` : CRUD seuils, ack/resolve/close alertes, run check_thresholds.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import enforce_facility_access, tenant_query
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.audit.service import audit_log
from app.modules.quality.dashboard_models import QualityAlert, QualityThreshold
from app.modules.quality.dashboard_schemas import (
    CheckThresholdsResponse,
    QualityAlertAck,
    QualityAlertListResponse,
    QualityAlertRead,
    QualityAlertResolve,
    QualityDashboardResponse,
    QualityThresholdCreate,
    QualityThresholdListResponse,
    QualityThresholdRead,
    QualityThresholdUpdate,
)
from app.modules.quality.dashboard_service import (
    acknowledge_alert,
    check_thresholds,
    close_alert,
    compute_dashboard,
    resolve_alert,
    seed_default_indicators,
    seed_default_thresholds,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/quality", tags=["quality-dashboard"])


# ── Dashboard agrégé ────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=QualityDashboardResponse)
def get_dashboard(
    facility_id: str | None = None,
    department_id: str | None = None,
    days: int = Query(30, ge=1, le=365, description="Période en jours (1-365)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.read")),
):
    """Retourne le dashboard qualité agrégé : KPIs, incidents, alertes, tendances.

    Multi-tenant : SUPER_ADMIN peut voir toutes les facilities (ou une facility
    explicite via `facility_id`). Les autres rôles sont limités à leur facility.
    """
    if current_user.role != "SUPER_ADMIN":
        facility_id = current_user.facility_id
    elif facility_id:
        enforce_facility_access(current_user, facility_id)

    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=days)

    return QualityDashboardResponse(
        **compute_dashboard(
            db,
            facility_id=facility_id,
            department_id=department_id,
            period_start=period_start,
            period_end=period_end,
        )
    )


@router.get("/indicators/catalog")
def get_indicators_catalog(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.read")),
):
    """Retourne le catalogue statique d'indicateurs prédéfinis (OMS/HAS).

    Indépendant du tenant — utilisé par l'UI pour afficher la documentation.
    """
    from app.modules.quality.dashboard_service import DEFAULT_INDICATORS, DEFAULT_THRESHOLDS
    return {
        "indicators": DEFAULT_INDICATORS,
        "thresholds": DEFAULT_THRESHOLDS,
    }


@router.post("/seed-defaults")
def seed_defaults(
    facility_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    """Insère les indicateurs OMS/HAS prédéfinis + seuils par défaut.

    Idempotent : ne crée que ce qui n'existe pas encore.
    Accessible uniquement aux ADMIN/SUPER_ADMIN.
    """
    if current_user.role != "SUPER_ADMIN":
        facility_id = current_user.facility_id
    elif facility_id:
        enforce_facility_access(current_user, facility_id)

    indicators_created = seed_default_indicators(db, facility_id=facility_id)
    thresholds_created = seed_default_thresholds(db, facility_id=facility_id)

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="quality.seed_defaults",
        entity_type="quality_threshold",
        level="IMPORTANT",
        notes=f"indicators_created={indicators_created}, thresholds_created={thresholds_created}, facility={facility_id}",
    )
    db.commit()
    return {
        "indicators_created": indicators_created,
        "thresholds_created": thresholds_created,
        "facility_id": facility_id,
    }


# ── Thresholds ──────────────────────────────────────────────────────────────

@router.get("/thresholds", response_model=QualityThresholdListResponse)
def list_thresholds(
    facility_id: str | None = None,
    indicator_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.read")),
):
    """Liste les seuils d'alerte qualité."""
    query = db.query(QualityThreshold)
    if current_user.role != "SUPER_ADMIN":
        if not current_user.facility_id:
            # Fail closed : un rôle établissement non rattaché ne voit même pas
            # le catalogue global, car son contexte tenant est invalide.
            query = query.filter(QualityThreshold.id == "__NO_FACILITY__")
        else:
            query = query.filter(
                (QualityThreshold.facility_id.is_(None)) |
                (QualityThreshold.facility_id == current_user.facility_id)
            )
    if facility_id:
        enforce_facility_access(current_user, facility_id)
        query = query.filter(QualityThreshold.facility_id == facility_id)
    if indicator_id:
        query = query.filter(QualityThreshold.indicator_id == indicator_id)

    rows = query.order_by(QualityThreshold.created_at.desc()).all()
    return QualityThresholdListResponse(
        data=[QualityThresholdRead.from_model(r) for r in rows],
        total=len(rows),
    )


@router.post("/thresholds", response_model=QualityThresholdRead, status_code=201)
def create_threshold(
    payload: QualityThresholdCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    """Crée un seuil d'alerte qualité."""
    if payload.facility_id:
        enforce_facility_access(current_user, payload.facility_id)
    elif not payload.facility_id and current_user.role != "SUPER_ADMIN":
        payload.facility_id = current_user.facility_id

    row = QualityThreshold(
        facility_id=payload.facility_id,
        department_id=payload.department_id,
        indicator_id=payload.indicator_id,
        comparator=payload.comparator,
        threshold_value=payload.threshold_value,
        severity=payload.severity,
        alert_message=payload.alert_message,
        notify_roles=",".join(payload.notify_roles) if payload.notify_roles else "ADMIN",
        channels=",".join(payload.channels) if payload.channels else "in_app",
        enabled="true" if payload.enabled else "false",
        cooldown_hours=str(payload.cooldown_hours),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        user=current_user,
        action="quality.threshold.create",
        resource_type="quality_threshold",
        resource_id=row.id,
        request=request,
        status_code=201,
        payload={"indicator_id": row.indicator_id, "comparator": row.comparator, "threshold_value": row.threshold_value},
    )
    return QualityThresholdRead.from_model(row)


@router.patch("/thresholds/{threshold_id}", response_model=QualityThresholdRead)
def update_threshold(
    threshold_id: str,
    payload: QualityThresholdUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    """Met à jour un seuil d'alerte qualité."""
    row = db.query(QualityThreshold).filter(QualityThreshold.id == threshold_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Seuil introuvable")
    if row.facility_id is None and current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Seul un SUPER_ADMIN peut modifier un seuil qualité global",
        )
    enforce_facility_access(current_user, row.facility_id)

    if payload.department_id is not None:
        row.department_id = payload.department_id
    if payload.comparator is not None:
        row.comparator = payload.comparator
    if payload.threshold_value is not None:
        row.threshold_value = payload.threshold_value
    if payload.severity is not None:
        row.severity = payload.severity
    if payload.alert_message is not None:
        row.alert_message = payload.alert_message
    if payload.notify_roles is not None:
        row.notify_roles = ",".join(payload.notify_roles) if payload.notify_roles else "ADMIN"
    if payload.channels is not None:
        row.channels = ",".join(payload.channels) if payload.channels else "in_app"
    if payload.enabled is not None:
        row.enabled = "true" if payload.enabled else "false"
    if payload.cooldown_hours is not None:
        row.cooldown_hours = str(payload.cooldown_hours)

    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        user=current_user,
        action="quality.threshold.update",
        resource_type="quality_threshold",
        resource_id=row.id,
        request=request,
        status_code=200,
        payload={"updated_fields": list(payload.model_dump(exclude_unset=True).keys())},
    )
    return QualityThresholdRead.from_model(row)


@router.delete("/thresholds/{threshold_id}", status_code=204)
def delete_threshold(
    threshold_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    """Supprime un seuil d'alerte qualité."""
    row = db.query(QualityThreshold).filter(QualityThreshold.id == threshold_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Seuil introuvable")
    if row.facility_id is None and current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Seul un SUPER_ADMIN peut supprimer un seuil qualité global",
        )
    enforce_facility_access(current_user, row.facility_id)
    db.delete(row)
    db.commit()

    audit_log(
        db=db,
        user=current_user,
        action="quality.threshold.delete",
        resource_type="quality_threshold",
        resource_id=threshold_id,
        request=request,
        status_code=204,
    )
    return None


# ── Alertes ─────────────────────────────────────────────────────────────────

@router.get("/alerts", response_model=QualityAlertListResponse)
def list_alerts(
    status: str | None = None,
    severity: str | None = None,
    facility_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.read")),
):
    """Liste les alertes qualité (paginé, multi-tenant)."""
    query = tenant_query(db, QualityAlert, current_user)
    if status:
        query = query.filter(QualityAlert.status == status)
    if severity:
        query = query.filter(QualityAlert.severity == severity)
    if facility_id:
        enforce_facility_access(current_user, facility_id)
        query = query.filter(QualityAlert.facility_id == facility_id)
    query = query.order_by(QualityAlert.created_at.desc())

    result = paginate(query, pagination)
    return QualityAlertListResponse(
        data=[QualityAlertRead.from_model(r) for r in result["data"]],
        total=result["total"],
    )


@router.post("/alerts/check", response_model=CheckThresholdsResponse)
def run_check_thresholds(
    request: Request,
    facility_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    """Déclenche manuellement l'évaluation des seuils sur les mesures des 7 derniers jours.

    En production, cette route est appelée automatiquement par un job Celery
    (à configurer) toutes les heures. Endpoint manuel pour tests et re-run.
    """
    if current_user.role != "SUPER_ADMIN":
        facility_id = current_user.facility_id
    elif facility_id:
        enforce_facility_access(current_user, facility_id)

    raised = check_thresholds(db, facility_id=facility_id)

    audit_log(
        db=db,
        user=current_user,
        action="quality.alerts.check",
        resource_type="quality_alert",
        request=request,
        status_code=200,
        payload={"facility_id": facility_id, "raised_count": len(raised)},
    )

    return CheckThresholdsResponse(
        evaluated=0,
        raised=len(raised),
        alerts=[QualityAlertRead.from_model(a) for a in raised],
    )


@router.post("/alerts/{alert_id}/acknowledge", response_model=QualityAlertRead)
def ack_alert(
    alert_id: str,
    payload: QualityAlertAck,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    """Marque une alerte comme prise en charge (ACKNOWLEDGED)."""
    existing = tenant_query(db, QualityAlert, current_user).filter(QualityAlert.id == alert_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    alert = acknowledge_alert(db, alert_id, current_user.id, payload.assign_to)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    audit_log(
        db=db,
        user=current_user,
        action="quality.alert.acknowledge",
        resource_type="quality_alert",
        resource_id=alert.id,
        request=request,
        status_code=200,
        payload={"assign_to": payload.assign_to},
    )
    return QualityAlertRead.from_model(alert)


@router.post("/alerts/{alert_id}/resolve", response_model=QualityAlertRead)
def resolve_alert_route(
    alert_id: str,
    payload: QualityAlertResolve,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    """Résout une alerte avec une note de résolution."""
    existing = tenant_query(db, QualityAlert, current_user).filter(QualityAlert.id == alert_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    alert = resolve_alert(db, alert_id, current_user.id, payload.resolution_note)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    audit_log(
        db=db,
        user=current_user,
        action="quality.alert.resolve",
        resource_type="quality_alert",
        resource_id=alert.id,
        request=request,
        status_code=200,
        payload={"resolution_note": payload.resolution_note[:200]},
    )
    return QualityAlertRead.from_model(alert)


@router.post("/alerts/{alert_id}/close", response_model=QualityAlertRead)
def close_alert_route(
    alert_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    """Clôture une alerte résolue."""
    existing = tenant_query(db, QualityAlert, current_user).filter(QualityAlert.id == alert_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    alert = close_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")

    audit_log(
        db=db,
        user=current_user,
        action="quality.alert.close",
        resource_type="quality_alert",
        resource_id=alert.id,
        request=request,
        status_code=200,
    )
    return QualityAlertRead.from_model(alert)
