from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text

from app.db.base import Base


class ClinicalNote(Base):
    __tablename__ = "clinical_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    admission_id = Column(String(36), ForeignKey('admissions.id'), index=True, nullable=True)
    note_type = Column(String(50), nullable=False)  # OBSERVATION, CONSULTATION, PRESCRIPTION, NOTE
    content = Column(Text, nullable=False)
    created_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=utcnow, nullable=True)


class PatientMeasurement(Base):
    __tablename__ = "patient_measurements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    admission_id = Column(String(36), ForeignKey('admissions.id'), index=True, nullable=True)
    measurement_type = Column(String(50), nullable=False)  # TEMPERATURE, BLOOD_PRESSURE, HEART_RATE, WEIGHT, HEIGHT, OXYGEN_SAT, PAIN_LEVEL, GLASGOW
    value = Column(String(100), nullable=False)  # valeur textuelle brute (ex: "120/80", "38.5")
    # v2.8.2 — P0-7 fix : valeur numérique pour charts/FHIR (NULL si composite comme "120/80")
    value_numeric = Column(Float, nullable=True)
    unit = Column(String(30), nullable=True)
    recorded_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    recorded_at = Column(DateTime, default=utcnow, nullable=False)


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    admission_id = Column(String(36), ForeignKey('admissions.id'), index=True, nullable=True)
    diagnosis_code = Column(String(50), nullable=True)  # CIM-10 code
    diagnosis_label = Column(String(255), nullable=False)
    diagnosis_type = Column(String(30), nullable=False)  # PRINCIPAL, SECONDARY, COMPLICATION
    status = Column(String(30), default="ACTIVE")  # ACTIVE, RESOLVED, CHRONIC
    created_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


# v2.6.0 — Phase 7 : Prescription structurée
# Modèle dédié pour les prescriptions médicamenteuses (au lieu du free-text
# ClinicalNote). Permet le handoff pharmacie + contrôle posologie + historique.
class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    admission_id = Column(String(36), ForeignKey('admissions.id'), index=True, nullable=True)
    clinical_note_id = Column(String(36), ForeignKey('clinical_notes.id'), index=True, nullable=True)
    # Médicament
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)  # ex: "500mg"
    frequency = Column(String(100), nullable=False)  # ex: "3 fois par jour"
    duration = Column(String(100), nullable=True)  # ex: "7 jours"
    quantity = Column(Float, nullable=True)  # quantité totale à dispenser
    # Instructions
    instructions = Column(Text, nullable=True)  # ex: "À prendre avec repas"
    # Statut
    status = Column(String(50), default="ACTIVE", nullable=False)  # ACTIVE, COMPLETED, CANCELLED
    # Métadonnées
    prescribed_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    prescribed_at = Column(DateTime, default=utcnow, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=utcnow, nullable=True)
