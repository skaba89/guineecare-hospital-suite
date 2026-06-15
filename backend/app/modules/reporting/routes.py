from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.reporting.models import EpidemicAlert, HealthStatistic, NationalReport
from app.modules.reporting.schemas import (
    EpidemicAlertCreate,
    HealthStatisticCreate,
    NationalReportCreate,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/reporting", tags=["reporting"])


# ── National Reports ──────────────────────────────────────────────────

@router.get("/national-reports")
def list_national_reports(
    facility_id: str | None = None,
    status: str | None = None,
    report_type: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.read")),
):
    query = tenant_query(db, NationalReport, current_user)
    if facility_id:
        query = query.filter(NationalReport.facility_id == facility_id)
    if status:
        query = query.filter(NationalReport.status == status)
    if report_type:
        query = query.filter(NationalReport.report_type == report_type)
    rows = query.order_by(NationalReport.created_at.desc()).all()
    return {"data": rows, "message": "national reports list"}


@router.post("/national-reports")
def create_national_report(
    payload: NationalReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.manage")),
):
    row = NationalReport(**payload.model_dump(exclude_none=True))
    if not row.facility_id:
        row.facility_id = current_user.facility_id
    enforce_facility_access(current_user, row.facility_id)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="reporting.national_report_created",
        entity_type="national_report",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "national report created"}


@router.post("/national-reports/{report_id}/submit")
def submit_national_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.manage")),
):
    report = db.query(NationalReport).filter(NationalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="National report not found")
    enforce_facility_access(current_user, report.facility_id)
    if report.status != "DRAFT":
        raise HTTPException(status_code=409, detail="Only DRAFT reports can be submitted")

    report.status = "SUBMITTED"
    report.submitted_at = utcnow()
    report.submitted_by = current_user.id

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="reporting.national_report_submitted",
        entity_type="national_report",
        entity_id=report.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(report)
    return {"data": report, "message": "national report submitted"}


@router.post("/national-reports/{report_id}/validate")
def validate_national_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.manage")),
):
    report = db.query(NationalReport).filter(NationalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="National report not found")
    enforce_facility_access(current_user, report.facility_id)
    if report.status != "SUBMITTED":
        raise HTTPException(status_code=409, detail="Only SUBMITTED reports can be validated")

    report.status = "VALIDATED"
    report.validated_at = utcnow()
    report.validated_by = current_user.id

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="reporting.national_report_validated",
        entity_type="national_report",
        entity_id=report.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(report)
    return {"data": report, "message": "national report validated"}


@router.post("/national-reports/{report_id}/reject")
def reject_national_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.manage")),
):
    report = db.query(NationalReport).filter(NationalReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="National report not found")
    enforce_facility_access(current_user, report.facility_id)
    if report.status != "SUBMITTED":
        raise HTTPException(status_code=409, detail="Only SUBMITTED reports can be rejected")

    report.status = "REJECTED"

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="reporting.national_report_rejected",
        entity_type="national_report",
        entity_id=report.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(report)
    return {"data": report, "message": "national report rejected"}


# ── Epidemic Alerts ───────────────────────────────────────────────────

@router.get("/epidemic-alerts")
def list_epidemic_alerts(
    facility_id: str | None = None,
    status: str | None = None,
    alert_level: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.read")),
):
    query = tenant_query(db, EpidemicAlert, current_user)
    if facility_id:
        query = query.filter(EpidemicAlert.facility_id == facility_id)
    if status:
        query = query.filter(EpidemicAlert.status == status)
    if alert_level:
        query = query.filter(EpidemicAlert.alert_level == alert_level)
    rows = query.order_by(EpidemicAlert.created_at.desc()).all()
    return {"data": rows, "message": "epidemic alerts list"}


@router.post("/epidemic-alerts")
def create_epidemic_alert(
    payload: EpidemicAlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.manage")),
):
    row = EpidemicAlert(**payload.model_dump(exclude_none=True))
    if not row.facility_id:
        row.facility_id = current_user.facility_id
    enforce_facility_access(current_user, row.facility_id)
    if not row.reported_by:
        row.reported_by = current_user.id
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="reporting.epidemic_alert_created",
        entity_type="epidemic_alert",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "epidemic alert created"}


@router.post("/epidemic-alerts/{alert_id}/close")
def close_epidemic_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.manage")),
):
    alert = db.query(EpidemicAlert).filter(EpidemicAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Epidemic alert not found")
    enforce_facility_access(current_user, alert.facility_id)
    if alert.status == "CLOSED":
        raise HTTPException(status_code=409, detail="Alert is already closed")

    alert.status = "CLOSED"
    alert.closed_at = utcnow()

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="reporting.epidemic_alert_closed",
        entity_type="epidemic_alert",
        entity_id=alert.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(alert)
    return {"data": alert, "message": "epidemic alert closed"}


# ── Health Statistics ─────────────────────────────────────────────────

@router.get("/statistics")
def list_health_statistics(
    facility_id: str | None = None,
    category: str | None = None,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.read")),
):
    query = tenant_query(db, HealthStatistic, current_user)
    if facility_id:
        query = query.filter(HealthStatistic.facility_id == facility_id)
    if category:
        query = query.filter(HealthStatistic.category == category)
    if period_start:
        query = query.filter(HealthStatistic.period_start >= period_start)
    if period_end:
        query = query.filter(HealthStatistic.period_end <= period_end)
    rows = query.order_by(HealthStatistic.created_at.desc()).all()
    return {"data": rows, "message": "health statistics list"}


@router.post("/statistics")
def create_health_statistic(
    payload: HealthStatisticCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.manage")),
):
    row = HealthStatistic(**payload.model_dump(exclude_none=True))
    if not row.facility_id:
        row.facility_id = current_user.facility_id
    enforce_facility_access(current_user, row.facility_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "health statistic created"}


# ── Dashboard ─────────────────────────────────────────────────────────

@router.get("/dashboard")
def get_dashboard(
    facility_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("reporting.read")),
):
    report_q = tenant_query(db, NationalReport, current_user)
    alert_q = tenant_query(db, EpidemicAlert, current_user)
    stat_q = tenant_query(db, HealthStatistic, current_user)

    if facility_id:
        enforce_facility_access(current_user, facility_id)
        report_q = report_q.filter(NationalReport.facility_id == facility_id)
        alert_q = alert_q.filter(EpidemicAlert.facility_id == facility_id)
        stat_q = stat_q.filter(HealthStatistic.facility_id == facility_id)

    total_reports = report_q.count()
    draft_reports = report_q.filter(NationalReport.status == "DRAFT").count()
    submitted_reports = report_q.filter(NationalReport.status == "SUBMITTED").count()
    validated_reports = report_q.filter(NationalReport.status == "VALIDATED").count()

    active_alerts = alert_q.filter(EpidemicAlert.status == "ACTIVE").count()
    total_alerts = alert_q.count()

    total_statistics = stat_q.count()

    return {
        "data": {
            "reports": {
                "total": total_reports,
                "draft": draft_reports,
                "submitted": submitted_reports,
                "validated": validated_reports,
            },
            "alerts": {
                "active": active_alerts,
                "total": total_alerts,
            },
            "statistics": {
                "total": total_statistics,
            },
        },
        "message": "reporting dashboard",
    }
