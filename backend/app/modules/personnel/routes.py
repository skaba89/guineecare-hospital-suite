from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.personnel.models import OnCallSchedule, StaffMember
from app.modules.personnel.schemas import (
    OnCallScheduleCreate,
    StaffMemberCreate,
    StaffMemberUpdate,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/personnel", tags=["personnel"])


# ── Staff Members ──────────────────────────────────────────────────────

@router.get("/staff")
def list_staff(
    facility_id: str | None = None,
    department_id: str | None = None,
    profession: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    query = db.query(StaffMember).order_by(StaffMember.last_name, StaffMember.first_name)
    if facility_id:
        query = query.filter(StaffMember.facility_id == facility_id)
    if department_id:
        query = query.filter(StaffMember.department_id == department_id)
    if profession:
        query = query.filter(StaffMember.profession == profession)
    if status:
        query = query.filter(StaffMember.status == status)
    if pagination.search:
        query = query.filter(
            (StaffMember.first_name.ilike(f"%{pagination.search}%"))
            | (StaffMember.last_name.ilike(f"%{pagination.search}%"))
            | (StaffMember.employee_number.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/staff")
def create_staff_member(
    payload: StaffMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    data = payload.model_dump(exclude_none=True)

    # Map frontend 'role' to backend 'profession' if provided
    if "role" in data and "profession" not in data:
        data["profession"] = data.pop("role")
    elif "role" in data:
        data.pop("role")

    # Auto-generate employee_number if not provided
    if not data.get("employee_number"):
        count = db.query(StaffMember).count()
        data["employee_number"] = f"EMP-{count + 1:04d}"

    # Auto-fill facility_id from current user if not provided
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id

    # Check employee_number uniqueness
    existing = db.query(StaffMember).filter(
        StaffMember.employee_number == data.get("employee_number")
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Employee number already exists")

    row = StaffMember(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="personnel.staff_created",
        entity_type="staff_member",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "staff member created"}


@router.get("/staff/{staff_id}")
def get_staff_member(
    staff_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return {"data": row, "message": "staff member detail"}


@router.put("/staff/{staff_id}")
def update_staff_member(
    staff_id: str,
    payload: StaffMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Staff member not found")

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(row, key, value)

    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="personnel.staff_updated",
        entity_type="staff_member",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "staff member updated"}


# ── On-Call Schedules ──────────────────────────────────────────────────

@router.get("/on-call")
def list_on_call_schedules(
    facility_id: str | None = None,
    department_id: str | None = None,
    on_call_date: datetime | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    query = db.query(OnCallSchedule).order_by(OnCallSchedule.on_call_date.desc())
    if facility_id:
        query = query.filter(OnCallSchedule.facility_id == facility_id)
    if department_id:
        query = query.filter(OnCallSchedule.department_id == department_id)
    if on_call_date:
        query = query.filter(OnCallSchedule.on_call_date == on_call_date)
    return paginate(query, pagination)


@router.post("/on-call")
def create_on_call_entry(
    payload: OnCallScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    data = payload.model_dump(exclude_none=True)

    # Map frontend 'shift' to backend 'shift_type' if provided
    if "shift" in data:
        shift_val = data.pop("shift")
        if "shift_type" not in data or data["shift_type"] == "DAY":
            data["shift_type"] = shift_val

    # Map frontend 'on_call_date_str' to 'on_call_date' if provided
    if "on_call_date_str" in data:
        date_str = data.pop("on_call_date_str")
        if not data.get("on_call_date"):
            data["on_call_date"] = datetime.strptime(date_str, "%Y-%m-%d")
    elif not data.get("on_call_date"):
        raise HTTPException(status_code=400, detail="on_call_date is required")

    # Auto-fill facility_id from current user
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id

    # Verify staff member exists
    staff_id = data.get("staff_id")
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    row = OnCallSchedule(**data, created_by=current_user.id)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="personnel.oncall_created",
        entity_type="on_call_schedule",
        entity_id=row.id,
        level="NORMAL",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "on-call entry created"}


@router.delete("/on-call/{schedule_id}")
def delete_on_call_entry(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    row = db.query(OnCallSchedule).filter(OnCallSchedule.id == schedule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="On-call schedule not found")

    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="personnel.oncall_deleted",
        entity_type="on_call_schedule",
        entity_id=row.id,
        level="NORMAL",
    )
    db.delete(row)
    db.commit()
    return {"data": None, "message": "on-call entry deleted"}
