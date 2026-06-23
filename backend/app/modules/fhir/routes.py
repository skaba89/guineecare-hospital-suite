"""Routes FHIR R4 v1.6.0 — endpoints RESTful conformes à la spécification FHIR.

Mountées sous `/api/v1/fhir/*` (préfixe FHIR standard).

Endpoints implémentés :
- `GET /fhir/Patient` — recherche (par _id, identifier, name, family, given, birthdate)
- `GET /fhir/Patient/{id}` — lecture
- `POST /fhir/Patient` — création (mapping inverse → table patients)
- `GET /fhir/Encounter` — recherche (par patient, status, date)
- `GET /fhir/Encounter/{id}` — lecture
- `GET /fhir/Observation` — recherche (par patient, category, code, date)
- `GET /fhir/Observation/{id}` — lecture
- `GET /fhir/MedicationRequest` — recherche (par patient, status)
- `GET /fhir/MedicationRequest/{id}` — lecture
- `GET /fhir/DiagnosticReport` — recherche (par patient, status, code)
- `GET /fhir/DiagnosticReport/{id}` — lecture
- `GET /fhir/metadata` — CapabilityStatement

Authentification :
- v1.6 : JWT Bearer standard GuinéeCare (permission `fhir.read`).
- v1.7 (prévu) : OAuth2 SMART on FHIR avec scopes `patient/*.read`.

Notes :
- Recherche full-text sur `name` : recherche sur first_name + last_name.
- Pagination FHIR : `_count` (défaut 50, max 200).
- Format réponse : Bundle searchset pour les listes, ressource simple pour les GET/{id}.
"""
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.admissions.models import Admission
from app.modules.audit.service import audit_log
from app.modules.clinical.models import ClinicalNote, PatientMeasurement
from app.modules.fhir.conversions import (
    admission_to_fhir,
    bundle,
    imaging_result_to_fhir,
    lab_result_to_fhir,
    measurement_to_fhir,
    operation_outcome,
    patient_to_fhir,
    prescription_to_fhir,
)
from app.modules.imaging.models import ImagingResult
from app.modules.laboratory.models import LabResult
from app.modules.patients.models import Patient
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/fhir", tags=["fhir-r4"])


# ---------------------------------------------------------------------------
# CapabilityStatement (metadata)
# ---------------------------------------------------------------------------

@router.get("/metadata")
def capability_statement(
    current_user: User = Depends(require_permission("fhir.read")),
):
    """CapabilityStatement FHIR — déclare les ressources et opérations supportées."""
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": datetime.utcnow().isoformat(),
        "publisher": "GuinéeCare Hospital Suite",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                            {"code": "create"},
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "identifier", "type": "token"},
                            {"name": "name", "type": "string"},
                            {"name": "family", "type": "string"},
                            {"name": "given", "type": "string"},
                            {"name": "birthdate", "type": "date"},
                        ],
                    },
                    {
                        "type": "Encounter",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "status", "type": "token"},
                        ],
                    },
                    {
                        "type": "Observation",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "category", "type": "token"},
                        ],
                    },
                    {
                        "type": "MedicationRequest",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "status", "type": "token"},
                        ],
                    },
                    {
                        "type": "DiagnosticReport",
                        "interaction": [
                            {"code": "read"},
                            {"code": "search-type"},
                        ],
                        "searchParam": [
                            {"name": "_id", "type": "token"},
                            {"name": "patient", "type": "reference"},
                            {"name": "status", "type": "token"},
                        ],
                    },
                ],
            }
        ],
    }


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------

