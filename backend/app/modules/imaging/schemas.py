from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Imaging Order ─────────────────────────────────────────────────────

class ImagingOrderCreate(BaseModel):
    facility_id: str
    patient_id: str
    requesting_doctor_id: str | None = None
    exam_type: str
    body_region: str
    clinical_info: str | None = None
    urgency: str = "ROUTINE"


class ImagingOrderRead(BaseModel):
    id: str
    facility_id: str
    patient_id: str
    requesting_doctor_id: str | None = None
    exam_type: str
    body_region: str
    clinical_info: str | None = None
    urgency: str
    status: str
    ordered_at: datetime
    performed_at: datetime | None = None
    reported_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Imaging Result ────────────────────────────────────────────────────

class ImagingResultCreate(BaseModel):
    facility_id: str
    order_id: str
    patient_id: str
    radiologist_id: str | None = None
    findings: str | None = None
    conclusion: str | None = None
    recommendation: str | None = None


class ImagingResultRead(BaseModel):
    id: str
    facility_id: str
    order_id: str
    patient_id: str
    radiologist_id: str | None = None
    findings: str | None = None
    conclusion: str | None = None
    recommendation: str | None = None
    status: str
    created_at: datetime
    validated_at: datetime | None = None

    class Config:
        from_attributes = True
