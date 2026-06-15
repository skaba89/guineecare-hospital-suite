from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.surgery.models import OperatingRoom, SurgeryReport, SurgerySchedule
from app.modules.surgery.schemas import (
    OperatingRoomCreate,
    SurgeryReportCreate,
    SurgeryScheduleCreate,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/surgery", tags=["surgery"])


# ── Operating Rooms ───────────────────────────────────────────────────

@router.get("/rooms")
def list_rooms(
    facility_id: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.read")),
):
    query = tenant_query(db, OperatingRoom, current_user)
    if facility_id:
        query = query.filter(OperatingRoom.facility_id == facility_id)
    if status:
        query = query.filter(OperatingRoom.status == status)
    rows = query.order_by(OperatingRoom.code).all()
    return {"data": rows, "message": "rooms list"}


@router.post("/rooms")
def create_room(
    payload: OperatingRoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = OperatingRoom(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="surgery.room_created",
        entity_type="operating_room",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "room created"}


# ── Surgery Schedules ─────────────────────────────────────────────────

@router.get("/schedules")
def list_schedules(
    patient_id: str | None = None,
    status: str | None = None,
    operating_room_id: str | None = None,
    date: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.read")),
):
    query = tenant_query(db, SurgerySchedule, current_user)
    if patient_id:
        query = query.filter(SurgerySchedule.patient_id == patient_id)
    if status:
        query = query.filter(SurgerySchedule.status == status)
    if operating_room_id:
        query = query.filter(SurgerySchedule.operating_room_id == operating_room_id)
    if date:
        filter_date = datetime.strptime(date, "%Y-%m-%d")
        query = query.filter(SurgerySchedule.scheduled_date >= filter_date)
    rows = query.order_by(SurgerySchedule.scheduled_date.desc()).all()
    return {"data": rows, "message": "schedules list"}


@router.post("/schedules")
def create_schedule(
    payload: SurgeryScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    if not data.get("surgeon_id"):
        data["surgeon_id"] = current_user.id
    row = SurgerySchedule(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="surgery.schedule_created",
        entity_type="surgery_schedule",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "schedule created"}


@router.post("/schedules/{schedule_id}/start")
def start_surgery(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.manage")),
):
    schedule = db.query(SurgerySchedule).filter(SurgerySchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    enforce_facility_access(current_user, schedule.facility_id)
    if schedule.status != "SCHEDULED":
        raise HTTPException(status_code=409, detail="Schedule is not in SCHEDULED status")

    schedule.status = "IN_PROGRESS"
    schedule.started_at = utcnow()

    # Mark room as OCCUPIED if assigned
    if schedule.operating_room_id:
        room = db.query(OperatingRoom).filter(OperatingRoom.id == schedule.operating_room_id).first()
        if room:
            room.status = "OCCUPIED"

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="surgery.started",
        entity_type="surgery_schedule",
        entity_id=schedule.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(schedule)
    return {"data": schedule, "message": "surgery started"}


@router.post("/schedules/{schedule_id}/complete")
def complete_surgery(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.manage")),
):
    schedule = db.query(SurgerySchedule).filter(SurgerySchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    enforce_facility_access(current_user, schedule.facility_id)
    if schedule.status != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="Schedule is not in IN_PROGRESS status")

    schedule.status = "COMPLETED"
    schedule.ended_at = utcnow()

    # Mark room as AVAILABLE if assigned
    if schedule.operating_room_id:
        room = db.query(OperatingRoom).filter(OperatingRoom.id == schedule.operating_room_id).first()
        if room:
            room.status = "AVAILABLE"

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="surgery.completed",
        entity_type="surgery_schedule",
        entity_id=schedule.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(schedule)
    return {"data": schedule, "message": "surgery completed"}


@router.post("/schedules/{schedule_id}/cancel")
def cancel_surgery(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.manage")),
):
    schedule = db.query(SurgerySchedule).filter(SurgerySchedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    enforce_facility_access(current_user, schedule.facility_id)
    if schedule.status == "COMPLETED":
        raise HTTPException(status_code=409, detail="Cannot cancel a completed surgery")

    # If the surgery was in progress, free the room before changing status
    if schedule.status == "IN_PROGRESS" and schedule.operating_room_id:
        room = db.query(OperatingRoom).filter(OperatingRoom.id == schedule.operating_room_id).first()
        if room:
            room.status = "AVAILABLE"

    schedule.status = "CANCELLED"

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="surgery.cancelled",
        entity_type="surgery_schedule",
        entity_id=schedule.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(schedule)
    return {"data": schedule, "message": "surgery cancelled"}


# ── Surgery Reports ───────────────────────────────────────────────────

@router.get("/reports")
def list_reports(
    patient_id: str | None = None,
    schedule_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.read")),
):
    query = tenant_query(db, SurgeryReport, current_user)
    if patient_id:
        query = query.filter(SurgeryReport.patient_id == patient_id)
    if schedule_id:
        query = query.filter(SurgeryReport.schedule_id == schedule_id)
    rows = query.order_by(SurgeryReport.created_at.desc()).all()
    return {"data": rows, "message": "reports list"}


@router.post("/reports")
def create_report(
    payload: SurgeryReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    if not data.get("surgeon_id"):
        data["surgeon_id"] = current_user.id
    if not data.get("patient_id"):
        schedule = db.query(SurgerySchedule).filter(SurgerySchedule.id == payload.schedule_id).first()
        if schedule:
            data["patient_id"] = schedule.patient_id
    row = SurgeryReport(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="surgery.report_created",
        entity_type="surgery_report",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "report created"}


@router.post("/reports/{report_id}/validate")
def validate_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("surgery.manage")),
):
    report = db.query(SurgeryReport).filter(SurgeryReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    enforce_facility_access(current_user, report.facility_id)
    if report.status == "VALIDATED":
        raise HTTPException(status_code=409, detail="Report already validated")

    report.status = "VALIDATED"
    report.validated_at = utcnow()

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="surgery.report_validated",
        entity_type="surgery_report",
        entity_id=report.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(report)
    return {"data": report, "message": "report validated"}
