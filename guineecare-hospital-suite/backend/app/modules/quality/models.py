from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db.base import Base


class QualityIndicator(Base):
    """Indicateur qualité (IPS, taux de mortalité, satisfaction, etc.)"""
    __tablename__ = "quality_indicators"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    code = Column(String(100), index=True, nullable=False)  # e.g. IPS, TMR24, SAT_PATIENT
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)  # SAFETY, EFFICIENCY, PATIENT_EXPERIENCE, CLINICAL_OUTCOME
    description = Column(Text, nullable=True)
    unit = Column(String(50), nullable=True)  # %, rate, count, score
    target_value = Column(String(50), nullable=True)
    frequency = Column(String(50), default="MONTHLY")  # DAILY, WEEKLY, MONTHLY, QUARTERLY, YEARLY
    created_at = Column(DateTime, default=utcnow, nullable=False)


class QualityMeasurement(Base):
    """Mesure/valeur d'un indicateur qualité pour une période"""
    __tablename__ = "quality_measurements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    indicator_id = Column(String(36), ForeignKey('quality_indicators.id'), index=True, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    value = Column(String(100), nullable=False)
    numerator = Column(String(100), nullable=True)
    denominator = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    recorded_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class IncidentReport(Base):
    """Déclaration d'événement indésirable (EI)"""
    __tablename__ = "incident_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    reported_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=True)
    incident_date = Column(DateTime, nullable=False)
    incident_type = Column(String(100), nullable=False)  # FALL, MEDICATION_ERROR, NOSOCOMIAL_INFECTION, EQUIPMENT_FAILURE, OTHER
    severity = Column(String(50), default="MINOR")  # NEAR_MISS, MINOR, MODERATE, MAJOR, CRITICAL
    description = Column(Text, nullable=False)
    immediate_actions = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    corrective_actions = Column(Text, nullable=True)
    status = Column(String(50), default="REPORTED")  # REPORTED, UNDER_INVESTIGATION, RESOLVED, CLOSED
    created_at = Column(DateTime, default=utcnow, nullable=False)
