from datetime import datetime, date
from typing import Optional

from pydantic import BaseModel


# ── StaffMember ────────────────────────────────────────────────────────

class StaffMemberCreate(BaseModel):
    facility_id: str | None = None
    user_id: str | None = None
    employee_number: str | None = None
    first_name: str
    last_name: str
    profession: str | None = None
    role: str | None = None  # alias for profession from frontend
    specialty: str | None = None
    department_id: str | None = None
    phone: str | None = None
    email: str | None = None
    hire_date: date | None = None
    contract_type: str | None = None
    salary_grade: str | None = None
    status: str = "ACTIVE"


class StaffMemberUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    profession: str | None = None
    specialty: str | None = None
    department_id: str | None = None
    phone: str | None = None
    email: str | None = None
    hire_date: date | None = None
    contract_type: str | None = None
    salary_grade: str | None = None
    status: str | None = None


class StaffMemberRead(BaseModel):
    id: str
    facility_id: str
    user_id: str | None = None
    employee_number: str
    first_name: str
    last_name: str
    profession: str | None = None
    specialty: str | None = None
    department_id: str | None = None
    phone: str | None = None
    email: str | None = None
    hire_date: date | None = None
    contract_type: str | None = None
    salary_grade: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── OnCallSchedule ─────────────────────────────────────────────────────

class OnCallScheduleCreate(BaseModel):
    facility_id: str | None = None
    department_id: str | None = None
    staff_id: str
    on_call_date: date | None = None
    on_call_date_str: str | None = None  # accept date as string from frontend
    shift_type: str = "DAY"  # DAY, NIGHT, FULL_DAY
    shift: str | None = None  # alias from frontend
    notes: str | None = None


class OnCallScheduleRead(BaseModel):
    id: str
    facility_id: str
    department_id: str | None = None
    staff_id: str
    on_call_date: date
    shift_type: str
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── LeaveRequest ───────────────────────────────────────────────────────

class LeaveRequestCreate(BaseModel):
    facility_id: str | None = None
    staff_id: str
    leave_type: str  # CONGE_ANNUEL, MALADIE, MATERNITE, PATERNITE, SANS_SOLDE, AUTORISATION
    start_date: date
    end_date: date
    reason: str | None = None


class LeaveRequestUpdate(BaseModel):
    leave_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = None
    status: str | None = None  # PENDING, APPROVED, REJECTED, CANCELLED


class LeaveRequestRead(BaseModel):
    id: str
    facility_id: str
    staff_id: str
    leave_type: str
    start_date: date
    end_date: date
    reason: str | None = None
    status: str
    approved_by: str | None = None
    approved_at: datetime | None = None
    created_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Contract ───────────────────────────────────────────────────────────

class ContractCreate(BaseModel):
    facility_id: str | None = None
    staff_id: str
    contract_type: str  # CDI, CDD, INTERIM, STAGIAIRE, CONSULTANT
    start_date: date
    end_date: date | None = None
    position: str | None = None
    department_id: str | None = None
    salary_grade: str | None = None
    notes: str | None = None


class ContractUpdate(BaseModel):
    contract_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    position: str | None = None
    department_id: str | None = None
    salary_grade: str | None = None
    status: str | None = None
    notes: str | None = None


class ContractRead(BaseModel):
    id: str
    facility_id: str
    staff_id: str
    contract_type: str
    start_date: date
    end_date: date | None = None
    position: str | None = None
    department_id: str | None = None
    salary_grade: str | None = None
    status: str
    notes: str | None = None
    created_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
