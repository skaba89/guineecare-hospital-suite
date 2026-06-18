from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
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

def _get_patient_or_404(db: Session, patient_id: str, current_user: User | None = None) -> Patient:
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    if current_user:
        enforce_facility_access(current_user, row.facility_id)
    return row


def _get_record_or_404(db: Session, record_id: str, current_user: User | None = None) -> MaternityRecord:
    row = db.query(MaternityRecord).filter(MaternityRecord.id == record_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Maternity record not found")
    if current_user:
        enforce_facility_access(current_user, row.facility_id)
    return row


# ── Maternity Records ────────────────────────────────────────

@router.get("/records")
def list_maternity_records(
    facility_id: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.read")),
):
    query = tenant_query(db, MaternityRecord, current_user)
    if facility_id:
        query = query.filter(MaternityRecord.facility_id == facility_id)
    if status:
        query = query.filter(MaternityRecord.status == status)
    query = query.order_by(MaternityRecord.created_at.desc())
    return paginate(query, pagination)


@router.post("/records")
def create_maternity_record(
    payload: MaternityRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.write")),
):
    _get_patient_or_404(db, payload.patient_id, current_user)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = MaternityRecord(
        **data,
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
    record = _get_record_or_404(db, record_id, current_user)
    consultations = (
        tenant_query(db, MaternityConsultation, current_user)
        .filter(MaternityConsultation.record_id == record_id)
        .order_by(MaternityConsultation.consulted_at.desc())
        .all()
    )
    deliveries = (
        tenant_query(db, DeliveryRecord, current_user)
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
    _get_record_or_404(db, record_id, current_user)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = MaternityConsultation(
        **data,
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
    _get_record_or_404(db, record_id, current_user)
    rows = (
        tenant_query(db, MaternityConsultation, current_user)
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
    maternity_record = _get_record_or_404(db, record_id, current_user)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = DeliveryRecord(
        **data,
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
    _get_record_or_404(db, record_id, current_user)
    rows = (
        tenant_query(db, DeliveryRecord, current_user)
        .filter(DeliveryRecord.record_id == record_id)
        .order_by(DeliveryRecord.delivery_date.desc())
        .all()
    )
    return {"data": rows, "message": "deliveries list"}
