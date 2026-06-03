from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.admissions.models import Admission
from app.modules.admissions.schemas import AdmissionCreate

router = APIRouter(prefix="/admissions", tags=["admissions"])


@router.get("")
def list_admissions(db: Session = Depends(get_db)):
    rows = db.query(Admission).order_by(Admission.admitted_at.desc()).all()
    return {"data": rows, "message": "admissions list"}


@router.post("")
def create_admission(payload: AdmissionCreate, db: Session = Depends(get_db)):
    row = Admission(**payload.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "admission created"}


@router.post("/{admission_id}/close")
def close_admission(admission_id: str, db: Session = Depends(get_db)):
    row = db.query(Admission).filter(Admission.id == admission_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Admission not found")
    row.status = "CLOSED"
    row.closed_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "admission closed"}
