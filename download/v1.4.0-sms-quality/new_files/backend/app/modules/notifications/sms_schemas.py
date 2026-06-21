"""Pydantic schemas pour le module SMS v1.4.0."""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── SmsProvider ─────────────────────────────────────────────────────────────

class SmsProviderCreate(BaseModel):
    code: Literal["mock", "orange", "mtn", "moov"] = Field(
        ..., description="Code court identifiant l'opérateur"
    )
    name: str = Field(..., min_length=1, max_length=128)
    enabled: bool = True
    api_url: str | None = Field(None, max_length=512)
    api_key: str | None = Field(None, description="Clé API (sera chiffrée côté service)")
    api_secret: str | None = Field(None, description="Secret API (sera chiffré côté service)")
    sender_id: str | None = Field(None, max_length=32, description="Sender ID ou numéro court")
    cost_per_sms_gnf: int = Field(0, ge=0, description="Coût par SMS en Franc Guinéen")
    rate_per_second: int = Field(10, ge=1, le=100, description="Limite de débit (SMS/s)")
    daily_quota: int | None = Field(None, ge=1, description="Quota quotidien (null = illimité)")


class SmsProviderUpdate(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    api_url: str | None = None
    api_key: str | None = Field(None, description="Nouvelle clé (écrase l'existante si fournie)")
    api_secret: str | None = None
    sender_id: str | None = None
    cost_per_sms_gnf: int | None = None
    rate_per_second: int | None = None
    daily_quota: int | None = None


class SmsProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    enabled: bool
    api_url: str | None = None
    sender_id: str | None = None
    cost_per_sms_gnf: int
    rate_per_second: int
    daily_quota: int | None = None
    has_api_key: bool = False
    has_api_secret: bool = False
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, p) -> "SmsProviderRead":
        """Construit le schéma depuis un SmsProvider en incluant les flags has_*."""
        return cls(
            id=p.id,
            code=p.code,
            name=p.name,
            enabled=bool(p.enabled),
            api_url=p.api_url,
            sender_id=p.sender_id,
            cost_per_sms_gnf=p.cost_per_sms_gnf or 0,
            rate_per_second=p.rate_per_second,
            daily_quota=p.daily_quota,
            has_api_key=bool(p.api_key_encrypted),
            has_api_secret=bool(p.api_secret_encrypted),
            created_at=p.created_at,
            updated_at=p.updated_at,
        )


class SmsProviderListResponse(BaseModel):
    data: list[SmsProviderRead]
    total: int


# ── SmsRoutingRule ──────────────────────────────────────────────────────────

class SmsRoutingRuleCreate(BaseModel):
    facility_id: str | None = None
    category: str = Field(..., min_length=1, max_length=32)
    channels: list[Literal["in_app", "sms", "email"]] = Field(
        default_factory=lambda: ["in_app"]
    )
    min_priority: Literal["low", "normal", "high", "urgent"] = "normal"
    preferred_provider_id: str | None = None
    enabled: bool = True
    description: str | None = None


class SmsRoutingRuleUpdate(BaseModel):
    channels: list[Literal["in_app", "sms", "email"]] | None = None
    min_priority: Literal["low", "normal", "high", "urgent"] | None = None
    preferred_provider_id: str | None = None
    enabled: bool | None = None
    description: str | None = None


class SmsRoutingRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    facility_id: str | None = None
    category: str
    channels: list[str] = Field(default_factory=list)
    min_priority: str
    preferred_provider_id: str | None = None
    enabled: bool
    description: str | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, r) -> "SmsRoutingRuleRead":
        return cls(
            id=r.id,
            facility_id=r.facility_id,
            category=r.category,
            channels=[c for c in (r.channels or "").split(",") if c],
            min_priority=r.min_priority,
            preferred_provider_id=r.preferred_provider_id,
            enabled=bool(r.enabled),
            description=r.description,
            created_at=r.created_at,
        )


class SmsRoutingRuleListResponse(BaseModel):
    data: list[SmsRoutingRuleRead]
    total: int


# ── SmsMessage ──────────────────────────────────────────────────────────────

class SmsSendRequest(BaseModel):
    """Payload d'envoi manuel (admin only) — utile pour les tests et rappels."""
    to: str = Field(..., min_length=6, max_length=32, description="Numéro E.164")
    body: str = Field(..., min_length=1, max_length=480)
    category: str = Field("manual", max_length=32)
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    recipient_id: str | None = None
    facility_id: str | None = None
    provider_id: str | None = Field(None, description="Surcharge la règle de routage")


class SmsMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    facility_id: str | None = None
    provider_id: str | None = None
    provider_code: str
    recipient_id: str | None = None
    recipient_phone: str
    body: str
    category: str
    priority: str
    notification_id: str | None = None
    status: str
    operator_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    cost_gnf: int
    attempts: int
    sent_at: datetime | None = None
    delivered_at: datetime | None = None


class SmsMessageListResponse(BaseModel):
    data: list[SmsMessageRead]
    total: int
    page: int
    page_size: int


class SmsStatsResponse(BaseModel):
    since: str
    total: int
    sent: int
    failed: int
    pending: int
    rejected: int
    success_rate_pct: float
    total_cost_gnf: int
    by_provider: list[dict]
    by_category: list[dict]


class SmsProviderTestRequest(BaseModel):
    """Teste un provider en envoyant un SMS à un numéro de test."""
    to: str = Field(..., description="Numéro E.164 du destinataire de test")
    body: str | None = Field(None, max_length=480, description="Message (défaut: 'Test GuinéeCare v1.4')")


class SmsProviderTestResponse(BaseModel):
    success: bool
    message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    cost_gnf: int = 0
