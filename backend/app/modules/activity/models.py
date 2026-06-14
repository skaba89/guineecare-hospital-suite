from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db.base import Base


class ActivityEntry(Base):
    __tablename__ = "activity_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    actor_id = Column(String(36), ForeignKey('users.id'), nullable=True, index=True)
    action_name = Column(String(150), nullable=False, index=True)
    entity_type = Column(String(150), nullable=True, index=True)
    entity_id = Column(String(36), nullable=True, index=True)
    level = Column(String(50), default="NORMAL", nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
