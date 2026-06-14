from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ── National Report ───────────────────────────────────────────────────

class NationalReportCreate(BaseModel):
    facility_id: str | None = None
    report_type: str
    period_start: datetime
    period_end: datetime
    total_admissions: str | None = None
    total_discharges: str | None = None
    total_deaths: str | None = None
    total_births: str | None = None
    total_surgeries: str | None = None
    total_emergency_visits: str | None = None
    bed_occupancy_rate: str | None = None
    average_stay_days: str | None = None
    disease_distribution: str | None = None
    notes: str | None = None


class NationalReportRead(BaseModel):
    id: str
    facility_id: str
    report_type: str
    period_start: datetime
    period_end: datetime
    total_admissions: str | None = None
    total_discharges: str | None = None
    total_deaths: str | None = None
    total_births: str | None = None
    total_surgeries: str | None = None
    total_emergency_visits: str | None = None
    bed_occupancy_rate: str | None = None
    average_stay_days: str | None = None
    disease_distribution: str | None = None
    status: str
    submitted_by: str | None = None
    submitted_at: datetime | None = None
    validated_by: str | None = None
    validated_at: datetime | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Epidemic Alert ────────────────────────────────────────────────────

class EpidemicAlertCreate(BaseModel):
    facility_id: str | None = None
    disease_name: str
    case_count: str
    threshold_exceeded: str = "YES"
    alert_level: str = "WARNING"
    region: str | None = None
    description: str | None = None
    measures_taken: str | None = None
    reported_by: str | None = None


class EpidemicAlertRead(BaseModel):
    id: str
    facility_id: str
    disease_name: str
    case_count: str
    threshold_exceeded: str
    alert_level: str
    region: str | None = None
    description: str | None = None
    measures_taken: str | None = None
    status: str
    reported_by: str | None = None
    created_at: datetime
    closed_at: datetime | None = None

    class Config:
        from_attributes = True


# ── Health Statistic ──────────────────────────────────────────────────

class HealthStatisticCreate(BaseModel):
    facility_id: str | None = None
    category: str
    metric_name: str
    metric_value: str
    period_start: datetime
    period_end: datetime
    unit: str | None = None
    source: str | None = None


class HealthStatisticRead(BaseModel):
    id: str
    facility_id: str
    category: str
    metric_name: str
    metric_value: str
    period_start: datetime
    period_end: datetime
    unit: str | None = None
    source: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
