from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
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
    query = tenant_query(db, Patient, current_user).order_by(Patient.created_at.desc())
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
    data = payload.model_dump(exclude_none=True)
    # Nettoyer les champs vides (le frontend SimpleForm envoie "" pour les champs non remplis)
    for key in list(data.keys()):
        if data[key] == "":
            del data[key]
    # FORCER les champs médicaux avec valeurs par défaut (la DB Neon n'a pas de server_default)
    if "blood_type" not in data:
        data["blood_type"] = "NON_RENSEIGNE"
    if "allergies" not in data:
        data["allergies"] = "Non renseigné"
    if "medical_history" not in data:
        data["medical_history"] = "Non renseigné"
    if "current_medication" not in data:
        data["current_medication"] = "Non renseigné"
    if "chronic_conditions" not in data:
        data["chronic_conditions"] = "Non renseigné"
    # Auto-génère facility_id si manquant
    if not data.get("facility_id"):
        # Si le SUPER_ADMIN n'a pas de facility, utiliser la première facility disponible
        if current_user.facility_id:
            data["facility_id"] = current_user.facility_id
        else:
            from app.modules.facilities.models import Facility
            first_fac = db.query(Facility).first()
            if not first_fac:
                raise HTTPException(status_code=400, detail="Aucun établissement trouvé. Créez un établissement d'abord.")
            data["facility_id"] = first_fac.id
    enforce_facility_access(current_user, data.get("facility_id"))
    # Auto-génère patient_number si manquant (format PAT-YYYYMMDDHHMMSS + suffixe aléatoire)
    if not data.get("patient_number"):
        import secrets as _secrets
        data["patient_number"] = f"PAT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_secrets.token_hex(3)}"
    # Vérifier l'unicité du patient_number
    existing = db.query(Patient).filter(Patient.patient_number == data["patient_number"]).first()
    if existing:
        import secrets as _secrets
        data["patient_number"] = f"PAT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_secrets.token_hex(4)}"
    row = Patient(**data)
    db.add(row)
    try:
        db.flush()
    except Exception:
        import secrets as _secrets
        data["patient_number"] = f"PAT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{_secrets.token_hex(6)}"
        row = Patient(**data)
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
    enforce_facility_access(current_user, row.facility_id)
    return {"data": row, "message": "patient detail"}
