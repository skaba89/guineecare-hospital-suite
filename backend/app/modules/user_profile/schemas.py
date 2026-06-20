"""Pydantic schemas for the user_profile module (v1.1.0)."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


Locale = Literal["fr", "en"]
Theme = Literal["light", "dark", "auto"]
FeedbackCategory = Literal["bug", "suggestion", "question", "praise"]
FeedbackPriority = Literal["low", "normal", "high", "urgent"]
FeedbackStatus = Literal["open", "triaged", "resolved", "wontfix"]
ResourceType = Literal[
    "patient", "admission", "emergency_visit", "hospital_stay", "lab_order",
    "imaging_order", "surgery", "invoice", "incident", "staff",
]


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

class UserPreferencesRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    locale: Locale = "fr"
    theme: Theme = "light"
    default_page_size: int = 20
    dashboard_refresh_seconds: int = 30
    extra: dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime | None = None


class UserPreferencesUpdate(BaseModel):
    locale: Locale | None = None
    theme: Theme | None = None
    default_page_size: int | None = Field(None, ge=5, le=200)
    dashboard_refresh_seconds: int | None = Field(None, ge=0, le=600)
    extra: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------

class FeedbackCreate(BaseModel):
    category: FeedbackCategory
    priority: FeedbackPriority = "normal"
    subject: str | None = Field(None, max_length=200)
    message: str = Field(..., min_length=1, max_length=4000)
    page_url: str | None = Field(None, max_length=500)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime | None = None
    user_id: str
    facility_id: str | None = None
    category: FeedbackCategory
    priority: FeedbackPriority
    status: FeedbackStatus
    subject: str | None = None
    message: str
    page_url: str | None = None
    user_agent: str | None = None
    admin_response: str | None = None
    resolved_at: datetime | None = None
    resolved_by: str | None = None


class FeedbackListResponse(BaseModel):
    data: list[FeedbackRead]
    total: int
    page: int
    page_size: int


class FeedbackResolve(BaseModel):
    """Admin payload to triage / resolve a feedback entry."""
    status: FeedbackStatus
    admin_response: str | None = Field(None, max_length=4000)


# ---------------------------------------------------------------------------
# Recent items
# ---------------------------------------------------------------------------

class RecentItemCreate(BaseModel):
    resource_type: ResourceType
    resource_id: str = Field(..., min_length=1, max_length=36)
    resource_label: str | None = Field(None, max_length=200)


class RecentItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    resource_type: str
    resource_id: str
    resource_label: str | None = None
    viewed_at: datetime | None = None


class RecentItemListResponse(BaseModel):
    data: list[RecentItemRead]
    total: int
