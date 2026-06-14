from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.patients.models import Patient
from app.modules.patients.schemas import PatientCreate

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def list_patients(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.read")),
):
    query = db.query(Patient).order_by(Patient.created_at.desc())
    if pagination.search:
        query = query.filter(
            (Patient.first_name.ilike(f"%{pagination.search}%"))
            | (Patient.last_name.ilike(f"%{pagination.search}%"))
            | (Patient.patient_number.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("")
def create_patient(
    payload: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.create")),
):
    row = Patient(**payload.model_dump())
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="patient.created",
        entity_type="patient",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "patient created"}


@router.get("/{patient_id}")
def get_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.read")),
):
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"data": row, "message": "patient detail"}
