from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String

from app.db.base import Base


class EmergencyVisit(Base):
    __tablename__ = "emergency_visits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(String(36), nullable=False, index=True)
    admission_id = Column(String(36), nullable=True, index=True)
    priority_level = Column(String(50), default="NORMAL", nullable=False)
    chief_complaint = Column(String(255), nullable=True)
    status = Column(String(50), default="WAITING", nullable=False)
    orientation = Column(String(100), nullable=True)
    arrived_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
