"""SQLAlchemy models for the user_profile module (v1.1.0).

Three tables, all keyed by user_id (FK → users.id):

- `user_preferences` — one row per user. Stores locale, theme, page size,
  dashboard refresh interval. Updated via PUT /me/preferences.
- `user_feedback` — append-only feedback entries submitted by users.
  Used by the change-management loop to collect bug reports, suggestions,
  questions, and praise per facility.
- `user_recent_items` — sliding-window history of recently viewed resources
  (patients, lab orders, etc.). Capped at MAX_RECENT_ITEMS per user; older
  rows are pruned on insert.
"""
import json
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# Maximum number of recent items kept per user. Older rows are pruned on insert.
MAX_RECENT_ITEMS = 50


class UserPreference(Base):
    """Per-user UI / behavior preferences. One row per user (1:1)."""

    __tablename__ = "user_preferences"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_preferences_user_id"),)

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, unique=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # UI / locale
    locale = Column(String(8), nullable=False, default="fr")  # fr|en
    theme = Column(String(16), nullable=False, default="light")  # light|dark|auto

    # Pagination default
    default_page_size = Column(Integer, nullable=False, default=20)  # 5..200

    # Dashboard auto-refresh interval in seconds (0 = disabled)
    dashboard_refresh_seconds = Column(Integer, nullable=False, default=30)

    # Free-form JSON bag for forward-compat (e.g. pinned modules, layout)
    extra = Column(Text, nullable=True)

    user = relationship("User", backref="preferences_row", lazy="select")

    def get_extra(self) -> dict:
        if not self.extra:
            return {}
        try:
            return json.loads(self.extra)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_extra(self, value: dict | None) -> None:
        self.extra = json.dumps(value, ensure_ascii=False) if value else None

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "locale": self.locale,
            "theme": self.theme,
            "default_page_size": self.default_page_size,
            "dashboard_refresh_seconds": self.dashboard_refresh_seconds,
            "extra": self.get_extra(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserFeedback(Base):
    """Append-only user feedback entries. Used by the change-management loop."""

    __tablename__ = "user_feedback"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=True, index=True)

    # Classification
    category = Column(String(32), nullable=False, index=True)  # bug|suggestion|question|praise
    priority = Column(String(16), nullable=False, default="normal")  # low|normal|high|urgent
    status = Column(String(16), nullable=False, default="open", index=True)  # open|triaged|resolved|wontfix

    # Content
    subject = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)

    # Context (auto-captured from the request)
    page_url = Column(String(500), nullable=True)
    user_agent = Column(String(512), nullable=True)

    # Admin response
    admin_response = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], lazy="select")
    resolver = relationship("User", foreign_keys=[resolved_by], lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "user_id": self.user_id,
            "facility_id": self.facility_id,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "subject": self.subject,
            "message": self.message,
            "page_url": self.page_url,
            "user_agent": self.user_agent,
            "admin_response": self.admin_response,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
        }


class UserRecentItem(Base):
    """Sliding-window history of recently viewed resources per user.

    Capped at MAX_RECENT_ITEMS rows per user — older entries are pruned
    when a new entry is recorded for the same (user_id, resource_type, resource_id)
    triple. Re-visiting the same resource bubbles it to the top.
    """

    __tablename__ = "user_recent_items"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    resource_type = Column(String(32), nullable=False)  # patient|lab_order|imaging_order|...
    resource_id = Column(String(36), nullable=False)
    resource_label = Column(String(200), nullable=True)  # denormalized for display
    viewed_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint(
            "user_id", "resource_type", "resource_id",
            name="uq_user_recent_user_resource",
        ),
    )

    user = relationship("User", backref="recent_items", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_label": self.resource_label,
            "viewed_at": self.viewed_at.isoformat() if self.viewed_at else None,
        }
