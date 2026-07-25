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
    # v2.8.0 — Audit log pour traçabilité médico-légale
    audit_log(
        db=db,
        action="maternity.delivery.create",
        user=current_user,
        resource_type="delivery",
        resource_id=str(row.id),
        request=None,  # pas de Request dans cette fonction
        status_code=200,
    )
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


# ============================================================================
# v2.6.0 — Phase 7 : Alertes grossesse à risque automatiques
# ============================================================================

def _parse_bp(bp_str: str | None) -> tuple[int | None, int | None]:
    """Parser une tension artérielle '120/80' → (120, 80). None si invalide."""
    if not bp_str:
        return None, None
    try:
        parts = bp_str.replace(" ", "").split("/")
        if len(parts) == 2:
            return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        pass
    return None, None


def _evaluate_pregnancy_risks(consultations: list) -> list[dict]:
    """Évaluer les risques grossesse à partir des consultations prénatales.

    Règles (OMS / OMS-Afrique) :
    - HTA gravidique : PA systolique ≥ 140 OU diastolique ≥ 90
    - HTA sévère : PA systolique ≥ 160 OU diastolique ≥ 110
    - Prééclampsie suspectée : HTA + œdèmes (à étendre)
    - Poids faible : < 45 kg ou perte > 2 kg en 2 semaines
    - Anémie suspectée : pâleur conjonctive (texte libre)

    Retourne une liste d'alertes {consultation_id, type, severity, message}.
    """
    alerts = []
    for c in consultations:
        if not hasattr(c, "id"):
            continue

        # Analyse tension artérielle
        systolic, diastolic = _parse_bp(getattr(c, "blood_pressure", None))
        if systolic and diastolic:
            if systolic >= 160 or diastolic >= 110:
                alerts.append({
                    "consultation_id": str(c.id),
                    "type": "HYPERTENSION_SEVERE",
                    "severity": "CRITICAL",
                    "message": f"HTA sévère détectée : {systolic}/{diastolic} mmHg — risque de prééclampsie/éclampsie. Évacuation sanitaire recommandée.",
                })
            elif systolic >= 140 or diastolic >= 90:
                alerts.append({
                    "consultation_id": str(c.id),
                    "type": "HYPERTENSION_GRAVIDIQUE",
                    "severity": "HIGH",
                    "message": f"HTA gravidique : {systolic}/{diastolic} mmHg — surveillance rapprochée requise.",
                })

        # Analyse poids
        weight = getattr(c, "weight_kg", None)
        if weight and weight < 45:
            alerts.append({
                "consultation_id": str(c.id),
                "type": "LOW_WEIGHT",
                "severity": "MEDIUM",
                "message": f"Poids faible : {weight} kg — risque nutritionnel. Supplémentation recommandée.",
            })

    return alerts


@router.get("/alerts")
def maternity_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("maternity.read")),
):
    """Alertes grossesse à risque — détection automatique.

    Scanne toutes les consultations prénatales des grossesses actives et
    détecte les risques selon les seuils OMS :
    - HTA sévère (systolic ≥ 160 ou diastolic ≥ 110) → CRITICAL
    - HTA gravidique (systolic ≥ 140 ou diastolic ≥ 90) → HIGH
    - Poids faible (< 45 kg) → MEDIUM

    Retourne :
    - alerts : liste des alertes détectées
    - alerts_count : nombre total
    - critical_count / high_count / medium_count : répartition par sévérité
    - by_facility : répartition par établissement
    """
    # Récupérer toutes les consultations prénatales (consultation_type = PRENATAL)
    # pour les grossesses actives
    consultations = (
        tenant_query(db, MaternityConsultation, current_user)
        .filter(MaternityConsultation.consultation_type == "PRENATAL")
        .all()
    )

    # Évaluer les risques
    alerts = _evaluate_pregnancy_risks(consultations)

    # Enrichir avec facility_id + patient_id (via MaternityRecord parent)
    # MaternityConsultation n'a pas patient_id directement — il faut passer
    # par le MaternityRecord parent.
    record_ids = list({c.record_id for c in consultations})
    records = (
        db.query(MaternityRecord)
        .filter(MaternityRecord.id.in_(record_ids))
        .all()
        if record_ids else []
    )
    record_map = {r.id: r for r in records}

    for alert in alerts:
        consult = next((c for c in consultations if str(c.id) == alert["consultation_id"]), None)
        if consult:
            alert["facility_id"] = str(consult.facility_id)
            record = record_map.get(consult.record_id)
            alert["patient_id"] = str(record.patient_id) if record else None
            alert["consultation_date"] = consult.consulted_at.isoformat() if consult.consulted_at else None

    # Compteurs par sévérité
    critical_count = sum(1 for a in alerts if a["severity"] == "CRITICAL")
    high_count = sum(1 for a in alerts if a["severity"] == "HIGH")
    medium_count = sum(1 for a in alerts if a["severity"] == "MEDIUM")

    # Répartition par établissement
    by_facility_map: dict[str, int] = {}
    for a in alerts:
        fid = a.get("facility_id", "unknown")
        by_facility_map[fid] = by_facility_map.get(fid, 0) + 1
    by_facility = [{"facility_id": k, "alerts_count": v} for k, v in by_facility_map.items()]

    return {
        "data": {
            "alerts": alerts,
            "alerts_count": len(alerts),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "by_facility": by_facility,
        },
        "message": "pregnancy risk alerts",
    }
