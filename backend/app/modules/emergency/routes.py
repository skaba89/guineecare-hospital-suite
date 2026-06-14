from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.db.session import get_db
from app.modules.emergency.models import EmergencyVisit
from app.modules.emergency.schemas import (
    EmergencyCareUpdate,
    EmergencyDischargeUpdate,
    EmergencyOrientationUpdate,
    EmergencyTriageUpdate,
    EmergencyVisitCreate,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.get("/queue")
def get_emergency_queue(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.read")),
):
    query = db.query(EmergencyVisit).filter(EmergencyVisit.status.notin_(["ORIENTED", "DISCHARGED"])).order_by(EmergencyVisit.arrived_at.asc())
    if pagination.search:
        query = query.filter(
            (EmergencyVisit.chief_complaint.ilike(f"%{pagination.search}%"))
            | (EmergencyVisit.priority_level.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/visits")
def create_emergency_visit(
    payload: EmergencyVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.create")),
):
    row = EmergencyVisit(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "emergency visit created"}


@router.post("/visits/{visit_id}/triage")
def triage_visit(
    visit_id: str,
    payload: EmergencyTriageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.triage")),
):
    row = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    row.priority_level = payload.priority_level
    row.status = "TRIAGED"
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "triage saved"}


@router.post("/visits/{visit_id}/orientation")
def orient_visit(
    visit_id: str,
    payload: EmergencyOrientationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.orient")),
):
    row = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    row.orientation = payload.orientation
    row.status = "ORIENTED"
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "orientation saved"}


@router.post("/visits/{visit_id}/care")
def care_visit(
    visit_id: str,
    payload: EmergencyCareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.care")),
):
    """Prise en charge médicale — transition TRIAGED → IN_CARE"""
    row = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    if row.status not in ("TRIAGED", "WAITING"):
        raise HTTPException(status_code=409, detail="Visit cannot be taken in care from current status")
    row.status = "IN_CARE"
    row.attending_doctor_id = payload.attending_doctor_id
    if payload.vital_signs:
        row.vital_signs = payload.vital_signs
    if payload.treatment_notes:
        row.treatment_notes = payload.treatment_notes
    row.seen_at = utcnow()
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "patient taken in care"}


@router.post("/visits/{visit_id}/discharge")
def discharge_visit(
    visit_id: str,
    payload: EmergencyDischargeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.discharge")),
):
    """Sortie des urgences — transition IN_CARE → DISCHARGED"""
    row = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    if row.status != "IN_CARE":
        raise HTTPException(status_code=409, detail="Only patients in care can be discharged")
    row.status = "DISCHARGED"
    row.discharge_summary = payload.discharge_summary
    row.discharge_destination = payload.discharge_destination
    if payload.orientation:
        row.orientation = payload.orientation
    row.discharged_at = utcnow()
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "patient discharged from emergency"}
