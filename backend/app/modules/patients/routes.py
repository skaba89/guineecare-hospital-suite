from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.audit.service import audit_log
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.patients.models import Patient
from app.modules.patients.schemas import PatientCreate
# v2.4.0 — Phase 4 : imports pour l'historique agrégé du patient
from app.modules.admissions.models import Admission
from app.modules.clinical.models import ClinicalNote, PatientMeasurement
from app.modules.laboratory.models import LabOrder
from app.modules.billing.models import Invoice
from app.modules.imaging.models import ImagingOrder

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def list_patients(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.read")),
):
    query = tenant_query(db, Patient, current_user).order_by(Patient.created_at.desc())
    # P1 fix v2.2.0 : exclure les patients soft-deleted (status=DELETED)
    query = query.filter(Patient.status != "DELETED")
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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.read")),
):
    """Lecture d'un dossier patient.

    Sécurité (v2.2.0) :
    - `enforce_facility_access` empêche la lecture cross-tenant (déjà en place).
    - `audit_log` trace l'accès au dossier patient (PHI access log) — nouvelle
      obligation conformité données médicales Guinée.
    """
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    enforce_facility_access(current_user, row.facility_id)
    # P1 fix v2.2.0 : tracer l'accès au dossier patient (PHI access log)
    audit_log(
        db=db,
        action="patient.read",
        user=current_user,
        resource_type="patient",
        resource_id=str(row.id),
        request=request,
        status_code=200,
        facility_id=row.facility_id,
    )
    # v2.8.3 — P2-3 : masquer les données médicales sensibles pour les rôles
    # non-cliniques (PHARMACIST, LAB_TECH, CASHIER ne doivent pas voir blood_type,
    # allergies, medical_history, current_medication, chronic_conditions).
    # Seuls SUPER_ADMIN, ADMIN, DOCTOR, NURSE, MIDWIFE ont accès aux champs médicaux.
    CLINICAL_ROLES = {"SUPER_ADMIN", "ADMIN", "DOCTOR", "NURSE", "MIDWIFE"}
    if current_user.role not in CLINICAL_ROLES:
        # Masquer les champs médicaux sensibles
        patient_data = {
            "id": str(row.id),
            "facility_id": row.facility_id,
            "patient_number": row.patient_number,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "gender": row.gender,
            "date_of_birth": row.date_of_birth.isoformat() if row.date_of_birth else None,
            "phone": row.phone,
            "address": row.address,
            "status": row.status,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            # Champs médicaux masqués (non inclus pour PHARMACIST/LAB_TECH/CASHIER)
            "blood_type": "[RESTREINT]",
            "allergies": "[RESTREINT]",
            "medical_history": "[RESTREINT]",
            "current_medication": "[RESTREINT]",
            "chronic_conditions": "[RESTREINT]",
        }
    else:
        patient_data = row

    return {"data": patient_data, "message": "patient detail"}


# ============================================================================
# v2.4.0 — Phase 4 : Historique patient agrégé (timeline)
# ============================================================================

