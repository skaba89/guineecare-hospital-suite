from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String

from app.db.base import Base


class Admission(Base):
    __tablename__ = "admissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(String(36), nullable=False, index=True)
    department_id = Column(String(36), nullable=True, index=True)
    admission_type = Column(String(50), nullable=False)
    status = Column(String(50), default="OPEN", nullable=False)
    admitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)
