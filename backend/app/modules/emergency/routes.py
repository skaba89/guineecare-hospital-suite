from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.emergency.models import EmergencyVisit
from app.modules.emergency.schemas import EmergencyOrientationUpdate, EmergencyTriageUpdate, EmergencyVisitCreate
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.get("/queue")
def get_emergency_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.read")),
):
    rows = db.query(EmergencyVisit).filter(EmergencyVisit.status != "CLOSED").order_by(EmergencyVisit.arrived_at.asc()).all()
    return {"data": rows, "message": "emergency queue"}


@router.post("/visits")
def create_emergency_visit(
    payload: EmergencyVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.create")),
):
    row = EmergencyVisit(**payload.dict())
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
    row.updated_at = datetime.utcnow()
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
    row.status = "CLOSED"
    row.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "orientation saved"}