@router.get("/Patient")
def search_patients(
    _id: str | None = Query(None, alias="_id"),
    identifier: str | None = None,
    name: str | None = None,
    family: str | None = None,
    given: str | None = None,
    birthdate: str | None = None,
    _count: int = Query(50, ge=1, le=200, alias="_count"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Recherche de patients FHIR.

    Paramètres supportés :
    - `_id` : ID interne GuinéeCare.
    - `identifier` : patient_number ou national_id.
    - `name` : recherche full-text sur first_name + last_name.
    - `family` : last_name (préfixe).
    - `given` : first_name (préfixe).
    - `birthdate` : date de naissance (YYYY-MM-DD).
    - `_count` : pagination (défaut 50, max 200).
    """
    query = db.query(Patient).filter(Patient.status != "DELETED")

    if _id:
        query = query.filter(Patient.id == _id)
    if identifier:
        query = query.filter(
            or_(
                Patient.patient_number == identifier,
                Patient.national_id == identifier,
            )
        )
    if name:
        like = f"%{name}%"
        query = query.filter(
            or_(
                Patient.first_name.ilike(like),
                Patient.last_name.ilike(like),
            )
        )
    if family:
        query = query.filter(Patient.last_name.ilike(f"{family}%"))
    if given:
        query = query.filter(Patient.first_name.ilike(f"{given}%"))
    if birthdate:
        try:
            from datetime import date as _date
            d = _date.fromisoformat(birthdate)
            query = query.filter(Patient.date_of_birth == d)
        except ValueError:
            pass

    rows = query.limit(_count).all()
    return bundle([patient_to_fhir(p) for p in rows], total=len(rows))


@router.get("/Patient/{patient_id}")
def read_patient(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Lecture d'un patient par ID."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail=operation_outcome(
            "error", "not-found", f"Patient/{patient_id} introuvable"
        ))
    return patient_to_fhir(patient)


@router.post("/Patient", status_code=201)
def create_patient_fhir(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.write")),
):
    """Création d'un patient via FHIR.

    Le payload doit être une ressource FHIR Patient valide. Les champs mappés :
    - `name[0].family` → last_name
    - `name[0].given[0]` → first_name
    - `gender` → gender (mapping inverse male→M, female→F)
    - `birthDate` → date_of_birth
    - `telecom[?system=phone].value` → phone
    - `address[0].text` → address
    - `identifier[?system=...national-id].value` → national_id
    """
    if payload.get("resourceType") != "Patient":
        raise HTTPException(status_code=400, detail=operation_outcome(
            "error", "invalid", "resourceType doit être 'Patient'"
        ))

    # Mapping inverse
    names = payload.get("name", [])
    family = names[0].get("family", "") if names else ""
    given_list = names[0].get("given", []) if names else []
    first_name = given_list[0] if given_list else ""

    if not family or not first_name:
        raise HTTPException(status_code=400, detail=operation_outcome(
            "error", "required", "name[0].family et name[0].given[0] sont requis"
        ))

    # Génération patient_number
    from datetime import datetime as _dt
    patient_number = f"PAT-{_dt.utcnow().strftime('%Y%m%d%H%M%S')}"

    # Genre
    gender_fhir = payload.get("gender")
    gender_map = {"male": "M", "female": "F", "other": "O", "unknown": "U"}
    gender = gender_map.get(gender_fhir, None)

    # BirthDate
    birth_date = None
    if payload.get("birthDate"):
        try:
            from datetime import date as _date
            birth_date = _date.fromisoformat(payload["birthDate"])
        except ValueError:
            pass

    # Phone
    phone = None
    for telecom in payload.get("telecom", []):
        if telecom.get("system") == "phone":
            phone = telecom.get("value")
            break

    # Address
    address = None
    if payload.get("address"):
        address = payload["address"][0].get("text")

    # National ID
    national_id = None
    for ident in payload.get("identifier", []):
        if "national-id" in (ident.get("system") or ""):
            national_id = ident.get("value")
            break

    # Facility ID (required) — utilise celle du current_user
    facility_id = current_user.facility_id
    if not facility_id:
        raise HTTPException(status_code=400, detail=operation_outcome(
            "error", "required", "L'utilisateur courant doit avoir une facility_id"
        ))

    patient = Patient(
        facility_id=facility_id,
        patient_number=patient_number,
        first_name=first_name,
        last_name=family,
        gender=gender,
        date_of_birth=birth_date,
        phone=phone,
        address=address,
        national_id=national_id,
        status="ACTIVE",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    audit_log(
        db=db, user=current_user, action="fhir.patient.create",
        resource_type="patient", resource_id=patient.id, request=request,
        status_code=201, payload={"via": "fhir", "patient_number": patient_number},
    )

    return patient_to_fhir(patient)


# ---------------------------------------------------------------------------
# Encounter (Admission)
# ---------------------------------------------------------------------------

@router.get("/Encounter")
def search_encounters(
    _id: str | None = Query(None, alias="_id"),
    patient: str | None = None,
    status: str | None = None,
    _count: int = Query(50, ge=1, le=200, alias="_count"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Recherche d'encounters (admissions).

    Statuts FHIR acceptés : planned, in-progress, finished, cancelled.
    Mapping inverse : planned→SCHEDULED, in-progress→ACTIVE, finished→DISCHARGED, cancelled→CANCELLED.
    """
    query = db.query(Admission)
    if _id:
        query = query.filter(Admission.id == _id)
    if patient:
        # patient peut être "Patient/{id}" ou juste "{id}"
        patient_id = patient.split("/")[-1] if "/" in patient else patient
        query = query.filter(Admission.patient_id == patient_id)
    if status:
        status_map = {
            "planned": "SCHEDULED",
            "in-progress": "ACTIVE",
            "finished": "DISCHARGED",
            "cancelled": "CANCELLED",
        }
        internal_status = status_map.get(status)
        if internal_status:
            query = query.filter(Admission.status == internal_status)

    rows = query.limit(_count).all()
    return bundle([admission_to_fhir(a) for a in rows], total=len(rows))


@router.get("/Encounter/{encounter_id}")
def read_encounter(
    encounter_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Lecture d'un encounter par ID."""
    admission = db.query(Admission).filter(Admission.id == encounter_id).first()
    if not admission:
        raise HTTPException(status_code=404, detail=operation_outcome(
            "error", "not-found", f"Encounter/{encounter_id} introuvable"
        ))
    return admission_to_fhir(admission)


# ---------------------------------------------------------------------------
# Observation (constantes + labo)
# ---------------------------------------------------------------------------

@router.get("/Observation")
def search_observations(
    _id: str | None = Query(None, alias="_id"),
    patient: str | None = None,
    category: str | None = None,
    code: str | None = None,
    _count: int = Query(50, ge=1, le=200, alias="_count"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Recherche d'observations (constantes vitales + résultats labo).

    Paramètres :
    - `patient` : Patient/{id} ou {id}
    - `category` : vital-signs | laboratory
    - `code` : code LOINC (ex: 8867-4 pour fréquence cardiaque)
    """
    if category == "laboratory":
        # Résultats labo
        query = db.query(LabResult)
        # LabResult n'a pas de patient_id direct, il faut passer par LabOrder
        from app.modules.laboratory.models import LabOrder
        query = query.join(LabOrder, LabResult.order_id == LabOrder.id)
        if patient:
            patient_id = patient.split("/")[-1] if "/" in patient else patient
            query = query.filter(LabOrder.patient_id == patient_id)
        rows = query.limit(_count).all()
        return bundle(
            [lab_result_to_fhir(r, _get_patient_id_for_lab(r, db)) for r in rows],
            total=len(rows),
        )
    else:
        # Constantes vitales (par défaut si category non spécifié ou =vital-signs)
        query = db.query(PatientMeasurement)
        if patient:
            patient_id = patient.split("/")[-1] if "/" in patient else patient
            query = query.filter(PatientMeasurement.patient_id == patient_id)
        if code:
            # Code LOINC → measurement_type (reverse mapping)
            from app.modules.fhir.conversions import VITAL_LOINC
            for m_type, (loinc_code, _) in VITAL_LOINC.items():
                if loinc_code == code:
                    query = query.filter(PatientMeasurement.measurement_type == m_type)
                    break
        rows = query.limit(_count).all()
        return bundle(
            [measurement_to_fhir(m, m.patient_id) for m in rows],
            total=len(rows),
        )


@router.get("/Observation/{observation_id}")
def read_observation(
    observation_id: str,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Lecture d'une observation par ID.

    Comme les IDs sont partagés entre PatientMeasurement et LabResult, on
    essaie les deux tables. Le paramètre `category` permet de cibler.
    """
    # Essayer d'abord une constante vitale
    if category != "laboratory":
        m = db.query(PatientMeasurement).filter(PatientMeasurement.id == observation_id).first()
        if m:
            return measurement_to_fhir(m, m.patient_id)

    # Puis un résultat labo
    r = db.query(LabResult).filter(LabResult.id == observation_id).first()
    if r:
        return lab_result_to_fhir(r, _get_patient_id_for_lab(r, db))

    raise HTTPException(status_code=404, detail=operation_outcome(
        "error", "not-found", f"Observation/{observation_id} introuvable"
    ))


def _get_patient_id_for_lab(lab_result, db) -> str:
    """Récupère le patient_id depuis le LabOrder parent."""
    from app.modules.laboratory.models import LabOrder
    order = db.query(LabOrder).filter(LabOrder.id == lab_result.order_id).first()
    return order.patient_id if order else ""


# ---------------------------------------------------------------------------
# MedicationRequest (prescriptions)
# ---------------------------------------------------------------------------

@router.get("/MedicationRequest")
def search_medication_requests(
    _id: str | None = Query(None, alias="_id"),
    patient: str | None = None,
    status: str | None = None,
    _count: int = Query(50, ge=1, le=200, alias="_count"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Recherche de prescriptions (ClinicalNote avec note_type=PRESCRIPTION)."""
    query = db.query(ClinicalNote).filter(ClinicalNote.note_type == "PRESCRIPTION")
    if _id:
        query = query.filter(ClinicalNote.id == _id)
    if patient:
        patient_id = patient.split("/")[-1] if "/" in patient else patient
        query = query.filter(ClinicalNote.patient_id == patient_id)
    if status:
        status_map = {
            "active": "ACTIVE",
            "completed": "COMPLETED",
            "cancelled": "CANCELLED",
            "draft": "DRAFT",
        }
        internal = status_map.get(status)
        if internal and hasattr(ClinicalNote, "status"):
            query = query.filter(ClinicalNote.status == internal)

    rows = query.limit(_count).all()
    return bundle(
        [prescription_to_fhir(n, n.patient_id) for n in rows],
        total=len(rows),
    )


@router.get("/MedicationRequest/{med_request_id}")
def read_medication_request(
    med_request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Lecture d'une prescription par ID."""
    note = (
        db.query(ClinicalNote)
        .filter(ClinicalNote.id == med_request_id)
        .filter(ClinicalNote.note_type == "PRESCRIPTION")
        .first()
    )
    if not note:
        raise HTTPException(status_code=404, detail=operation_outcome(
            "error", "not-found", f"MedicationRequest/{med_request_id} introuvable"
        ))
    return prescription_to_fhir(note, note.patient_id)


# ---------------------------------------------------------------------------
# DiagnosticReport (imagerie)
# ---------------------------------------------------------------------------

@router.get("/DiagnosticReport")
def search_diagnostic_reports(
    _id: str | None = Query(None, alias="_id"),
    patient: str | None = None,
    status: str | None = None,
    _count: int = Query(50, ge=1, le=200, alias="_count"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Recherche de comptes rendus d'imagerie."""
    query = db.query(ImagingResult)
    if _id:
        query = query.filter(ImagingResult.id == _id)
    if patient:
        patient_id = patient.split("/")[-1] if "/" in patient else patient
        # ImagingResult a directement un patient_id
        query = query.filter(ImagingResult.patient_id == patient_id)
    if status:
        status_map = {
            "preliminary": "DRAFT",
            "final": "VALIDATED",
            "cancelled": "CANCELLED",
            "amended": "AMENDED",
        }
        internal = status_map.get(status)
        if internal and hasattr(ImagingResult, "status"):
            query = query.filter(ImagingResult.status == internal)

    rows = query.limit(_count).all()
    return bundle(
        [imaging_result_to_fhir(r, r.patient_id) for r in rows],
        total=len(rows),
    )


@router.get("/DiagnosticReport/{report_id}")
def read_diagnostic_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("fhir.read")),
):
    """Lecture d'un compte rendu d'imagerie par ID."""
    result = db.query(ImagingResult).filter(ImagingResult.id == report_id).first()
    if not result:
        raise HTTPException(status_code=404, detail=operation_outcome(
            "error", "not-found", f"DiagnosticReport/{report_id} introuvable"
        ))
    return imaging_result_to_fhir(result, result.patient_id)


def _get_patient_id_for_imaging(imaging_result, db) -> str:
    """Récupère le patient_id depuis le ImagingOrder parent."""
    from app.modules.imaging.models import ImagingOrder
    order = db.query(ImagingOrder).filter(ImagingOrder.id == imaging_result.order_id).first()
    return order.patient_id if order else ""