@router.get("/{patient_id}/history")
def get_patient_history(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.read")),
):
    """Historique agrégé du patient — timeline chronologique.

    Retourne dans une seule réponse les événements clés du parcours patient :
    - Admissions (consultations, hospitalisations, urgences)
    - Notes cliniques (consultations, prescriptions, observations)
    - Mesures (constantes vitales)
    - Demandes laboratoire
    - Demandes imagerie
    - Factures

    Sécurité (v2.4.0) :
    - `enforce_facility_access` vérifie que le patient appartient à
      l'établissement de l'utilisateur.
    - `audit_log` trace l'accès à l'historique (PHI access log).

    Utilisé par la page Dossier Patient pour afficher une timeline unifiée.
    """
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    enforce_facility_access(current_user, row.facility_id)
    audit_log(
        db=db,
        action="patient.history.read",
        user=current_user,
        resource_type="patient",
        resource_id=str(row.id),
        request=request,
        status_code=200,
        facility_id=row.facility_id,
    )

    # v2.8.9 — perf : limiter à 50 events max par type pour éviter de tout charger
    # + utiliser .limit() sur chaque requête
    events: list[dict] = []

    # Admissions (limit 50)
    for adm in db.query(Admission).filter(Admission.patient_id == patient_id).order_by(Admission.admitted_at.desc()).limit(50).all():
        events.append({
            "type": "admission",
            "date": adm.admitted_at.isoformat() if getattr(adm, "admitted_at", None) else None,
            "summary": f"Admission ({getattr(adm, 'admission_type', '—')}) — {getattr(adm, 'status', '—')}",
            "data": {
                "id": str(adm.id),
                "type": getattr(adm, "admission_type", None),
                "status": getattr(adm, "status", None),
                "department_id": getattr(adm, "department_id", None),
                "admitted_at": adm.admitted_at.isoformat() if getattr(adm, "admitted_at", None) else None,
            },
        })

    # Notes cliniques (limit 50)
    for note in db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id).order_by(ClinicalNote.created_at.desc()).limit(50).all():
        note_type = getattr(note, "note_type", "NOTE")
        events.append({
            "type": "clinical_note",
            "date": note.created_at.isoformat() if getattr(note, "created_at", None) else None,
            "summary": f"{note_type} — {(getattr(note, 'content', '') or '')[:80]}",
            "data": {
                "id": str(note.id),
                "note_type": note_type,
                "content": getattr(note, "content", None),
                "created_by": getattr(note, "created_by", None),
                "created_at": note.created_at.isoformat() if getattr(note, "created_at", None) else None,
            },
        })

    # Mesures (limit 50)
    for m in db.query(PatientMeasurement).filter(PatientMeasurement.patient_id == patient_id).order_by(PatientMeasurement.recorded_at.desc()).limit(50).all():
        events.append({
            "type": "measurement",
            "date": m.recorded_at.isoformat() if getattr(m, "recorded_at", None) else None,
            "summary": f"{getattr(m, 'measurement_type', '—')}: {getattr(m, 'value', '—')} {getattr(m, 'unit', '') or ''}".strip(),
            "data": {
                "id": str(m.id),
                "measurement_type": getattr(m, "measurement_type", None),
                "value": getattr(m, "value", None),
                "unit": getattr(m, "unit", None),
            },
        })

    # Demandes laboratoire (limit 50)
    for lab in db.query(LabOrder).filter(LabOrder.patient_id == patient_id).order_by(LabOrder.ordered_at.desc()).limit(50).all():
        events.append({
            "type": "lab_order",
            "date": lab.ordered_at.isoformat() if getattr(lab, "ordered_at", None) else None,
            "summary": f"Labo — {getattr(lab, 'status', '—')}",
            "data": {
                "id": str(lab.id),
                "test_id": getattr(lab, "test_id", None),
                "priority": getattr(lab, "priority", None),
                "status": getattr(lab, "status", None),
            },
        })

    # Demandes imagerie (limit 50)
    for img in db.query(ImagingOrder).filter(ImagingOrder.patient_id == patient_id).order_by(ImagingOrder.ordered_at.desc()).limit(50).all():
        events.append({
            "type": "imaging_order",
            "date": img.ordered_at.isoformat() if getattr(img, "ordered_at", None) else None,
            "summary": f"Imagerie ({getattr(img, 'exam_type', '—')}) — {getattr(img, 'status', '—')}",
            "data": {
                "id": str(img.id),
                "exam_type": getattr(img, "exam_type", None),
                "body_region": getattr(img, "body_region", None),
                "status": getattr(img, "status", None),
                "ordered_at": img.ordered_at.isoformat() if getattr(img, "ordered_at", None) else None,
            },
        })

    # Factures
    for inv in db.query(Invoice).filter(Invoice.patient_id == patient_id).all():
        events.append({
            "type": "invoice",
            "date": inv.created_at.isoformat() if getattr(inv, "created_at", None) else None,
            "summary": f"Facture {getattr(inv, 'invoice_number', '—')} — {getattr(inv, 'status', '—')} ({getattr(inv, 'net_amount', 0)} GNF)",
            "data": {
                "id": str(inv.id),
                "invoice_number": getattr(inv, "invoice_number", None),
                "net_amount": getattr(inv, "net_amount", 0),
                "paid_amount": getattr(inv, "paid_amount", 0),
                "balance_due": getattr(inv, "balance_due", 0),
                "status": getattr(inv, "status", None),
                "created_at": inv.created_at.isoformat() if getattr(inv, "created_at", None) else None,
            },
        })

    # Tri chronologique descendant (plus récent en premier)
    events.sort(key=lambda e: e["date"] or "", reverse=True)

    return {
        "data": {
            "patient_id": str(row.id),
            "patient_name": f"{row.first_name} {row.last_name}",
            "patient_number": row.patient_number,
            "total_events": len(events),
        },
        "events": events,
        "message": "patient history timeline",
    }


