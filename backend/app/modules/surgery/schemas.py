from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Operating Room ────────────────────────────────────────────────────

class OperatingRoomCreate(BaseModel):
    facility_id: str | None = None
    code: str
    name: str
    room_type: str | None = None
    status: str = "AVAILABLE"


class OperatingRoomRead(BaseModel):
    id: str
    facility_id: str
    code: str
    name: str
    room_type: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Surgery Schedule ──────────────────────────────────────────────────

class SurgeryScheduleCreate(BaseModel):
    facility_id: str | None = None
    patient_id: str
    operating_room_id: str | None = None
    surgeon_id: str | None = None
    anesthesiologist_id: str | None = None
    procedure_name: str
    procedure_code: str | None = None
    laterality: str | None = None
    urgency: str = "PLANNED"
    scheduled_date: datetime | None = None
    notes: str | None = None


class SurgeryScheduleRead(BaseModel):
    id: str
    facility_id: str
    patient_id: str
    operating_room_id: str | None = None
    surgeon_id: str | None = None
    anesthesiologist_id: str | None = None
    procedure_name: str
    procedure_code: str | None = None
    laterality: str | None = None
    urgency: str
    status: str
    scheduled_date: datetime | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Surgery Team Member ───────────────────────────────────────────────

class SurgeryTeamMemberCreate(BaseModel):
    schedule_id: str
    user_id: str | None = None
    role: str


class SurgeryTeamMemberRead(BaseModel):
    id: str
    schedule_id: str
    user_id: str | None = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Surgery Report ────────────────────────────────────────────────────

class SurgeryReportCreate(BaseModel):
    facility_id: str | None = None
    schedule_id: str
    patient_id: str | None = None
    surgeon_id: str | None = None
    operative_findings: str | None = None
    procedure_performed: str | None = None
    complications: str | None = None
    specimens: str | None = None
    blood_loss: str | None = None
    anesthesia_type: str | None = None


class SurgeryReportRead(BaseModel):
    id: str
    facility_id: str
    schedule_id: str
    patient_id: str
    surgeon_id: str | None = None
    operative_findings: str | None = None
    procedure_performed: str | None = None
    complications: str | None = None
    specimens: str | None = None
    blood_loss: str | None = None
    anesthesia_type: str | None = None
    status: str
    created_at: datetime
    validated_at: datetime | None = None

    class Config:
        from_attributes = True
