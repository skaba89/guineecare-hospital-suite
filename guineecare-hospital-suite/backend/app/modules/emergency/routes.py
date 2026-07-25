from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.emergency.models import EmergencyVisit
from app.modules.emergency.schemas import (
    EmergencyCareUpdate,
    EmergencyDischargeUpdate,
    EmergencyOrientationUpdate,
    EmergencyTriageUpdate,
    EmergencyVisitCreate,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.get("/queue")
def get_emergency_queue(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.read")),
):
    query = tenant_query(db, EmergencyVisit, current_user).filter(EmergencyVisit.status.notin_(["ORIENTED", "DISCHARGED"])).order_by(EmergencyVisit.arrived_at.asc())
    if pagination.search:
        query = query.filter(
            (EmergencyVisit.chief_complaint.ilike(f"%{pagination.search}%"))
            | (EmergencyVisit.priority_level.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/visits")
def create_emergency_visit(
    payload: EmergencyVisitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.create")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = EmergencyVisit(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "emergency visit created"}


@router.post("/visits/{visit_id}/triage")
def triage_visit(
    visit_id: str,
    payload: EmergencyTriageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.triage")),
):
    row = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    enforce_facility_access(current_user, row.facility_id)
    row.priority_level = payload.priority_level
    row.status = "TRIAGED"
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "triage saved"}


@router.post("/visits/{visit_id}/orientation")
def orient_visit(
    visit_id: str,
    payload: EmergencyOrientationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.orient")),
):
    row = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    enforce_facility_access(current_user, row.facility_id)
    row.orientation = payload.orientation
    row.status = "ORIENTED"
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "orientation saved"}


@router.post("/visits/{visit_id}/care")
def care_visit(
    visit_id: str,
    payload: EmergencyCareUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.care")),
):
    """Prise en charge médicale — transition TRIAGED → IN_CARE"""
    row = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    enforce_facility_access(current_user, row.facility_id)
    if row.status not in ("TRIAGED", "WAITING"):
        raise HTTPException(status_code=409, detail="Visit cannot be taken in care from current status")
    row.status = "IN_CARE"
    row.attending_doctor_id = payload.attending_doctor_id
    if payload.vital_signs:
        row.vital_signs = payload.vital_signs
    if payload.treatment_notes:
        row.treatment_notes = payload.treatment_notes
    row.seen_at = utcnow()
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "patient taken in care"}


@router.post("/visits/{visit_id}/discharge")
def discharge_visit(
    visit_id: str,
    payload: EmergencyDischargeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.discharge")),
):
    """Sortie des urgences — transition IN_CARE → DISCHARGED"""
    row = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Emergency visit not found")
    enforce_facility_access(current_user, row.facility_id)
    if row.status != "IN_CARE":
        raise HTTPException(status_code=409, detail="Only patients in care can be discharged")
    row.status = "DISCHARGED"
    row.discharge_summary = payload.discharge_summary
    row.discharge_destination = payload.discharge_destination
    if payload.orientation:
        row.orientation = payload.orientation
    row.discharged_at = utcnow()
    row.updated_at = utcnow()
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "patient discharged from emergency"}


# ============================================================================
# v2.4.0 — Phase 4 : Indicateurs temps d'attente + Transfert hospitalisation
# ============================================================================

@router.get("/indicators")
def emergency_indicators(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.read")),
):
    """Indicateurs urgences — temps d'attente et flux patients.

    Retourne :
    - avg_time_to_triage_min : temps moyen arrivée → triage (visites triées < 24h)
    - avg_time_to_care_min : temps moyen arrivée → prise en charge médecin
    - avg_time_to_discharge_min : temps moyen arrivée → sortie
    - count_by_status : {WAITING, TRIAGED, IN_CARE, DISCHARGED}
    - count_by_priority : {P1, P2, P3, P4, P5, NORMAL, URGENT}
    - current_waiting : patients actuellement en attente (WAITING ou TRIAGED)
    - total_today : visites arrivées aujourd'hui
    """
    from sqlalchemy import func

    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Visites du jour
    today_visits = (
        tenant_query(db, EmergencyVisit, current_user)
        .filter(EmergencyVisit.arrived_at >= today_start)
        .all()
    )

    # v2.8.1 — FIX : avg_to_triage calculé séparément de avg_to_care.
    # Le triage = temps entre arrivée et la première action (orientation ou
    # passage en IN_CARE). On utilise updated_at comme proxy du moment du triage
    # car il n'y a pas de colonne triaged_at dédiée.
    # avg_to_care = temps entre arrivée et seen_at (prise en charge médecin).

    # Temps moyen arrivée → triage (visites qui ont été triées = statut >= TRIAGED)
    # On utilise updated_at comme proxy du moment du triage.
    triaged_visits = [
        v for v in today_visits
        if v.status not in ("WAITING",) and v.arrived_at and v.updated_at
    ]
    if triaged_visits:
        avg_to_triage = sum(
            (v.updated_at - v.arrived_at).total_seconds()
            for v in triaged_visits
            if v.updated_at and v.arrived_at
        ) / len(triaged_visits) / 60.0  # minutes
    else:
        avg_to_triage = 0.0

    # Temps moyen arrivée → prise en charge médecin (seen_at)
    cared_visits = [v for v in today_visits if v.seen_at and v.arrived_at]
    if cared_visits:
        avg_to_care = sum(
            (v.seen_at - v.arrived_at).total_seconds()
            for v in cared_visits
            if v.seen_at and v.arrived_at
        ) / len(cared_visits) / 60.0  # minutes
    else:
        avg_to_care = 0.0

    # Temps moyen arrivée → sortie (visites discharged_at)
    discharged_visits = [v for v in today_visits if v.discharged_at and v.arrived_at]
    if discharged_visits:
        avg_to_discharge = sum(
            (v.discharged_at - v.arrived_at).total_seconds()
            for v in discharged_visits
            if v.discharged_at and v.arrived_at
        ) / len(discharged_visits) / 60.0
    else:
        avg_to_discharge = 0.0

    # Comptage par statut
    status_counts = {}
    priority_counts = {}
    for v in today_visits:
        status_counts[v.status] = status_counts.get(v.status, 0) + 1
        priority_counts[v.priority_level] = priority_counts.get(v.priority_level, 0) + 1

    # Patients actuellement en attente
    current_waiting = [
        v for v in today_visits
        if v.status in ("WAITING", "TRIAGED")
    ]

    return {
        "data": {
            "avg_time_to_triage_min": round(avg_to_triage, 1),
            "avg_time_to_care_min": round(avg_to_care, 1),
            "avg_time_to_discharge_min": round(avg_to_discharge, 1),
            "count_by_status": status_counts,
            "count_by_priority": priority_counts,
            "current_waiting_count": len(current_waiting),
            "total_today": len(today_visits),
            "period": "today",
            "generated_at": now.isoformat(),
        },
        "message": "emergency indicators",
    }