# ============================================================================
# v2.8.3 — P2-1 : Endpoint lookup léger pour dropdowns (privacy + perf)
# ============================================================================

@router.get("/lookup/light")
def patients_lookup_light(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.read")),
):
    """Lookup léger — retourne uniquement {id, name, patient_number}.

    v2.8.3 — P2-1 : Cet endpoint remplace l'usage de /patients?page_size=1000
    par useLookupData. Avant : le frontend chargeait TOUS les patients (avec
    téléphone, adresse, données médicales) dans le navigateur pour alimenter
    les dropdowns. Problème : privacy (PHI en mémoire browser) + perf
    (10k+ patients = payload énorme).

    Maintenant : seules les informations minimales sont retournées (id, nom,
    patient_number) — pas de PHI. Le frontend utilise cet endpoint pour les
    dropdowns/selects.

    Sécurité :
    - permission patient.read requise
    - tenant_query filtre par facility_id
    - Maximum 500 résultats (suffisant pour dropdowns)
    - Tri alphabétique par nom
    """
    query = tenant_query(db, Patient, current_user).filter(Patient.status != "DELETED")
    query = query.order_by(Patient.last_name.asc(), Patient.first_name.asc())
    rows = query.limit(500).all()
    return {
        "data": [
            {
                "id": str(r.id),
                "label": f"{r.last_name} {r.first_name}".strip(),
                "patient_number": r.patient_number,
            }
            for r in rows
        ],
        "total": len(rows),
    }


# ============================================================================
# v2.8.4 — Droits patients : rectification, effacement, export (RGPD-like)
# ============================================================================

@router.put("/{patient_id}")
def update_patient(
    patient_id: str,
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.create")),
):
    """Rectification d'un dossier patient (droit de rectification).

    Permet de corriger les informations démographiques et médicales.
    Tous les champs sont optionnels — seuls les champs fournis sont mis à jour.

    Sécurité :
    - permission patient.create requise (ADMIN, DOCTOR, SUPER_ADMIN)
    - enforce_facility_access
    - audit_log trace la modification
    """
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    enforce_facility_access(current_user, row.facility_id)

    # Champs autorisés à la modification
    ALLOWED_FIELDS = {
        "first_name", "last_name", "gender", "date_of_birth", "phone",
        "address", "national_id", "insurance_number",
        "blood_type", "allergies", "medical_history",
        "current_medication", "chronic_conditions",
        "emergency_contact_name", "emergency_contact_phone",
    }

    changes = {}
    for key, value in payload.items():
        if key in ALLOWED_FIELDS and value is not None:
            old_value = getattr(row, key, None)
            if str(old_value) != str(value):
                changes[key] = {"old": str(old_value), "new": str(value)}
                setattr(row, key, value)

    if not changes:
        return {"message": "Aucune modification à appliquer", "data": {"id": str(row.id)}}

    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        action="patient.update",
        user=current_user,
        resource_type="patient",
        resource_id=str(row.id),
        request=request,
        status_code=200,
        facility_id=row.facility_id,
        payload={"changes": changes},
    )

    return {"data": row, "message": "Patient mis à jour"}


