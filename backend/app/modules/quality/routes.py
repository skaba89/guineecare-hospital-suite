from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.quality.models import IncidentReport, QualityIndicator, QualityMeasurement
from app.modules.quality.schemas import (
    IncidentReportCreate,
    QualityIndicatorCreate,
    QualityMeasurementCreate,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/quality", tags=["quality"])


# ── Quality Indicators ────────────────────────────────────────────────

@router.get("/indicators")
def list_indicators(
    facility_id: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.read")),
):
    query = db.query(QualityIndicator)
    if facility_id:
        query = query.filter(QualityIndicator.facility_id == facility_id)
    if category:
        query = query.filter(QualityIndicator.category == category)
    rows = query.order_by(QualityIndicator.code).all()
    return {"data": rows, "message": "indicators list"}


@router.post("/indicators")
def create_indicator(
    payload: QualityIndicatorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    row = QualityIndicator(**payload.model_dump(exclude_none=True))
    if not row.facility_id:
        row.facility_id = current_user.facility_id
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="quality.indicator_created",
        entity_type="quality_indicator",
        entity_id=row.id,
        level="NORMAL",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "indicator created"}


# ── Quality Measurements ──────────────────────────────────────────────

@router.get("/measurements")
def list_measurements(
    indicator_id: str | None = None,
    facility_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.read")),
):
    query = db.query(QualityMeasurement)
    if indicator_id:
        query = query.filter(QualityMeasurement.indicator_id == indicator_id)
    if facility_id:
        query = query.filter(QualityMeasurement.facility_id == facility_id)
    rows = query.order_by(QualityMeasurement.period_start.desc()).all()
    return {"data": rows, "message": "measurements list"}


@router.post("/measurements")
def create_measurement(
    payload: QualityMeasurementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    indicator = db.query(QualityIndicator).filter(QualityIndicator.id == payload.indicator_id).first()
    if not indicator:
        raise HTTPException(status_code=404, detail="Indicator not found")
    row = QualityMeasurement(**payload.model_dump(exclude_none=True))
    if not row.facility_id:
        row.facility_id = current_user.facility_id
    if not row.recorded_by:
        row.recorded_by = current_user.id
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="quality.measurement_recorded",
        entity_type="quality_measurement",
        entity_id=row.id,
        level="NORMAL",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "measurement recorded"}


# ── Incident Reports ──────────────────────────────────────────────────

@router.get("/incidents")
def list_incidents(
    facility_id: str | None = None,
    status: str | None = None,
    severity: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.read")),
):
    query = db.query(IncidentReport)
    if facility_id:
        query = query.filter(IncidentReport.facility_id == facility_id)
    if status:
        query = query.filter(IncidentReport.status == status)
    if severity:
        query = query.filter(IncidentReport.severity == severity)
    rows = query.order_by(IncidentReport.incident_date.desc()).all()
    return {"data": rows, "message": "incidents list"}


@router.post("/incidents")
def create_incident(
    payload: IncidentReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    row = IncidentReport(**payload.model_dump(exclude_none=True))
    if not row.facility_id:
        row.facility_id = current_user.facility_id
    if not row.reported_by:
        row.reported_by = current_user.id
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="quality.incident_reported",
        entity_type="incident_report",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "incident reported"}


@router.post("/incidents/{incident_id}/investigate")
def investigate_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")

    incident.status = "UNDER_INVESTIGATION"
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="quality.incident_under_investigation",
        entity_type="incident_report",
        entity_id=incident.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(incident)
    return {"data": incident, "message": "incident under investigation"}


@router.post("/incidents/{incident_id}/resolve")
def resolve_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("quality.manage")),
):
    incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident report not found")

    incident.status = "RESOLVED"
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="quality.incident_resolved",
        entity_type="incident_report",
        entity_id=incident.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(incident)
    return {"data": incident, "message": "incident resolved"}
