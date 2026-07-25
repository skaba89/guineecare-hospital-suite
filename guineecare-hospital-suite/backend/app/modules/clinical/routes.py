from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.audit.service import audit_log
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.patients.models import Patient
from app.modules.clinical.models import ClinicalNote, PatientMeasurement, Diagnosis, Prescription
from app.modules.clinical.schemas import (
    PrescriptionCreate,
    ClinicalNoteCreate,
    PatientMeasurementCreate,
    DiagnosisCreate,
)

router = APIRouter(prefix="/clinical", tags=["clinical"])


# ── Helpers ───────────────────────────────────────────────────

def _get_patient_or_404(db: Session, patient_id: str, current_user: User | None = None) -> Patient:
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    if current_user:
        enforce_facility_access(current_user, row.facility_id)
    return row


# ── Clinical Notes ────────────────────────────────────────────

@router.get("/patients/{patient_id}/notes")
def list_clinical_notes(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    _get_patient_or_404(db, patient_id, current_user)
    rows = (
        tenant_query(db, ClinicalNote, current_user)
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
    patient = _get_patient_or_404(db, patient_id, current_user)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = patient.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = ClinicalNote(
        **data,
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
    # v2.8.0 — Audit log pour traçabilité médico-légale
    audit_log(
        db=db,
        action="clinical.note.create",
        user=current_user,
        resource_type="clinical_note",
        resource_id=str(row.id),
        request=None,  # pas de Request dans cette fonction
        status_code=200,
    )
    return {"data": row, "message": "clinical note created"}


# ── Patient Measurements ─────────────────────────────────────

@router.get("/patients/{patient_id}/measurements")
def list_patient_measurements(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    _get_patient_or_404(db, patient_id, current_user)
    rows = (
        tenant_query(db, PatientMeasurement, current_user)
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
    patient = _get_patient_or_404(db, patient_id, current_user)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = patient.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))

    # v2.8.2 — P0-7 fix : auto-extraction de value_numeric
    # Si la valeur est un nombre pur (ex: "38.5", "72"), on stocke aussi
    # la version numérique pour les charts et FHIR.
    # Si la valeur est composite (ex: "120/80"), value_numeric = NULL.
    raw_value = data.get("value", "")
    try:
        data["value_numeric"] = float(raw_value)
    except (ValueError, TypeError):
        data["value_numeric"] = None

    row = PatientMeasurement(
        **data,
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
    # v2.8.0 — Audit log pour traçabilité médico-légale
    audit_log(
        db=db,
        action="clinical.measurement.create",
        user=current_user,
        resource_type="measurement",
        resource_id=str(row.id),
        request=None,  # pas de Request dans cette fonction
        status_code=200,
    )
    return {"data": row, "message": "patient measurement recorded"}


# ── Diagnoses ────────────────────────────────────────────────

@router.get("/patients/{patient_id}/diagnoses")
def list_diagnoses(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    _get_patient_or_404(db, patient_id, current_user)
    rows = (
        tenant_query(db, Diagnosis, current_user)
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
    patient = _get_patient_or_404(db, patient_id, current_user)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = patient.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = Diagnosis(
        **data,
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


# ── Global list endpoints (for UI pages without patient context) ─────

@router.get("/notes")
def list_all_notes(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    """Liste toutes les notes cliniques (paginé, multi-tenant)."""
    query = tenant_query(db, ClinicalNote, current_user).order_by(ClinicalNote.created_at.desc())
    return paginate(query, pagination)


@router.get("/measurements")
def list_all_measurements(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    """Liste toutes les constantes vitales (paginé, multi-tenant)."""
    query = tenant_query(db, PatientMeasurement, current_user).order_by(PatientMeasurement.recorded_at.desc())
    return paginate(query, pagination)


# ============================================================================
# v2.6.0 — Phase 7 : Prescriptions structurées
# ============================================================================

@router.post("/prescriptions")
def create_prescription(
    payload: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.write")),
):
    """Créer une prescription médicamenteuse structurée.

    Body JSON:
    {
      "patient_id": "...",
      "admission_id": "...",          // optionnel
      "clinical_note_id": "...",      // optionnel — lier à une consultation
      "medication_name": "Paracétamol",
      "dosage": "500mg",
      "frequency": "3 fois par jour",
      "duration": "7 jours",
      "quantity": 21,
      "instructions": "À prendre avec un grand verre d'eau"
    }

    Sécurité :
    - permission clinical.write (DOCTOR, MIDWIFE, SUPER_ADMIN, ADMIN)
    - enforce_facility_access sur patient_id
    """
    patient_id = payload.patient_id
    medication_name = payload.medication_name
    dosage = payload.dosage
    frequency = payload.frequency

    if not patient_id or not medication_name or not dosage or not frequency:
        raise HTTPException(
            status_code=422,
            detail="patient_id, medication_name, dosage et frequency sont obligatoires",
        )

    # Vérifier patient + tenant
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    enforce_facility_access(current_user, patient.facility_id)

    rx = Prescription(
        facility_id=patient.facility_id,
        patient_id=patient_id,
        admission_id=payload.admission_id,
        clinical_note_id=payload.clinical_note_id,
        medication_name=medication_name,
        dosage=dosage,
        frequency=frequency,
        duration=payload.duration,
        quantity=payload.quantity,
        instructions=payload.instructions,
        status="ACTIVE",
        prescribed_by=str(current_user.id),
    )
    db.add(rx)
    db.commit()
    db.refresh(rx)
    # v2.8.0 — Audit log pour traçabilité médico-légale
    audit_log(
        db=db,
        action="clinical.prescription.create",
        user=current_user,
        resource_type="prescription",
        resource_id=str(rx.id),
        request=None,  # pas de Request dans cette fonction
        status_code=200,
    )

    record_activity(
        db=db, actor_id=str(current_user.id), action_name="prescription.create",
        entity_type="prescription", entity_id=rx.id,
        notes=f"{medication_name} {dosage} {frequency}",
    )

    return {
        "data": {
            "id": str(rx.id),
            "patient_id": str(rx.patient_id),
            "medication_name": rx.medication_name,
            "dosage": rx.dosage,
            "frequency": rx.frequency,
            "duration": rx.duration,
            "quantity": rx.quantity,
            "instructions": rx.instructions,
            "status": rx.status,
            "prescribed_by": rx.prescribed_by,
            "prescribed_at": rx.prescribed_at.isoformat() if rx.prescribed_at else None,
        },
        "message": "Prescription créée",
    }


@router.get("/prescriptions")
def list_prescriptions(
    patient_id: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    """Lister les prescriptions (filtrable par patient + statut, paginé).

    Sécurité : tenant_query filtre par facility_id.
    """
    query = tenant_query(db, Prescription, current_user).order_by(
        Prescription.prescribed_at.desc()
    )
    if patient_id:
        query = query.filter(Prescription.patient_id == patient_id)
    if status:
        query = query.filter(Prescription.status == status)
    return paginate(query, pagination)


@router.get("/patients/{patient_id}/prescriptions")
def list_patient_prescriptions(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    """Lister les prescriptions d'un patient spécifique."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    enforce_facility_access(current_user, patient.facility_id)

    rows = (
        db.query(Prescription)
        .filter(Prescription.patient_id == patient_id)
        .order_by(Prescription.prescribed_at.desc())
        .all()
    )
    return {
        "data": [
            {
                "id": str(r.id),
                "medication_name": r.medication_name,
                "dosage": r.dosage,
                "frequency": r.frequency,
                "duration": r.duration,
                "quantity": r.quantity,
                "instructions": r.instructions,
                "status": r.status,
                "prescribed_by": r.prescribed_by,
                "prescribed_at": r.prescribed_at.isoformat() if r.prescribed_at else None,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.patch("/prescriptions/{prescription_id}/cancel")
def cancel_prescription(
    prescription_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.write")),
):
    """Annuler une prescription (status → CANCELLED)."""
    rx = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not rx:
        raise HTTPException(status_code=404, detail="Prescription introuvable")
    enforce_facility_access(current_user, rx.facility_id)

    if rx.status == "CANCELLED":
        raise HTTPException(status_code=409, detail="Prescription déjà annulée")

    rx.status = "CANCELLED"
    db.commit()
    db.refresh(rx)
    return {"data": {"id": str(rx.id), "status": rx.status}, "message": "Prescription annulée"}
