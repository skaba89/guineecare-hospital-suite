from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── Quality Indicator ─────────────────────────────────────────────────

class QualityIndicatorCreate(BaseModel):
    facility_id: str | None = None
    code: str
    name: str
    category: str | None = None
    description: str | None = None
    unit: str | None = None
    target_value: str | None = None
    frequency: str = "MONTHLY"


class QualityIndicatorRead(BaseModel):
    id: str
    facility_id: str
    code: str
    name: str
    category: str | None = None
    description: str | None = None
    unit: str | None = None
    target_value: str | None = None
    frequency: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Quality Measurement ───────────────────────────────────────────────

class QualityMeasurementCreate(BaseModel):
    facility_id: str | None = None
    indicator_id: str
    period_start: datetime
    period_end: datetime
    value: str
    numerator: str | None = None
    denominator: str | None = None
    notes: str | None = None
    recorded_by: str | None = None


class QualityMeasurementRead(BaseModel):
    id: str
    facility_id: str
    indicator_id: str
    period_start: datetime
    period_end: datetime
    value: str
    numerator: str | None = None
    denominator: str | None = None
    notes: str | None = None
    recorded_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Incident Report ───────────────────────────────────────────────────

class IncidentReportCreate(BaseModel):
    facility_id: str | None = None
    reported_by: str | None = None
    patient_id: str | None = None
    incident_date: datetime
    incident_type: str
    severity: str = "MINOR"
    description: str
    immediate_actions: str | None = None
    root_cause: str | None = None
    corrective_actions: str | None = None


class IncidentReportRead(BaseModel):
    id: str
    facility_id: str
    reported_by: str | None = None
    patient_id: str | None = None
    incident_date: datetime
    incident_type: str
    severity: str
    description: str
    immediate_actions: str | None = None
    root_cause: str | None = None
    corrective_actions: str | None = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
