from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Room ──────────────────────────────────────────────────────────────

class RoomCreate(BaseModel):
    facility_id: str
    department_id: str
    code: str
    name: str
    room_type: str | None = None
    status: str = "ACTIVE"


class RoomRead(BaseModel):
    id: str
    facility_id: str
    department_id: str
    code: str
    name: str
    room_type: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Bed ───────────────────────────────────────────────────────────────

class BedCreate(BaseModel):
    facility_id: str
    room_id: str
    bed_number: str
    bed_status: str = "AVAILABLE"


class BedRead(BaseModel):
    id: str
    facility_id: str
    room_id: str
    bed_number: str
    bed_status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Hospital Stay ─────────────────────────────────────────────────────

class HospitalStayCreate(BaseModel):
    facility_id: str
    patient_id: str
    admission_id: str | None = None
    bed_id: str | None = None
    reason: str | None = None


class HospitalStayRead(BaseModel):
    id: str
    facility_id: str
    patient_id: str
    admission_id: str | None = None
    bed_id: str | None = None
    reason: str | None = None
    status: str
    admitted_at: datetime
    discharged_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Bed Board (convenience view) ──────────────────────────────────────

class BedBoardItem(BaseModel):
    room_code: str
    room_name: str
    bed_id: str
    bed_number: str
    bed_status: str
    patient_name: str | None = None
    stay_id: str | None = None
