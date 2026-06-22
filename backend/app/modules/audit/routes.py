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
