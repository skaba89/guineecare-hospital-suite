from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db.base import Base


class EmergencyVisit(Base):
    __tablename__ = "emergency_visits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False, index=True)
    admission_id = Column(String(36), ForeignKey('admissions.id'), nullable=True, index=True)
    priority_level = Column(String(50), default="NORMAL", nullable=False)
    chief_complaint = Column(String(255), nullable=True)
    status = Column(String(50), default="WAITING", nullable=False)
    orientation = Column(String(100), nullable=True)
    attending_doctor_id = Column(String(36), ForeignKey('users.id'), nullable=True, index=True)
    vital_signs = Column(Text, nullable=True)  # JSON string with vital signs data
    treatment_notes = Column(Text, nullable=True)  # notes de traitement
    discharge_summary = Column(Text, nullable=True)  # compte rendu de sortie
    discharge_destination = Column(String(100), nullable=True)  # HOME, HOSPITALIZATION, TRANSFER, MORGUE
    seen_at = Column(DateTime, nullable=True)  # quand le patient a été vu par le médecin
    discharged_at = Column(DateTime, nullable=True)  # quand le patient a quitté les urgences
    arrived_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