@router.delete("/{patient_id}")
def delete_patient(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.create")),
):
    """Effacement d'un dossier patient (droit à l'effacement).

    v2.8.4 — Implémente le droit à l'effacement RGPD-like.
    Effectue un soft-delete : status → "DELETED" + anonymisation des champs
    sensibles (nom, téléphone, adresse, données médicales).

    Les données restent en DB pour l'audit médical mais sont anonymisées.
    Le patient n'apparaît plus dans les listes (filtre status != DELETED).

    Sécurité :
    - permission patient.create requise
    - enforce_facility_access
    - audit_log trace l'effacement
    """
    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    enforce_facility_access(current_user, row.facility_id)

    if row.status == "DELETED":
        raise HTTPException(status_code=409, detail="Patient déjà supprimé")

    # Anonymisation
    row.status = "DELETED"
    row.first_name = "[SUPPRIMÉ]"
    row.last_name = "[SUPPRIMÉ]"
    row.phone = None
    row.address = None
    row.national_id = None
    row.insurance_number = None
    row.blood_type = "NON_RENSEIGNE"
    row.allergies = "[SUPPRIMÉ]"
    row.medical_history = "[SUPPRIMÉ]"
    row.current_medication = "[SUPPRIMÉ]"
    row.chronic_conditions = "[SUPPRIMÉ]"

    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        action="patient.delete",
        user=current_user,
        resource_type="patient",
        resource_id=str(row.id),
        request=request,
        status_code=200,
        facility_id=row.facility_id,
    )

    return {"message": "Patient supprimé (données anonymisées)", "data": {"id": str(row.id), "status": "DELETED"}}


@router.get("/{patient_id}/export")
def export_patient_data(
    patient_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("patient.read")),
):
    """Export des données patient (droit à la portabilité).

    v2.8.4 — Retourne toutes les données du patient au format JSON
    pour permettre l'export vers un autre système (droit à la portabilité).

    Inclut : démographie, admissions, notes cliniques, mesures, labos,
    imagerie, factures, prescriptions.

    Sécurité :
    - permission patient.read requise
    - enforce_facility_access
    - audit_log trace l'export
    """
    from app.modules.admissions.models import Admission
    from app.modules.clinical.models import ClinicalNote, PatientMeasurement
    from app.modules.laboratory.models import LabOrder
    from app.modules.billing.models import Invoice
    from app.modules.imaging.models import ImagingOrder

    row = db.query(Patient).filter(Patient.id == patient_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    enforce_facility_access(current_user, row.facility_id)

    audit_log(
        db=db,
        action="patient.export",
        user=current_user,
        resource_type="patient",
        resource_id=str(row.id),
        request=request,
        status_code=200,
        facility_id=row.facility_id,
    )

    export_data = {
        "patient": {
            "id": str(row.id),
            "patient_number": row.patient_number,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "gender": row.gender,
            "date_of_birth": row.date_of_birth.isoformat() if row.date_of_birth else None,
            "phone": row.phone,
            "address": row.address,
            "blood_type": row.blood_type,
            "allergies": row.allergies,
            "medical_history": row.medical_history,
            "current_medication": row.current_medication,
            "chronic_conditions": row.chronic_conditions,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        },
        "admissions": [
            {
                "id": str(a.id),
                "type": a.admission_type,
                "status": a.status,
                "admitted_at": a.admitted_at.isoformat() if a.admitted_at else None,
                "closed_at": a.closed_at.isoformat() if getattr(a, "closed_at", None) else None,
            }
            for a in db.query(Admission).filter(Admission.patient_id == patient_id).all()
        ],
        "clinical_notes": [
            {
                "id": str(n.id),
                "note_type": n.note_type,
                "content": n.content,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in db.query(ClinicalNote).filter(ClinicalNote.patient_id == patient_id).all()
        ],
        "measurements": [
            {
                "id": str(m.id),
                "type": m.measurement_type,
                "value": m.value,
                "unit": m.unit,
                "recorded_at": m.recorded_at.isoformat() if m.recorded_at else None,
            }
            for m in db.query(PatientMeasurement).filter(PatientMeasurement.patient_id == patient_id).all()
        ],
        "lab_orders": [
            {
                "id": str(l.id),
                "status": l.status,
                "priority": l.priority,
                "ordered_at": l.ordered_at.isoformat() if l.ordered_at else None,
            }
            for l in db.query(LabOrder).filter(LabOrder.patient_id == patient_id).all()
        ],
        "invoices": [
            {
                "id": str(i.id),
                "invoice_number": i.invoice_number,
                "net_amount": i.net_amount,
                "paid_amount": i.paid_amount,
                "balance_due": i.balance_due,
                "status": i.status,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in db.query(Invoice).filter(Invoice.patient_id == patient_id).all()
        ],
        "exported_at": utcnow().isoformat(),
        "exported_by": str(current_user.id),
    }

    return {"data": export_data, "message": "patient data export (portability)"}
