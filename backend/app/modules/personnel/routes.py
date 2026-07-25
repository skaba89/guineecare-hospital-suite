from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import enforce_facility_access, tenant_query, get_user_facility_id
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.personnel.models import StaffMember, OnCallSchedule, LeaveRequest, Contract
from app.modules.personnel.schemas import (
    OnCallScheduleCreate,
    StaffMemberCreate,
    StaffMemberUpdate,
    LeaveRequestCreate,
    LeaveRequestUpdate,
    ContractCreate,
    ContractUpdate,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/personnel", tags=["personnel"])


# ── Staff Members ──────────────────────────────────────────────────────

@router.get("/staff")
def list_staff(
    department_id: str | None = None,
    profession: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    query = tenant_query(db, StaffMember, current_user).order_by(
        StaffMember.last_name, StaffMember.first_name
    )
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

    # Enforce tenant: user can only create staff in their facility
    enforce_facility_access(current_user, data.get("facility_id"))

    # Check employee_number uniqueness
    existing = db.query(StaffMember).filter(
        StaffMember.employee_number == data.get("employee_number")
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Numéro d'employé déjà existant")

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
    return {"data": row, "message": "Membre du personnel créé"}


@router.get("/staff/{staff_id}")
def get_staff_member(
    staff_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Membre du personnel non trouvé")
    # Enforce tenant access
    enforce_facility_access(current_user, row.facility_id)
    return {"data": row}


@router.put("/staff/{staff_id}")
def update_staff_member(
    staff_id: str,
    payload: StaffMemberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Membre du personnel non trouvé")

    # Enforce tenant access
    enforce_facility_access(current_user, row.facility_id)

    update_data = payload.model_dump(exclude_unset=True)
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
    return {"data": row, "message": "Membre du personnel mis à jour"}


@router.delete("/staff/{staff_id}")
def delete_staff_member(
    staff_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    row = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Membre du personnel non trouvé")

    enforce_facility_access(current_user, row.facility_id)

    # Soft delete: set status to RESIGNED
    row.status = "RESIGNED"
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="personnel.staff_deactivated",
        entity_type="staff_member",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    return {"data": None, "message": "Membre du personnel désactivé"}


# ── On-Call Schedules ──────────────────────────────────────────────────

@router.get("/on-call")
def list_on_call_schedules(
    department_id: str | None = None,
    on_call_date: date | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    query = tenant_query(db, OnCallSchedule, current_user).order_by(
        OnCallSchedule.on_call_date.desc()
    )
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
            data["on_call_date"] = datetime.strptime(date_str, "%Y-%m-%d").date()
    elif not data.get("on_call_date"):
        raise HTTPException(status_code=400, detail="on_call_date est requis")

    # Auto-fill facility_id from current user
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id

    enforce_facility_access(current_user, data.get("facility_id"))

    # Verify staff member exists
    staff_id = data.get("staff_id")
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Membre du personnel non trouvé")

    # Enforce staff belongs to same facility
    enforce_facility_access(current_user, staff.facility_id)

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
    return {"data": row, "message": "Garde planifiée"}


@router.delete("/on-call/{schedule_id}")
def delete_on_call_entry(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    row = db.query(OnCallSchedule).filter(OnCallSchedule.id == schedule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Planning de garde non trouvé")

    enforce_facility_access(current_user, row.facility_id)

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
    return {"data": None, "message": "Garde supprimée"}


# ── Leave Requests ─────────────────────────────────────────────────────

@router.get("/leaves")
def list_leave_requests(
    staff_id: str | None = None,
    leave_type: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    query = tenant_query(db, LeaveRequest, current_user).order_by(
        LeaveRequest.created_at.desc()
    )
    if staff_id:
        query = query.filter(LeaveRequest.staff_id == staff_id)
    if leave_type:
        query = query.filter(LeaveRequest.leave_type == leave_type)
    if status:
        query = query.filter(LeaveRequest.status == status)
    if pagination.search:
        query = query.filter(
            (LeaveRequest.reason.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/leaves")
def create_leave_request(
    payload: LeaveRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    data = payload.model_dump(exclude_none=True)

    # Auto-fill facility_id from current user
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id

    enforce_facility_access(current_user, data.get("facility_id"))

    # Verify staff member exists
    staff = db.query(StaffMember).filter(StaffMember.id == data.get("staff_id")).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Membre du personnel non trouvé")

    enforce_facility_access(current_user, staff.facility_id)

    # Validate dates
    if data["end_date"] < data["start_date"]:
        raise HTTPException(status_code=400, detail="La date de fin doit être après la date de début")

    row = LeaveRequest(**data, created_by=current_user.id)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="personnel.leave_created",
        entity_type="leave_request",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "Demande de congé créée"}


@router.put("/leaves/{leave_id}")
def update_leave_request(
    leave_id: str,
    payload: LeaveRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    row = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Demande de congé non trouvée")

    enforce_facility_access(current_user, row.facility_id)

    update_data = payload.model_dump(exclude_unset=True)

    # If approving/rejecting, set approved_by
    if update_data.get("status") in ("APPROVED", "REJECTED"):
        update_data["approved_by"] = current_user.id
        update_data["approved_at"] = datetime.utcnow()

    for key, value in update_data.items():
        setattr(row, key, value)

    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name=f"personnel.leave_{row.status.lower()}",
        entity_type="leave_request",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "Demande de congé mise à jour"}


# ── Contracts ──────────────────────────────────────────────────────────

@router.get("/contracts")
def list_contracts(
    staff_id: str | None = None,
    contract_type: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    query = tenant_query(db, Contract, current_user).order_by(
        Contract.created_at.desc()
    )
    if staff_id:
        query = query.filter(Contract.staff_id == staff_id)
    if contract_type:
        query = query.filter(Contract.contract_type == contract_type)
    if status:
        query = query.filter(Contract.status == status)
    return paginate(query, pagination)


@router.post("/contracts")
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    data = payload.model_dump(exclude_none=True)

    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id

    enforce_facility_access(current_user, data.get("facility_id"))

    staff = db.query(StaffMember).filter(StaffMember.id == data.get("staff_id")).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Membre du personnel non trouvé")

    enforce_facility_access(current_user, staff.facility_id)

    row = Contract(**data, created_by=current_user.id)
    db.add(row)
    db.flush()

    # Update staff member contract info
    if data.get("contract_type"):
        staff.contract_type = data["contract_type"]
    if data.get("salary_grade"):
        staff.salary_grade = data["salary_grade"]

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="personnel.contract_created",
        entity_type="contract",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "Contrat créé"}


@router.put("/contracts/{contract_id}")
def update_contract(
    contract_id: str,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    row = db.query(Contract).filter(Contract.id == contract_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Contrat non trouvé")

    enforce_facility_access(current_user, row.facility_id)

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(row, key, value)

    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="personnel.contract_updated",
        entity_type="contract",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "Contrat mis à jour"}


# ── Dashboard/Stats ────────────────────────────────────────────────────

@router.get("/stats")
def personnel_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Get personnel statistics for the current facility."""
    from sqlalchemy import func

    base_query = tenant_query(db, StaffMember, current_user)

    total = base_query.count()
    by_profession = (
        tenant_query(db, StaffMember, current_user)
        .with_entities(StaffMember.profession, func.count(StaffMember.id))
        .group_by(StaffMember.profession)
        .all()
    )
    by_status = (
        tenant_query(db, StaffMember, current_user)
        .with_entities(StaffMember.status, func.count(StaffMember.id))
        .group_by(StaffMember.status)
        .all()
    )

    pending_leaves = (
        tenant_query(db, LeaveRequest, current_user)
        .filter(LeaveRequest.status == "PENDING")
        .count()
    )

    return {
        "data": {
            "total_staff": total,
            "by_profession": {p or "NON_DEFINI": c for p, c in by_profession},
            "by_status": {s: c for s, c in by_status},
            "pending_leaves": pending_leaves,
        }
    }
