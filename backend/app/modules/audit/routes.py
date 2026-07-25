"""Read-only audit log endpoints (SUPER_ADMIN/ADMIN only)."""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.tenant import tenant_query
from app.db.session import get_db
from app.modules.audit.schemas import AuditLogRead
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import AuditLog
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
def list_audit_logs(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    action: str | None = Query(None, description="Filter by action (e.g. 'patient.create')"),
    resource_type: str | None = Query(None, description="Filter by resource type"),
    resource_id: str | None = Query(None, description="Filter by resource ID"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    start_date: datetime | None = Query(None, description="Filter logs from this date"),
    end_date: datetime | None = Query(None, description="Filter logs until this date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit.read")),
):
    """List audit logs with filters and pagination.

    SUPER_ADMIN sees all logs. ADMIN sees only their facility's logs.
    Other roles receive 403 (audit.read permission required).
    """
    # Use tenant_query — but AuditLog uses facility_id, so we filter on that
    # For SUPER_ADMIN, no filter. For others, only their facility.
    query = db.query(AuditLog)

    from app.core.tenant import CROSS_TENANT_ROLES
    if current_user.role not in CROSS_TENANT_ROLES:
        if current_user.facility_id is None:
            # No facility = no audit logs visible
            return {
                "data": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0,
            }
        query = query.filter(AuditLog.facility_id == current_user.facility_id)

    # Optional filters
    filters = []
    if action:
        filters.append(AuditLog.action == action)
    if resource_type:
        filters.append(AuditLog.resource_type == resource_type)
    if resource_id:
        filters.append(AuditLog.resource_id == resource_id)
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if start_date:
        filters.append(AuditLog.created_at >= start_date)
    if end_date:
        filters.append(AuditLog.created_at <= end_date)

    if filters:
        query = query.filter(and_(*filters))

    total = query.count()
    total_pages = (total + page_size - 1) // page_size
    rows = (
        query.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # Deserialize payload JSON for response
    data = []
    for row in rows:
        item = AuditLogRead.model_validate(row).model_dump()
        if row.payload:
            try:
                item["payload"] = json.loads(row.payload)
            except (json.JSONDecodeError, TypeError):
                item["payload"] = row.payload
        data.append(item)

    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.get("/logs/{log_id}")
def get_audit_log(
    log_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit.read")),
):
    """Get a single audit log entry by ID."""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log introuvable")

    # Tenant check
    from app.core.tenant import CROSS_TENANT_ROLES
    if current_user.role not in CROSS_TENANT_ROLES:
        if log.facility_id != current_user.facility_id:
            raise HTTPException(status_code=403, detail="Accès interdit")

    item = AuditLogRead.model_validate(log).model_dump()
    if log.payload:
        try:
            item["payload"] = json.loads(log.payload)
        except (json.JSONDecodeError, TypeError):
            item["payload"] = log.payload
    return item


# ============================================================================
# v2.8.4 — Registre des violations de données (RGPD Article 33)
# ============================================================================

@router.get("/breaches")
def list_data_breaches(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit.read")),
):
    """Lister les violations de données enregistrées.

    v2.8.4 — Conformité RGPD Article 33 : registre des violations.
    Chaque violation doit être notifiée à l'autorité de contrôle dans les 72h.
    """
    from app.modules.auth.models import DataBreach
    query = tenant_query(db, DataBreach, current_user) if hasattr(DataBreach, 'facility_id') else db.query(DataBreach)
    if current_user.role != "SUPER_ADMIN" and hasattr(DataBreach, 'facility_id'):
        query = query.filter(DataBreach.facility_id == current_user.facility_id)
    rows = query.order_by(DataBreach.detected_at.desc()).all()
    return {
        "data": [
            {
                "id": str(b.id),
                "title": b.title,
                "description": b.description,
                "severity": b.severity,
                "status": b.status,
                "affected_patients_count": b.affected_patients_count,
                "notified_authority": b.notified_authority,
                "notified_at": b.notified_at.isoformat() if b.notified_at else None,
                "authority_name": b.authority_name,
                "detected_at": b.detected_at.isoformat() if b.detected_at else None,
                "resolved_at": b.resolved_at.isoformat() if b.resolved_at else None,
            }
            for b in rows
        ],
        "total": len(rows),
    }


@router.post("/breaches")
def create_data_breach(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit.read")),
):
    """Enregistrer une violation de données.

    Body JSON:
    {
      "title": "Accès non autorisé au dossier patient",
      "description": "Un employé a accédé au dossier d'un patient sans motif médical",
      "severity": "HIGH",
      "affected_patients_count": 1
    }

    Dès qu'une violation est détectée, elle doit être enregistrée ici
    et notifiée à l'autorité de contrôle dans les 72h (RGPD Article 33).
    """
    from app.modules.auth.models import DataBreach

    title = (payload or {}).get("title", "").strip()
    description = (payload or {}).get("description", "").strip()
    severity = (payload or {}).get("severity", "MEDIUM").upper()

    if not title or not description:
        raise HTTPException(status_code=422, detail="title et description obligatoires")
    if severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
        raise HTTPException(status_code=422, detail="severity doit être LOW, MEDIUM, HIGH ou CRITICAL")

    breach = DataBreach(
        facility_id=current_user.facility_id,
        reported_by=str(current_user.id),
        title=title[:255],
        description=description,
        severity=severity,
        status="OPEN",
        affected_patients_count=int((payload or {}).get("affected_patients_count", 0)),
    )
    db.add(breach)
    db.commit()
    db.refresh(breach)

    audit_log(
        db=db,
        action="audit.breach.created",
        user=current_user,
        resource_type="data_breach",
        resource_id=str(breach.id),
        request=request,
        status_code=200,
    )

    return {
        "data": {
            "id": str(breach.id),
            "title": breach.title,
            "severity": breach.severity,
            "status": breach.status,
            "detected_at": breach.detected_at.isoformat(),
            "message": "Violation enregistrée. Notifier l'autorité dans les 72h.",
        },
        "message": "data breach registered",
    }


@router.post("/breaches/{breach_id}/notify")
def notify_breach_authority(
    breach_id: str,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("audit.read")),
):
    """Marquer une violation comme notifiée à l'autorité de contrôle.

    Body JSON:
    {"authority_name": "Commission Nationale de Protection des Données Guinée"}

    Conformité RGPD Article 33 : notification dans les 72h.
    """
    from app.modules.auth.models import DataBreach

    breach = db.query(DataBreach).filter(DataBreach.id == breach_id).first()
    if not breach:
        raise HTTPException(status_code=404, detail="Violation introuvable")

    breach.notified_authority = True
    breach.notified_at = utcnow()
    breach.authority_name = (payload or {}).get("authority_name", "Autorité de contrôle")
    breach.status = "NOTIFIED"
    db.commit()
    db.refresh(breach)

    audit_log(
        db=db,
        action="audit.breach.notified",
        user=current_user,
        resource_type="data_breach",
        resource_id=str(breach.id),
        request=request,
        status_code=200,
    )

    return {
        "data": {
            "id": str(breach.id),
            "notified_authority": breach.notified_authority,
            "notified_at": breach.notified_at.isoformat(),
            "authority_name": breach.authority_name,
            "status": breach.status,
        },
        "message": "Violation notifiée à l'autorité",
    }
