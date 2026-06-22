"""Pydantic schemas for the notifications module."""
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


Priority = Literal["low", "normal", "high", "urgent"]


def _channels_to_list(value: Any) -> list[str]:
    """Accept either a list, a CSV string, or None — return a clean list."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(c) for c in value if c]
    if isinstance(value, str):
        return [c for c in value.split(",") if c]
    # If it's a SQLAlchemy InstrumentedAttribute or similar, str() it
    return [c for c in str(value).split(",") if c]


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime | None = None
    recipient_id: str
    facility_id: str | None = None
    sender_id: str | None = None
    category: str
    priority: Priority = "normal"
    title: str
    body: str | None = None
    action_url: str | None = None
    channels: list[str] = Field(default_factory=list)
    in_app_delivered: bool = False
    email_delivered: bool = False
    sms_delivered: bool = False
    delivery_error: str | None = None
    read_at: datetime | None = None
    dismissed_at: datetime | None = None
    resource_type: str | None = None
    resource_id: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _convert_channels(cls, data: Any) -> Any:
        """Normalize channels from CSV string (SQLAlchemy) to list[str] (Pydantic).

        Also handles the case where `from_attributes=True` is used and the
        source object exposes a `channels_list` property (preferred) — we
        copy that to `channels` so Pydantic doesn't choke on the raw CSV string.
        """
        # Case 1: source is a SQLAlchemy model instance (from_attributes=True)
        if hasattr(data, "channels_list") and not isinstance(data, dict):
            # Use the property and replace channels
            try:
                # Pydantic v2: we can't mutate a non-dict source, so we return
                # a dict built from the model's to_dict() method.
                if hasattr(data, "to_dict"):
                    d = data.to_dict()
                    # to_dict already returns channels as a list
                    return d
            except Exception:
                pass

        # Case 2: source is a dict — convert channels if it's a string
        if isinstance(data, dict):
            if "channels" in data:
                data = {**data, "channels": _channels_to_list(data["channels"])}
        return data

    @computed_field  # type: ignore[misc]
    @property
    def is_read(self) -> bool:
        return self.read_at is not None


class NotificationSend(BaseModel):
    """Admin-only payload to send a notification to a user."""
    recipient_id: str = Field(..., description="User ID of the recipient")
    category: str = Field(..., max_length=32, description="e.g. system, lab_result, appointment")
    priority: Priority = "normal"
    title: str = Field(..., min_length=1, max_length=200)
    body: str | None = Field(None, max_length=4000)
    action_url: str | None = Field(None, max_length=500)
    channels: list[Literal["in_app", "email", "sms"]] = Field(
        default_factory=lambda: ["in_app"],
        description="Channels to attempt. in_app is always attempted.",
    )
    resource_type: str | None = Field(None, max_length=64)
    resource_id: str | None = Field(None, max_length=36)


class NotificationListResponse(BaseModel):
    data: list[NotificationRead]
    total: int
    page: int
    page_size: int
    total_pages: int
    unread_count: int


class UnreadCountResponse(BaseModel):
    unread_count: int
