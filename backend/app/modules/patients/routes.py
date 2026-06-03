from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.patients.models import Patient
from app.modules.patients.schemas import PatientCreate

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def list_patients(db: Session = Depends(get_db)):
    rows = db.query(Patient).order_by(Patient.created_at.desc()).all()
    return {"data": rows, "message": "patients list"}


@router.post("")
def create_patient(payload: PatientCreate, db: Session = Depends(get_db)):
    row = Patient(**payload.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "patient created"}


@router.get("/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {"data": row, "message": "patient detail"}
