"""Schemas Pydantic pour le dashboard qualité v1.4.0."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ── Threshold ───────────────────────────────────────────────────────────────

class QualityThresholdCreate(BaseModel):
    facility_id: str | None = None
    department_id: str | None = None
    indicator_id: str
    comparator: Literal["LT", "LE", "GT", "GE", "EQ"] = "GT"
    threshold_value: str = Field(..., min_length=1, max_length=100)
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"
    alert_message: str | None = Field(None, description="Template avec {{value}} et {{threshold}}")
    notify_roles: list[str] = Field(default_factory=lambda: ["ADMIN"])
    channels: list[Literal["in_app", "sms", "email"]] = Field(
        default_factory=lambda: ["in_app"]
    )
    enabled: bool = True
    cooldown_hours: int = Field(24, ge=0, le=720, description="Heures entre 2 alertes identiques")


class QualityThresholdUpdate(BaseModel):
    department_id: str | None = None
    comparator: Literal["LT", "LE", "GT", "GE", "EQ"] | None = None
    threshold_value: str | None = None
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] | None = None
    alert_message: str | None = None
    notify_roles: list[str] | None = None
    channels: list[Literal["in_app", "sms", "email"]] | None = None
    enabled: bool | None = None
    cooldown_hours: int | None = None


class QualityThresholdRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    facility_id: str | None = None
    department_id: str | None = None
    indicator_id: str
    comparator: str
    threshold_value: str
    severity: str
    alert_message: str | None = None
    notify_roles: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    enabled: bool
    cooldown_hours: int

    @classmethod
    def from_model(cls, t) -> "QualityThresholdRead":
        return cls(
            id=t.id,
            created_at=t.created_at,
            updated_at=t.updated_at,
            facility_id=t.facility_id,
            department_id=t.department_id,
            indicator_id=t.indicator_id,
            comparator=t.comparator,
            threshold_value=t.threshold_value,
            severity=t.severity,
            alert_message=t.alert_message,
            notify_roles=[r for r in (t.notify_roles or "").split(",") if r],
            channels=[c for c in (t.channels or "").split(",") if c],
            enabled=str(t.enabled).lower() == "true",
            cooldown_hours=int(t.cooldown_hours) if t.cooldown_hours and str(t.cooldown_hours).isdigit() else 24,
        )


class QualityThresholdListResponse(BaseModel):
    data: list[QualityThresholdRead]
    total: int


# ── Alert ───────────────────────────────────────────────────────────────────

class QualityAlertAck(BaseModel):
    assign_to: str | None = Field(None, description="User ID à qui assigner l'alerte")


class QualityAlertResolve(BaseModel):
    resolution_note: str = Field(..., min_length=1, max_length=4000)


class QualityAlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
    facility_id: str | None = None
    department_id: str | None = None
    threshold_id: str | None = None
    measurement_id: str | None = None
    notification_id: str | None = None
    indicator_id: str | None = None
    status: str
    severity: str
    title: str
    message: str | None = None
    observed_value: str | None = None
    threshold_value: str | None = None
    comparator: str | None = None
    assigned_to: str | None = None
    acknowledged_at: datetime | None = None
    acknowledged_by: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None
    resolution_note: str | None = None
    closed_at: datetime | None = None

    @classmethod
    def from_model(cls, a) -> "QualityAlertRead":
        return cls(
            id=a.id,
            created_at=a.created_at,
            updated_at=a.updated_at,
            facility_id=a.facility_id,
            department_id=a.department_id,
            threshold_id=a.threshold_id,
            measurement_id=a.measurement_id,
            notification_id=a.notification_id,
            indicator_id=a.indicator_id,
            status=a.status,
            severity=a.severity,
            title=a.title,
            message=a.message,
            observed_value=a.observed_value,
            threshold_value=a.threshold_value,
            comparator=a.comparator,
            assigned_to=a.assigned_to,
            acknowledged_at=a.acknowledged_at,
            acknowledged_by=a.acknowledged_by,
            resolved_at=a.resolved_at,
            resolved_by=a.resolved_by,
            resolution_note=a.resolution_note,
            closed_at=a.closed_at,
        )


class QualityAlertListResponse(BaseModel):
    data: list[QualityAlertRead]
    total: int


# ── Dashboard ───────────────────────────────────────────────────────────────

class QualityDashboardResponse(BaseModel):
    period_start: str
    period_end: str
    facility_id: str | None = None
    department_id: str | None = None
    kpis: list[dict]
    incidents: dict
    alerts: dict
    trends: list[dict]
    thresholds_count: int


class CheckThresholdsResponse(BaseModel):
    evaluated: int
    raised: int
    alerts: list[QualityAlertRead]
