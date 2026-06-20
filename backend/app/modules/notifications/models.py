"""Notifications models — in-app notifications with pluggable channel providers."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Recipient (required) — the user who will see this notification
    recipient_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=True, index=True)
    # Sender (optional — null for system-generated notifications)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Classification
    category = Column(String(32), nullable=False, index=True)
    priority = Column(String(16), nullable=False, default="normal")  # low|normal|high|urgent

    # Content
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=True)
    action_url = Column(String(500), nullable=True)

    # Channel delivery state
    channels = Column(String(64), nullable=False, default="in_app")  # csv: in_app,email,sms
    in_app_delivered = Column(Boolean, nullable=False, default=True)
    email_delivered = Column(Boolean, nullable=False, default=False)
    sms_delivered = Column(Boolean, nullable=False, default=False)
    delivery_error = Column(Text, nullable=True)

    # Read state
    read_at = Column(DateTime, nullable=True, index=True)
    dismissed_at = Column(DateTime, nullable=True)

    # Optional domain reference
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(36), nullable=True)

    recipient = relationship("User", foreign_keys=[recipient_id], lazy="select")
    sender = relationship("User", foreign_keys=[sender_id], lazy="select")

    @property
    def channels_list(self) -> list[str]:
        """Parsed list of channel names from the CSV string. Used by Pydantic schema."""
        return [c for c in (self.channels or "").split(",") if c]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "recipient_id": self.recipient_id,
            "facility_id": self.facility_id,
            "sender_id": self.sender_id,
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "body": self.body,
            "action_url": self.action_url,
            "channels": [c for c in (self.channels or "").split(",") if c],
            "in_app_delivered": bool(self.in_app_delivered),
            "email_delivered": bool(self.email_delivered),
            "sms_delivered": bool(self.sms_delivered),
            "delivery_error": self.delivery_error,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "dismissed_at": self.dismissed_at.isoformat() if self.dismissed_at else None,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "is_read": self.read_at is not None,
        }
