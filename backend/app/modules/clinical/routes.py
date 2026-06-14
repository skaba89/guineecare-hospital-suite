from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.patients.models import Patient
from app.modules.clinical.models import ClinicalNote, PatientMeasurement, Diagnosis
from app.modules.clinical.schemas import (
    ClinicalNoteCreate,
    PatientMeasurementCreate,
    DiagnosisCreate,
)

router = APIRouter(prefix="/clinical", tags=["clinical"])


# ── Helpers ───────────────────────────────────────────────────

def _get_patient_or_404(db: Session, patient_id: str) -> Patient:
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return row


# ── Clinical Notes ────────────────────────────────────────────

@router.get("/patients/{patient_id}/notes")
def list_clinical_notes(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    _get_patient_or_404(db, patient_id)
    rows = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.patient_id == patient_id)
        .order_by(ClinicalNote.created_at.desc())
        .all()
    )
    return {"data": rows, "message": "clinical notes list"}


@router.post("/patients/{patient_id}/notes")
def create_clinical_note(
    patient_id: str,
    payload: ClinicalNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.write")),
):
    _get_patient_or_404(db, patient_id)
    row = ClinicalNote(
        **payload.model_dump(),
        patient_id=patient_id,
        created_by=current_user.id,
    )
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="clinical.note_created",
        entity_type="clinical_note",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "clinical note created"}


# ── Patient Measurements ─────────────────────────────────────

@router.get("/patients/{patient_id}/measurements")
def list_patient_measurements(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    _get_patient_or_404(db, patient_id)
    rows = (
        db.query(PatientMeasurement)
        .filter(PatientMeasurement.patient_id == patient_id)
        .order_by(PatientMeasurement.recorded_at.desc())
        .all()
    )
    return {"data": rows, "message": "patient measurements list"}


@router.post("/patients/{patient_id}/measurements")
def create_patient_measurement(
    patient_id: str,
    payload: PatientMeasurementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.write")),
):
    _get_patient_or_404(db, patient_id)
    row = PatientMeasurement(
        **payload.model_dump(),
        patient_id=patient_id,
        recorded_by=current_user.id,
    )
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="clinical.measurement_recorded",
        entity_type="patient_measurement",
        entity_id=row.id,
        level="INFO",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "patient measurement recorded"}


# ── Diagnoses ────────────────────────────────────────────────

@router.get("/patients/{patient_id}/diagnoses")
def list_diagnoses(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    _get_patient_or_404(db, patient_id)
    rows = (
        db.query(Diagnosis)
        .filter(Diagnosis.patient_id == patient_id)
        .order_by(Diagnosis.created_at.desc())
        .all()
    )
    return {"data": rows, "message": "diagnoses list"}


@router.post("/patients/{patient_id}/diagnoses")
def create_diagnosis(
    patient_id: str,
    payload: DiagnosisCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.write")),
):
    _get_patient_or_404(db, patient_id)
    row = Diagnosis(
        **payload.model_dump(),
        patient_id=patient_id,
        created_by=current_user.id,
    )
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="clinical.diagnosis_created",
        entity_type="diagnosis",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "diagnosis created"}
