from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db.base import Base


class ImagingOrder(Base):
    """Prescription d'examen d'imagerie"""
    __tablename__ = "imaging_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    requesting_doctor_id = Column(String(36), ForeignKey('users.id'), index=True, nullable=True)
    exam_type = Column(String(100), nullable=False)  # RADIOGRAPHY, CT_SCAN, MRI, ULTRASOUND, MAMMOGRAPHY, SCINTIGRAPHY
    body_region = Column(String(255), nullable=False)  # e.g. "Thorax", "Abdomen", "Crâne"
    clinical_info = Column(Text, nullable=True)  # motif de la demande / info clinique
    urgency = Column(String(50), default="ROUTINE")  # ROUTINE, URGENT, EMERGENCY
    status = Column(String(50), default="PENDING")  # PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    ordered_at = Column(DateTime, default=utcnow, nullable=False)
    performed_at = Column(DateTime, nullable=True)
    reported_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class ImagingResult(Base):
    """Résultat / compte rendu d'examen d'imagerie"""
    __tablename__ = "imaging_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    order_id = Column(String(36), ForeignKey('imaging_orders.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    radiologist_id = Column(String(36), ForeignKey('users.id'), index=True, nullable=True)
    findings = Column(Text, nullable=True)  # résultats / constatations
    conclusion = Column(Text, nullable=True)  # conclusion du radiologue
    recommendation = Column(Text, nullable=True)  # recommandations
    status = Column(String(50), default="DRAFT")  # DRAFT, VALIDATED, AMENDED
    created_at = Column(DateTime, default=utcnow, nullable=False)
    validated_at = Column(DateTime, nullable=True)
