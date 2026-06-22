from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text

from app.db.base import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), nullable=False, index=True)
    patient_number = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(10), nullable=True)
    phone = Column(String(30), nullable=True)
    address = Column(Text, nullable=True)
    national_id = Column(String(50), nullable=True, unique=True)
    insurance_number = Column(String(100), nullable=True)
    emergency_contact_name = Column(String(150), nullable=True)
    emergency_contact_phone = Column(String(30), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # v1.7.1 — Champs médicaux (avec valeurs par défaut "Non renseigné" pour
    # ne jamais laisser vide un champ à la création. Le soignant pourra mettre
    # à jour ces champs ultérieurement via le DPI patient.)
    blood_type = Column(String(10), nullable=False, default="NON_RENSEIGNE")
    # blood_type : A+ | A- | B+ | B- | AB+ | AB- | O+ | O- | NON_RENSEIGNE
    allergies = Column(Text, nullable=False, default="Non renseigné")
    medical_history = Column(Text, nullable=False, default="Non renseigné")
    # antécédents médicaux (chirurgical, familial, etc.)
    current_medication = Column(Text, nullable=False, default="Non renseigné")
    # traitement en cours
    chronic_conditions = Column(Text, nullable=False, default="Non renseigné")
    # maladies chroniques (diabète, HTA, etc.)
