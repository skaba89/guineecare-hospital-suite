"""Schemas Pydantic pour le module RH v2 v1.5.0."""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Shift ───────────────────────────────────────────────────────────────────

ShiftType = Literal["DAY", "NIGHT", "FULL_DAY", "ON_CALL"]
Recurrence = Literal["DAILY", "WEEKDAYS", "WEEKEND", "CUSTOM"]


class ShiftCreate(BaseModel):
    facility_id: str | None = None
    department_id: str | None = None
    code: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=200)
    shift_type: ShiftType = "DAY"
    color: str | None = Field(None, max_length=16)
    start_time: str | None = Field(None, description="HH:MM")
    end_time: str | None = Field(None, description="HH:MM")
    duration_hours: int | None = Field(None, ge=1, le=72)
    recurrence: Recurrence = "DAILY"
    days_of_week: list[int] | None = Field(None, description="0=dimanche...6=samedi, si recurrence=CUSTOM")
    required_staff_count: int = Field(1, ge=1, le=50)
    required_profession: str | None = None
    enabled: bool = True
    description: str | None = None


class ShiftUpdate(BaseModel):
    name: str | None = None
    shift_type: ShiftType | None = None
    color: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_hours: int | None = None
    recurrence: Recurrence | None = None
    days_of_week: list[int] | None = None
    required_staff_count: int | None = None
    required_profession: str | None = None
    enabled: bool | None = None
    description: str | None = None


class ShiftRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    facility_id: str
    department_id: str | None = None
    code: str
    name: str
    shift_type: str
    color: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    duration_hours: int | None = None
    recurrence: str
    days_of_week: list[int] = Field(default_factory=list)
    required_staff_count: int
    required_profession: str | None = None
    enabled: bool
    description: str | None = None

    @classmethod
    def from_model(cls, s) -> "ShiftRead":
        from datetime import time as _time
        return cls(
            id=s.id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            facility_id=s.facility_id,
            department_id=s.department_id,
            code=s.code,
            name=s.name,
            shift_type=s.shift_type,
            color=s.color,
            start_time=s.start_time.isoformat() if isinstance(s.start_time, _time) else s.start_time,
            end_time=s.end_time.isoformat() if isinstance(s.end_time, _time) else s.end_time,
            duration_hours=s.duration_hours,
            recurrence=s.recurrence,
            days_of_week=[int(d) for d in (s.days_of_week or "").split(",") if d.isdigit()],
            required_staff_count=s.required_staff_count,
            required_profession=s.required_profession,
            enabled=bool(s.enabled),
            description=s.description,
        )


class ShiftListResponse(BaseModel):
    data: list[ShiftRead]
    total: int


# ── ShiftAssignment ─────────────────────────────────────────────────────────

AssignmentStatus = Literal["SCHEDULED", "CONFIRMED", "COMPLETED", "ABSENT", "CANCELLED"]


class ShiftAssignmentCreate(BaseModel):
    facility_id: str | None = None
    department_id: str | None = None
    shift_id: str
    staff_id: str
    assignment_date: date
    start_time: str | None = None
    end_time: str | None = None
    notes: str | None = None


class ShiftAssignmentUpdate(BaseModel):
    staff_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    status: AssignmentStatus | None = None
    notes: str | None = None


class ShiftAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    facility_id: str
    department_id: str | None = None
    shift_id: str
    staff_id: str
    assignment_date: date
    start_time: str | None = None
    end_time: str | None = None
    status: str
    notes: str | None = None
    created_by: str | None = None
    confirmed_at: datetime | None = None
    completed_at: datetime | None = None

    @classmethod
    def from_model(cls, a) -> "ShiftAssignmentRead":
        from datetime import time as _time
        return cls(
            id=a.id,
            created_at=a.created_at,
            updated_at=a.updated_at,
            facility_id=a.facility_id,
            department_id=a.department_id,
            shift_id=a.shift_id,
            staff_id=a.staff_id,
            assignment_date=a.assignment_date,
            start_time=a.start_time.isoformat() if isinstance(a.start_time, _time) else a.start_time,
            end_time=a.end_time.isoformat() if isinstance(a.end_time, _time) else a.end_time,
            status=a.status,
            notes=a.notes,
            created_by=a.created_by,
            confirmed_at=a.confirmed_at,
            completed_at=a.completed_at,
        )


class ShiftAssignmentListResponse(BaseModel):
    data: list[ShiftAssignmentRead]
    total: int


class GenerateAssignmentsRequest(BaseModel):
    """Payload pour générer des affectations en masse à partir d'un shift récurrent."""
    start_date: date
    end_date: date
    staff_id: str | None = Field(None, description="Si null, le premier staff éligible est affecté")
    skip_weekends: bool = False
    skip_weekdays: bool = False


class GenerateAssignmentsResponse(BaseModel):
    generated: int
    skipped: int
    assignments: list[ShiftAssignmentRead]


# ── LeaveBalance ────────────────────────────────────────────────────────────

class LeaveBalanceCreate(BaseModel):
    facility_id: str | None = None
    staff_id: str
    year: int = Field(..., ge=2020, le=2100)
    accumulated_days: int = Field(26, ge=0, le=365)
    carried_over_days: int = Field(0, ge=0, le=365)


