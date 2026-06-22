"""Routes RH v2 v1.5.0 — plannings, shifts, gardes, congés, astreintes, swaps.

Sous-module monté sous `/api/v1/personnel/*` (préfixe partagé avec le module
personnel existant).

Permissions RBAC :
- `personnel.read` : consultation planning, shifts, soldes, astreintes, swaps.
- `personnel.manage` : CRUD shifts, affectations, approbation swaps, soldes.
"""
from datetime import date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import enforce_facility_access, tenant_query
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.audit.service import audit_log
from app.modules.notifications.service import notify
from app.modules.personnel.models import LeaveRequest, StaffMember
from app.modules.personnel.rh_v2_models import (
    LeaveBalance,
    OnCallDuty,
    Shift,
    ShiftAssignment,
    ShiftSwap,
)
from app.modules.personnel.rh_v2_schemas import (
    GenerateAssignmentsRequest,
    GenerateAssignmentsResponse,
    LeaveBalanceCreate,
    LeaveBalanceListResponse,
    LeaveBalanceRead,
    LeaveBalanceUpdate,
    OnCallDutyCreate,
    OnCallDutyListResponse,
    OnCallDutyRead,
    OnCallDutyUpdate,
    PlanningResponse,
    ShiftAssignmentCreate,
    ShiftAssignmentListResponse,
    ShiftAssignmentRead,
    ShiftAssignmentUpdate,
    ShiftCreate,
    ShiftListResponse,
    ShiftRead,
    ShiftSwapAction,
    ShiftSwapCreate,
    ShiftSwapListResponse,
    ShiftSwapRead,
    ShiftUpdate,
)
from app.modules.personnel.rh_v2_service import (
    accept_swap,
    approve_swap,
    cancel_swap,
    check_conflicts,
    create_swap,
    generate_assignments,
    get_or_create_balance,
    get_planning,
    recompute_leave_balance,
    reject_swap,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/personnel", tags=["personnel-rh-v2"])


# ── Planning view ───────────────────────────────────────────────────────────

@router.get("/planning", response_model=PlanningResponse)
def get_planning_view(
    start_date: date = Query(..., description="Date de début (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Date de fin (YYYY-MM-DD)"),
    department_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Retourne le planning (rows × cells) pour une facility + période.

    Multi-tenant : SUPER_ADMIN peut voir toutes les facilities. Les autres
    rôles sont limités à leur facility.
    """
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date doit être >= start_date")
    if (end_date - start_date).days > 90:
        raise HTTPException(status_code=400, detail="Période max 90 jours")

    facility_id = None if current_user.role == "SUPER_ADMIN" else current_user.facility_id
    if facility_id is None and department_id:
        # SUPER_ADMIN peut filtrer par department mais on n'a pas la facility
        pass  # on laisse None, le filtrage par department suffit

    result = get_planning(
        db,
        facility_id=facility_id,
        department_id=department_id,
        start_date=start_date,
        end_date=end_date,
    )
    return PlanningResponse(**result)


# ── Shifts (templates récurrents) ───────────────────────────────────────────

@router.get("/shifts", response_model=ShiftListResponse)
def list_shifts(
    department_id: str | None = None,
    shift_type: str | None = None,
    enabled: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Liste les shifts (templates récurrents)."""
    query = tenant_query(db, Shift, current_user)
    if department_id:
        query = query.filter(Shift.department_id == department_id)
    if shift_type:
        query = query.filter(Shift.shift_type == shift_type)
    if enabled is not None:
        query = query.filter(Shift.enabled == enabled)
    rows = query.order_by(Shift.code).all()
    return ShiftListResponse(
        data=[ShiftRead.from_model(r) for r in rows],
        total=len(rows),
    )


@router.post("/shifts", response_model=ShiftRead, status_code=201)
def create_shift(
    payload: ShiftCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Crée un template de shift récurrent."""
    if payload.facility_id:
        enforce_facility_access(current_user, payload.facility_id)
    elif current_user.role != "SUPER_ADMIN":
        payload.facility_id = current_user.facility_id

    from datetime import time as _time
    row = Shift(
        facility_id=payload.facility_id,
        department_id=payload.department_id,
        code=payload.code,
        name=payload.name,
        shift_type=payload.shift_type,
        color=payload.color,
        start_time=_parse_time_or_none(payload.start_time),
        end_time=_parse_time_or_none(payload.end_time),
        duration_hours=payload.duration_hours,
        recurrence=payload.recurrence,
        days_of_week=",".join(str(d) for d in payload.days_of_week) if payload.days_of_week else None,
        required_staff_count=payload.required_staff_count,
        required_profession=payload.required_profession,
        enabled=payload.enabled,
        description=payload.description,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_log(
        db=db, user=current_user, action="rh_v2.shift.create",
        resource_type="shift", resource_id=row.id, request=request,
        status_code=201, payload={"code": row.code, "shift_type": row.shift_type},
    )
    return ShiftRead.from_model(row)


@router.patch("/shifts/{shift_id}", response_model=ShiftRead)
def update_shift(
    shift_id: str,
    payload: ShiftUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Met à jour un template de shift."""
    row = db.query(Shift).filter(Shift.id == shift_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Shift introuvable")
    enforce_facility_access(current_user, row.facility_id)

    if payload.name is not None: row.name = payload.name
    if payload.shift_type is not None: row.shift_type = payload.shift_type
    if payload.color is not None: row.color = payload.color
    if payload.start_time is not None: row.start_time = _parse_time_or_none(payload.start_time)
    if payload.end_time is not None: row.end_time = _parse_time_or_none(payload.end_time)
    if payload.duration_hours is not None: row.duration_hours = payload.duration_hours
    if payload.recurrence is not None: row.recurrence = payload.recurrence
    if payload.days_of_week is not None:
        row.days_of_week = ",".join(str(d) for d in payload.days_of_week) if payload.days_of_week else None
    if payload.required_staff_count is not None: row.required_staff_count = payload.required_staff_count
    if payload.required_profession is not None: row.required_profession = payload.required_profession
    if payload.enabled is not None: row.enabled = payload.enabled
    if payload.description is not None: row.description = payload.description

    db.commit()
    db.refresh(row)
    audit_log(
        db=db, user=current_user, action="rh_v2.shift.update",
        resource_type="shift", resource_id=row.id, request=request, status_code=200,
        payload={"updated_fields": list(payload.model_dump(exclude_unset=True).keys())},
    )
    return ShiftRead.from_model(row)


@router.delete("/shifts/{shift_id}", status_code=204)
def delete_shift(
    shift_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Supprime un template de shift. Les affectations existantes sont conservées."""
    row = db.query(Shift).filter(Shift.id == shift_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Shift introuvable")
    enforce_facility_access(current_user, row.facility_id)
    code_snapshot = row.code
    db.delete(row)
    db.commit()
    audit_log(
        db=db, user=current_user, action="rh_v2.shift.delete",
        resource_type="shift", resource_id=shift_id, request=request, status_code=204,
        payload={"code": code_snapshot},
    )
    return None


@router.post("/shifts/{shift_id}/generate", response_model=GenerateAssignmentsResponse)
def generate_shift_assignments(
    shift_id: str,
    payload: GenerateAssignmentsRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Génère des affectations en masse à partir d'un shift récurrent.

    Crée une ShiftAssignment par jour où le shift s'applique (selon sa récurrence).
    Si `staff_id` est null, le service choisit automatiquement un staff éligible.
    """
    shift = db.query(Shift).filter(Shift.id == shift_id).first()
    if not shift:
        raise HTTPException(status_code=404, detail="Shift introuvable")
    enforce_facility_access(current_user, shift.facility_id)

    assignments, skipped = generate_assignments(
        db=db,
        shift=shift,
        start_date=payload.start_date,
        end_date=payload.end_date,
        staff_id=payload.staff_id,
        skip_weekends=payload.skip_weekends,
        skip_weekdays=payload.skip_weekdays,
        created_by=current_user.id,
    )

    audit_log(
        db=db, user=current_user, action="rh_v2.shift.generate",
        resource_type="shift", resource_id=shift.id, request=request, status_code=200,
        payload={"generated": len(assignments), "skipped": skipped, "period": f"{payload.start_date} → {payload.end_date}"},
    )

    return GenerateAssignmentsResponse(
        generated=len(assignments),
        skipped=skipped,
        assignments=[ShiftAssignmentRead.from_model(a) for a in assignments],
    )


# ── Shift Assignments ───────────────────────────────────────────────────────

@router.get("/assignments", response_model=ShiftAssignmentListResponse)
def list_assignments(
    staff_id: str | None = None,
    shift_id: str | None = None,
    department_id: str | None = None,
    status: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Liste les affectations de shifts (paginé, multi-tenant)."""
    query = tenant_query(db, ShiftAssignment, current_user)
    if staff_id:
        query = query.filter(ShiftAssignment.staff_id == staff_id)
    if shift_id:
        query = query.filter(ShiftAssignment.shift_id == shift_id)
    if department_id:
        query = query.filter(ShiftAssignment.department_id == department_id)
    if status:
        query = query.filter(ShiftAssignment.status == status)
    if start_date:
        query = query.filter(ShiftAssignment.assignment_date >= start_date)
    if end_date:
        query = query.filter(ShiftAssignment.assignment_date <= end_date)
    query = query.order_by(ShiftAssignment.assignment_date.desc())
    result = paginate(query, pagination)
    return ShiftAssignmentListResponse(
        data=[ShiftAssignmentRead.from_model(r) for r in result["data"]],
        total=result["total"],
    )


@router.post("/assignments", response_model=ShiftAssignmentRead, status_code=201)
def create_assignment(
    payload: ShiftAssignmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Affecte un staff à un shift à une date donnée.

    Vérifie les conflits (staff déjà affecté ce jour-là) mais ne bloque pas —
    retourne un warning dans la réponse.
    """
    if payload.facility_id:
        enforce_facility_access(current_user, payload.facility_id)
    elif current_user.role != "SUPER_ADMIN":
        payload.facility_id = current_user.facility_id

    # Vérifier que le staff existe et appartient à la même facility
    staff = db.query(StaffMember).filter(StaffMember.id == payload.staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff introuvable")
    enforce_facility_access(current_user, staff.facility_id)

    from datetime import time as _time
    row = ShiftAssignment(
        facility_id=payload.facility_id or staff.facility_id,
        department_id=payload.department_id or staff.department_id,
        shift_id=payload.shift_id,
        staff_id=payload.staff_id,
        assignment_date=payload.assignment_date,
        start_time=_parse_time_or_none(payload.start_time),
        end_time=_parse_time_or_none(payload.end_time),
        status="SCHEDULED",
        created_by=current_user.id,
        notes=payload.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_log(
        db=db, user=current_user, action="rh_v2.assignment.create",
        resource_type="shift_assignment", resource_id=row.id, request=request,
        status_code=201, payload={"staff_id": row.staff_id, "date": row.assignment_date.isoformat()},
    )
    return ShiftAssignmentRead.from_model(row)


@router.patch("/assignments/{assignment_id}", response_model=ShiftAssignmentRead)
def update_assignment(
    assignment_id: str,
    payload: ShiftAssignmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Met à jour une affectation (changement de staff, statut, etc.)."""
    row = db.query(ShiftAssignment).filter(ShiftAssignment.id == assignment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Affectation introuvable")
    enforce_facility_access(current_user, row.facility_id)

    if payload.staff_id is not None: row.staff_id = payload.staff_id
    if payload.start_time is not None: row.start_time = _parse_time_or_none(payload.start_time)
    if payload.end_time is not None: row.end_time = _parse_time_or_none(payload.end_time)
    if payload.status is not None:
        row.status = payload.status
        if payload.status == "CONFIRMED":
            row.confirmed_at = datetime.utcnow()
        elif payload.status == "COMPLETED":
            row.completed_at = datetime.utcnow()
    if payload.notes is not None: row.notes = payload.notes

    db.commit()
    db.refresh(row)
    audit_log(
        db=db, user=current_user, action="rh_v2.assignment.update",
        resource_type="shift_assignment", resource_id=row.id, request=request, status_code=200,
        payload={"updated_fields": list(payload.model_dump(exclude_unset=True).keys())},
    )
    return ShiftAssignmentRead.from_model(row)


@router.delete("/assignments/{assignment_id}", status_code=204)
def delete_assignment(
    assignment_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Supprime une affectation. Préférable d'utiliser PATCH status=CANCELLED pour l'audit."""
    row = db.query(ShiftAssignment).filter(ShiftAssignment.id == assignment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Affectation introuvable")
    enforce_facility_access(current_user, row.facility_id)
    db.delete(row)
    db.commit()
    audit_log(
        db=db, user=current_user, action="rh_v2.assignment.delete",
        resource_type="shift_assignment", resource_id=assignment_id, request=request, status_code=204,
    )
    return None


@router.get("/assignments/{assignment_id}/conflicts")
def check_assignment_conflicts(
    assignment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Vérifie les conflits pour une affectation (staff déjà affecté le même jour)."""
    row = db.query(ShiftAssignment).filter(ShiftAssignment.id == assignment_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Affectation introuvable")
    enforce_facility_access(current_user, row.facility_id)

    conflicts = check_conflicts(
        db=db,
        staff_id=row.staff_id,
        assignment_date=row.assignment_date,
        start_time=row.start_time,
        end_time=row.end_time,
        exclude_assignment_id=row.id,
    )
    return {
        "assignment_id": row.id,
        "staff_id": row.staff_id,
        "date": row.assignment_date.isoformat(),
        "conflicts": [ShiftAssignmentRead.from_model(c).model_dump() for c in conflicts],
        "has_conflict": len(conflicts) > 0,
    }


# ── Leave Balances ──────────────────────────────────────────────────────────

@router.get("/leave-balances", response_model=LeaveBalanceListResponse)
def list_leave_balances(
    staff_id: str | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Liste les soldes de congés. Recalcule automatiquement used/pending."""
    query = tenant_query(db, LeaveBalance, current_user)
    if staff_id:
        query = query.filter(LeaveBalance.staff_id == staff_id)
    if year:
        query = query.filter(LeaveBalance.year == year)
    rows = query.order_by(LeaveBalance.year.desc()).all()
    # Recalculer chaque solde
    for r in rows:
        recompute_leave_balance(db, r)
    return LeaveBalanceListResponse(
        data=[LeaveBalanceRead.from_model(r) for r in rows],
        total=len(rows),
    )


@router.post("/leave-balances", response_model=LeaveBalanceRead, status_code=201)
def create_leave_balance(
    payload: LeaveBalanceCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Crée ou met à jour le solde de congés d'un staff pour une année."""
    if payload.facility_id:
        enforce_facility_access(current_user, payload.facility_id)
    elif current_user.role != "SUPER_ADMIN":
        payload.facility_id = current_user.facility_id

    # Vérifier l'existence
    existing = (
        db.query(LeaveBalance)
        .filter(LeaveBalance.staff_id == payload.staff_id)
        .filter(LeaveBalance.year == payload.year)
        .first()
    )
    if existing:
        existing.accumulated_days = payload.accumulated_days
        existing.carried_over_days = payload.carried_over_days
        db.commit()
        db.refresh(existing)
        recompute_leave_balance(db, existing)
        return LeaveBalanceRead.from_model(existing)

    row = LeaveBalance(
        facility_id=payload.facility_id,
        staff_id=payload.staff_id,
        year=payload.year,
        accumulated_days=payload.accumulated_days,
        carried_over_days=payload.carried_over_days,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    recompute_leave_balance(db, row)

    audit_log(
        db=db, user=current_user, action="rh_v2.leave_balance.create",
        resource_type="leave_balance", resource_id=row.id, request=request,
        status_code=201, payload={"staff_id": row.staff_id, "year": row.year},
    )
    return LeaveBalanceRead.from_model(row)


@router.get("/leave-balances/by-staff/{staff_id}", response_model=LeaveBalanceRead)
def get_staff_balance(
    staff_id: str,
    year: int = Query(..., ge=2020, le=2100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Récupère le solde de congés d'un staff pour une année (créé si manquant)."""
    staff = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff introuvable")
    enforce_facility_access(current_user, staff.facility_id)

    balance = get_or_create_balance(db, staff_id, staff.facility_id, year)
    return LeaveBalanceRead.from_model(balance)


# ── On-Call Duties (astreintes) ─────────────────────────────────────────────

@router.get("/on-call-duties", response_model=OnCallDutyListResponse)
def list_on_call_duties(
    staff_id: str | None = None,
    department_id: str | None = None,
    status: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Liste les astreintes."""
    query = tenant_query(db, OnCallDuty, current_user)
    if staff_id:
        query = query.filter(OnCallDuty.staff_id == staff_id)
    if department_id:
        query = query.filter(OnCallDuty.department_id == department_id)
    if status:
        query = query.filter(OnCallDuty.status == status)
    if start_date:
        query = query.filter(OnCallDuty.start_at >= start_date)
    if end_date:
        query = query.filter(OnCallDuty.end_at <= end_date)
    rows = query.order_by(OnCallDuty.start_at.desc()).all()
    return OnCallDutyListResponse(
        data=[OnCallDutyRead.from_model(r) for r in rows],
        total=len(rows),
    )


@router.post("/on-call-duties", response_model=OnCallDutyRead, status_code=201)
def create_on_call_duty(
    payload: OnCallDutyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Planifie une astreinte."""
    if payload.facility_id:
        enforce_facility_access(current_user, payload.facility_id)
    elif current_user.role != "SUPER_ADMIN":
        payload.facility_id = current_user.facility_id

    if payload.end_at <= payload.start_at:
        raise HTTPException(status_code=400, detail="end_at doit être > start_at")

    staff = db.query(StaffMember).filter(StaffMember.id == payload.staff_id).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff introuvable")

    row = OnCallDuty(
        facility_id=payload.facility_id or staff.facility_id,
        department_id=payload.department_id or staff.department_id,
        staff_id=payload.staff_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        duty_type=payload.duty_type,
        reason=payload.reason,
        compensation_days=payload.compensation_days,
        notes=payload.notes,
        created_by=current_user.id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_log(
        db=db, user=current_user, action="rh_v2.on_call.create",
        resource_type="on_call_duty", resource_id=row.id, request=request,
        status_code=201, payload={"staff_id": row.staff_id, "duty_type": row.duty_type},
    )
    return OnCallDutyRead.from_model(row)


@router.patch("/on-call-duties/{duty_id}", response_model=OnCallDutyRead)
def update_on_call_duty(
    duty_id: str,
    payload: OnCallDutyUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Met à jour une astreinte."""
    row = db.query(OnCallDuty).filter(OnCallDuty.id == duty_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Astreinte introuvable")
    enforce_facility_access(current_user, row.facility_id)

    if payload.duty_type is not None: row.duty_type = payload.duty_type
    if payload.reason is not None: row.reason = payload.reason
    if payload.status is not None: row.status = payload.status
    if payload.compensation_days is not None: row.compensation_days = payload.compensation_days
    if payload.notes is not None: row.notes = payload.notes

    db.commit()
    db.refresh(row)
    audit_log(
        db=db, user=current_user, action="rh_v2.on_call.update",
        resource_type="on_call_duty", resource_id=row.id, request=request, status_code=200,
    )
    return OnCallDutyRead.from_model(row)


@router.delete("/on-call-duties/{duty_id}", status_code=204)
def delete_on_call_duty(
    duty_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Supprime une astreinte."""
    row = db.query(OnCallDuty).filter(OnCallDuty.id == duty_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Astreinte introuvable")
    enforce_facility_access(current_user, row.facility_id)
    db.delete(row)
    db.commit()
    audit_log(
        db=db, user=current_user, action="rh_v2.on_call.delete",
        resource_type="on_call_duty", resource_id=duty_id, request=request, status_code=204,
    )
    return None


# ── Shift Swaps (remplacements) ─────────────────────────────────────────────

@router.get("/swaps", response_model=ShiftSwapListResponse)
def list_swaps(
    status: str | None = None,
    requester_id: str | None = None,
    replacement_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Liste les demandes de swap."""
    query = tenant_query(db, ShiftSwap, current_user)
    if status:
        query = query.filter(ShiftSwap.status == status)
    if requester_id:
        query = query.filter(ShiftSwap.requester_id == requester_id)
    if replacement_id:
        query = query.filter(ShiftSwap.replacement_id == replacement_id)
    rows = query.order_by(ShiftSwap.created_at.desc()).all()
    return ShiftSwapListResponse(
        data=[ShiftSwapRead.from_model(r) for r in rows],
        total=len(rows),
    )


@router.post("/swaps", response_model=ShiftSwapRead, status_code=201)
def create_swap_request(
    payload: ShiftSwapCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Crée une demande de swap. N'importe quel staff peut en faire la demande
    (pas besoin de `personnel.manage` — c'est son propre shift).
    """
    assignment = (
        db.query(ShiftAssignment)
        .filter(ShiftAssignment.id == payload.assignment_id)
        .first()
    )
    if not assignment:
        raise HTTPException(status_code=404, detail="Affectation introuvable")
    enforce_facility_access(current_user, assignment.facility_id)

    # Vérifier que le replacement existe
    replacement = db.query(StaffMember).filter(StaffMember.id == payload.replacement_id).first()
    if not replacement:
        raise HTTPException(status_code=404, detail="Staff remplaçant introuvable")

    if payload.facility_id:
        enforce_facility_access(current_user, payload.facility_id)
    elif current_user.role != "SUPER_ADMIN":
        payload.facility_id = current_user.facility_id

    swap = create_swap(
        db=db,
        assignment=assignment,
        replacement_id=payload.replacement_id,
        reason=payload.reason,
    )

    audit_log(
        db=db, user=current_user, action="rh_v2.swap.create",
        resource_type="shift_swap", resource_id=swap.id, request=request,
        status_code=201, payload={"assignment_id": assignment.id, "replacement_id": payload.replacement_id},
    )
    return ShiftSwapRead.from_model(swap)


@router.post("/swaps/{swap_id}/accept", response_model=ShiftSwapRead)
def accept_swap_request(
    swap_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Le remplaçant accepte la demande de swap."""
    swap = db.query(ShiftSwap).filter(ShiftSwap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=404, detail="Demande de swap introuvable")
    enforce_facility_access(current_user, swap.facility_id)

    swap = accept_swap(db, swap)
    audit_log(
        db=db, user=current_user, action="rh_v2.swap.accept",
        resource_type="shift_swap", resource_id=swap.id, request=request, status_code=200,
    )
    return ShiftSwapRead.from_model(swap)


@router.post("/swaps/{swap_id}/approve", response_model=ShiftSwapRead)
def approve_swap_request(
    swap_id: str,
    payload: ShiftSwapAction,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Le manager approuve le swap → transfère l'affectation au remplaçant."""
    swap = db.query(ShiftSwap).filter(ShiftSwap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=404, detail="Demande de swap introuvable")
    enforce_facility_access(current_user, swap.facility_id)

    swap = approve_swap(db, swap, current_user.id, payload.manager_note)
    audit_log(
        db=db, user=current_user, action="rh_v2.swap.approve",
        resource_type="shift_swap", resource_id=swap.id, request=request, status_code=200,
        payload={"manager_note": payload.manager_note},
    )
    return ShiftSwapRead.from_model(swap)


@router.post("/swaps/{swap_id}/reject", response_model=ShiftSwapRead)
def reject_swap_request(
    swap_id: str,
    payload: ShiftSwapAction,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.manage")),
):
    """Le manager refuse le swap."""
    swap = db.query(ShiftSwap).filter(ShiftSwap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=404, detail="Demande de swap introuvable")
    enforce_facility_access(current_user, swap.facility_id)

    swap = reject_swap(db, swap, current_user.id, payload.manager_note)
    audit_log(
        db=db, user=current_user, action="rh_v2.swap.reject",
        resource_type="shift_swap", resource_id=swap.id, request=request, status_code=200,
    )
    return ShiftSwapRead.from_model(swap)


@router.post("/swaps/{swap_id}/cancel", response_model=ShiftSwapRead)
def cancel_swap_request(
    swap_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("personnel.read")),
):
    """Le requester annule sa demande de swap."""
    swap = db.query(ShiftSwap).filter(ShiftSwap.id == swap_id).first()
    if not swap:
        raise HTTPException(status_code=404, detail="Demande de swap introuvable")
    enforce_facility_access(current_user, swap.facility_id)

    swap = cancel_swap(db, swap)
    audit_log(
        db=db, user=current_user, action="rh_v2.swap.cancel",
        resource_type="shift_swap", resource_id=swap.id, request=request, status_code=200,
    )
    return ShiftSwapRead.from_model(swap)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_time_or_none(s: str | None):
    """Parse 'HH:MM' ou 'HH:MM:SS' → time. None si vide."""
    if not s:
        return None
    parts = s.split(":")
    try:
        if len(parts) == 2:
            from datetime import time as _t
            return _t(int(parts[0]), int(parts[1]))
        if len(parts) == 3:
            from datetime import time as _t
            return _t(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        return None
    return None