@router.post("/visits/{visit_id}/hospitalize")
def transfer_to_hospitalization(
    visit_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("emergency.write")),
):
    """Transfert d'un patient des urgences vers l'hospitalisation.

    Body JSON:
    {
      "room_id": "...",          // optionnel — sinon auto-assigne un lit AVAILABLE
      "bed_id": "...",           // optionnel
      "attending_doctor_id": "...",  // optionnel
      "reason": "Surveillance post-urgences"
    }

    Actions :
    1. Vérifie que la visite a le statut IN_CARE
    2. Crée une admission de type HOSPITALIZATION
    3. Crée un HospitalStay (lit occupé)
    4. Clôture la visite urgence (status=DISCHARGED, destination=HOSPITALIZATION)
    """
    visit = db.query(EmergencyVisit).filter(EmergencyVisit.id == visit_id).first()
    if not visit:
        raise HTTPException(status_code=404, detail="Visite urgence introuvable")
    enforce_facility_access(current_user, visit.facility_id)

    if visit.status not in ("IN_CARE", "TRIAGED"):
        raise HTTPException(
            status_code=409,
            detail=f"Transfert impossible — statut actuel: {visit.status}. "
                   "Doit être IN_CARE ou TRIAGED.",
        )

    # 1. Créer une admission de type HOSPITALIZATION
    from app.modules.admissions.models import Admission
    admission = Admission(
        facility_id=visit.facility_id,
        patient_id=visit.patient_id,
        admission_type="HOSPITALIZATION",
        status="ACTIVE",
        admitted_at=utcnow(),
    )
    db.add(admission)
    db.flush()  # pour avoir l'ID

    # 2. Créer un HospitalStay si bed_id fourni
    bed_id = (payload or {}).get("bed_id")
    if bed_id:
        from app.modules.hospitalization.models import Bed, HospitalStay
        bed = db.query(Bed).filter(Bed.id == bed_id).first()
        if not bed:
            raise HTTPException(status_code=404, detail="Lit introuvable")
        enforce_facility_access(current_user, bed.facility_id)
        # v2.8.0 — P0-6 fix : vérifier que le lit appartient au MÊME établissement
        # que la visite urgence (cross-tenant safety)
        if bed.facility_id != visit.facility_id:
            raise HTTPException(
                status_code=403,
                detail="Le lit doit appartenir au même établissement que la visite urgence",
            )
        if bed.bed_status != "AVAILABLE":
            raise HTTPException(
                status_code=409,
                detail=f"Lit non disponible — statut actuel: {bed.bed_status}",
            )
        stay = HospitalStay(
            facility_id=visit.facility_id,
            patient_id=visit.patient_id,
            admission_id=admission.id,
            bed_id=bed_id,
            status="ACTIVE",
            admitted_at=utcnow(),
        )
        db.add(stay)
        bed.bed_status = "OCCUPIED"

    # 3. Clôturer la visite urgence
    visit.status = "DISCHARGED"
    visit.discharge_destination = "HOSPITALIZATION"
    visit.discharged_at = utcnow()
    visit.discharge_summary = (payload or {}).get("reason", "Transfert vers hospitalisation")
    visit.admission_id = admission.id

    db.commit()
    db.refresh(visit)
    db.refresh(admission)

    return {
        "data": {
            "visit_id": str(visit.id),
            "visit_status": visit.status,
            "admission_id": str(admission.id),
            "admission_type": admission.admission_type,
            "bed_id": bed_id,
            "transferred_at": utcnow().isoformat(),
            "transferred_by": str(current_user.id),
        },
        "message": "Patient transféré vers hospitalisation",
    }
