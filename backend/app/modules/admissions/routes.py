from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.admissions.models import Admission
from app.modules.admissions.schemas import AdmissionCreate

router = APIRouter(prefix="/admissions", tags=["admissions"])


@router.get("")
def list_admissions(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admission.read")),
):
    query = tenant_query(db, Admission, current_user).order_by(Admission.admitted_at.desc())
    if pagination.search:
        query = query.filter(Admission.admission_type.ilike(f"%{pagination.search}%"))
    return paginate(query, pagination)


@router.post("")
def create_admission(
    payload: AdmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admission.create")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = Admission(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="admission.created",
        entity_type="admission",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "admission created"}


@router.post("/{admission_id}/close")
def close_admission(
    admission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("admission.close")),
):
    row = db.query(Admission).filter(Admission.id == admission_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Admission not found")
    enforce_facility_access(current_user, row.facility_id)
    row.status = "CLOSED"
    row.closed_at = utcnow()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="admission.closed",
        entity_type="admission",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "admission closed"}
