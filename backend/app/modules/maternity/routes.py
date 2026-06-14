from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.patients.models import Patient
from app.modules.maternity.models import MaternityRecord, MaternityConsultation, DeliveryRecord
from app.modules.maternity.schemas import (
    MaternityRecordCreate,
    MaternityConsultationCreate,
    DeliveryRecordCreate,
)

router = APIRouter(prefix="/maternity", tags=["maternity"])


# ── Helpers ───────────────────────────────────────────────────

def _get_patient_or_404(db: Session, patient_id: str) -> Patient:
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return row


def _get_record_or_404(db: Session, record_id: str) -> MaternityRecord:
    row = db.query(MaternityRecord).filter(MaternityRecord.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Maternity record not found")
    return row


# ── Maternity Records ────────────────────────────────────────

@router.get("/records")
def list_maternity_records(
    facility_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.read")),
):
    query = db.query(MaternityRecord)
    if facility_id:
        query = query.filter(MaternityRecord.facility_id == facility_id)
    if status:
        query = query.filter(MaternityRecord.status == status)
    rows = query.order_by(MaternityRecord.created_at.desc()).all()
    return {"data": rows, "message": "maternity records list"}


@router.post("/records")
def create_maternity_record(
    payload: MaternityRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.write")),
):
    _get_patient_or_404(db, payload.patient_id)
    row = MaternityRecord(
        **payload.model_dump(),
        created_by=current_user.id,
    )
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="maternity.record_created",
        entity_type="maternity_record",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "maternity record created"}


@router.get("/records/{record_id}")
def get_maternity_record(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.read")),
):
    record = _get_record_or_404(db, record_id)
    consultations = (
        db.query(MaternityConsultation)
        .filter(MaternityConsultation.record_id == record_id)
        .order_by(MaternityConsultation.consulted_at.desc())
        .all()
    )
    deliveries = (
        db.query(DeliveryRecord)
        .filter(DeliveryRecord.record_id == record_id)
        .order_by(DeliveryRecord.delivery_date.desc())
        .all()
    )
    return {
        "data": {
            "record": record,
            "consultations": consultations,
            "deliveries": deliveries,
        },
        "message": "maternity record detail",
    }


# ── Maternity Consultations ──────────────────────────────────

@router.post("/records/{record_id}/consultations")
def create_consultation(
    record_id: str,
    payload: MaternityConsultationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.write")),
):
    _get_record_or_404(db, record_id)
    row = MaternityConsultation(
        **payload.model_dump(),
        record_id=record_id,
        consulted_by=current_user.id,
    )
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="maternity.consultation_created",
        entity_type="maternity_consultation",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "consultation created"}


@router.get("/records/{record_id}/consultations")
def list_consultations(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.read")),
):
    _get_record_or_404(db, record_id)
    rows = (
        db.query(MaternityConsultation)
        .filter(MaternityConsultation.record_id == record_id)
        .order_by(MaternityConsultation.consulted_at.desc())
        .all()
    )
    return {"data": rows, "message": "consultations list"}


# ── Delivery Records ─────────────────────────────────────────

@router.post("/records/{record_id}/deliveries")
def create_delivery(
    record_id: str,
    payload: DeliveryRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.write")),
):
    maternity_record = _get_record_or_404(db, record_id)
    row = DeliveryRecord(
        **payload.model_dump(),
        record_id=record_id,
        performed_by=current_user.id,
    )
    db.add(row)

    # Auto-update maternity record status to DELIVERED
    maternity_record.status = "DELIVERED"

    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="maternity.delivery_recorded",
        entity_type="delivery_record",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "delivery recorded"}


@router.get("/records/{record_id}/deliveries")
def list_deliveries(
    record_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.read")),
):
    _get_record_or_404(db, record_id)
    rows = (
        db.query(DeliveryRecord)
        .filter(DeliveryRecord.record_id == record_id)
        .order_by(DeliveryRecord.delivery_date.desc())
        .all()
    )
    return {"data": rows, "message": "deliveries list"}