class LeaveBalanceUpdate(BaseModel):
    accumulated_days: int | None = None
    carried_over_days: int | None = None
    notes: str | None = None


class LeaveBalanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    facility_id: str
    staff_id: str
    year: int
    accumulated_days: int
    used_days: int
    carried_over_days: int
    pending_days: int
    remaining_days: int
    notes: str | None = None

    @classmethod
    def from_model(cls, b) -> "LeaveBalanceRead":
        remaining = b.accumulated_days + b.carried_over_days - b.used_days - b.pending_days
        return cls(
            id=b.id,
            created_at=b.created_at,
            updated_at=b.updated_at,
            facility_id=b.facility_id,
            staff_id=b.staff_id,
            year=b.year,
            accumulated_days=b.accumulated_days,
            used_days=b.used_days,
            carried_over_days=b.carried_over_days,
            pending_days=b.pending_days,
            remaining_days=remaining,
            notes=b.notes,
        )


class LeaveBalanceListResponse(BaseModel):
    data: list[LeaveBalanceRead]
    total: int


# ── OnCallDuty ──────────────────────────────────────────────────────────────

DutyType = Literal["TELEPHONIC", "PHYSICAL", "MIXED"]
OnCallStatus = Literal["SCHEDULED", "ACTIVE", "COMPLETED", "CANCELLED"]


class OnCallDutyCreate(BaseModel):
    facility_id: str | None = None
    department_id: str | None = None
    staff_id: str
    start_at: datetime
    end_at: datetime
    duty_type: DutyType = "TELEPHONIC"
    reason: str | None = None
    compensation_days: int = Field(1, ge=0, le=10)
    notes: str | None = None


class OnCallDutyUpdate(BaseModel):
    duty_type: DutyType | None = None
    reason: str | None = None
    status: OnCallStatus | None = None
    compensation_days: int | None = None
    notes: str | None = None


class OnCallDutyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    facility_id: str
    department_id: str | None = None
    staff_id: str
    start_at: datetime
    end_at: datetime
    duty_type: str
    reason: str | None = None
    status: str
    compensation_days: int
    notes: str | None = None
    created_by: str | None = None

    @classmethod
    def from_model(cls, d) -> "OnCallDutyRead":
        return cls(
            id=d.id,
            created_at=d.created_at,
            facility_id=d.facility_id,
            department_id=d.department_id,
            staff_id=d.staff_id,
            start_at=d.start_at,
            end_at=d.end_at,
            duty_type=d.duty_type,
            reason=d.reason,
            status=d.status,
            compensation_days=d.compensation_days,
            notes=d.notes,
            created_by=d.created_by,
        )


class OnCallDutyListResponse(BaseModel):
    data: list[OnCallDutyRead]
    total: int


# ── ShiftSwap ───────────────────────────────────────────────────────────────

SwapStatus = Literal["REQUESTED", "ACCEPTED", "APPROVED", "REJECTED", "CANCELLED", "COMPLETED"]


class ShiftSwapCreate(BaseModel):
    facility_id: str | None = None
    assignment_id: str
    replacement_id: str
    reason: str | None = None


class ShiftSwapAction(BaseModel):
    """Action générique pour accepter/refuser/approuver une demande de swap."""
    manager_note: str | None = None


class ShiftSwapRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    facility_id: str
    assignment_id: str
    requester_id: str
    replacement_id: str
    reason: str | None = None
    status: str
    accepted_at: datetime | None = None
    approved_at: datetime | None = None
    rejected_at: datetime | None = None
    cancelled_at: datetime | None = None
    approved_by: str | None = None
    rejected_by: str | None = None
    manager_note: str | None = None

    @classmethod
    def from_model(cls, s) -> "ShiftSwapRead":
        return cls(
            id=s.id,
            created_at=s.created_at,
            updated_at=s.updated_at,
            facility_id=s.facility_id,
            assignment_id=s.assignment_id,
            requester_id=s.requester_id,
            replacement_id=s.replacement_id,
            reason=s.reason,
            status=s.status,
            accepted_at=s.accepted_at,
            approved_at=s.approved_at,
            rejected_at=s.rejected_at,
            cancelled_at=s.cancelled_at,
            approved_by=s.approved_by,
            rejected_by=s.rejected_by,
            manager_note=s.manager_note,
        )


class ShiftSwapListResponse(BaseModel):
    data: list[ShiftSwapRead]
    total: int


# ── Planning view ───────────────────────────────────────────────────────────

class PlanningCell(BaseModel):
    """Cellule du planning hebdo : un staff × un jour = 0..N affectations."""
    staff_id: str
    date: date
    assignments: list[ShiftAssignmentRead]


class PlanningRow(BaseModel):
    """Ligne du planning : un staff × tous les jours de la période."""
    staff_id: str
    staff_name: str
    employee_number: str | None = None
    profession: str | None = None
    cells: list[PlanningCell]


class PlanningResponse(BaseModel):
    """Planning complet pour une facility + période."""
    facility_id: str | None = None
    department_id: str | None = None
    start_date: date
    end_date: date
    days: list[str] = Field(default_factory=list, description="Liste des dates ISO au format YYYY-MM-DD")
    rows: list[PlanningRow]
    summary: dict
