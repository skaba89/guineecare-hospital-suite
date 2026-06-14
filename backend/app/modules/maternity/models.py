from app.core.datetime import utcnow
from sqlalchemy import Column, String, DateTime, Text, Float, ForeignKey
from datetime import datetime
from uuid import uuid4

from app.db.base import Base


class MaternityRecord(Base):
    __tablename__ = "maternity_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    gravidity = Column(String(10), nullable=True)  # Number of pregnancies
    parity = Column(String(10), nullable=True)  # Number of births
    last_menstrual_period = Column(DateTime, nullable=True)  # DDR
    expected_due_date = Column(DateTime, nullable=True)  # Date prevue accouchement
    blood_type = Column(String(10), nullable=True)
    rh_factor = Column(String(10), nullable=True)
    allergies = Column(Text, nullable=True)
    risk_level = Column(String(30), default="LOW")  # LOW, MEDIUM, HIGH
    status = Column(String(30), default="ACTIVE")  # ACTIVE, DELIVERED, CLOSED
    created_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=utcnow, nullable=True)


class MaternityConsultation(Base):
    __tablename__ = "maternity_consultations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    record_id = Column(String(36), ForeignKey('maternity_records.id'), index=True, nullable=False)
    consultation_type = Column(String(50), nullable=False)  # PRENATAL, POSTNATAL, FOLLOW_UP
    gestational_age_weeks = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    blood_pressure = Column(String(30), nullable=True)
    fetal_heart_rate = Column(Float, nullable=True)
    fundal_height_cm = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    consulted_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    consulted_at = Column(DateTime, default=utcnow, nullable=False)


class DeliveryRecord(Base):
    __tablename__ = "delivery_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    record_id = Column(String(36), ForeignKey('maternity_records.id'), index=True, nullable=False)
    delivery_type = Column(String(50), nullable=False)  # VAGINAL, CESAREAN, ASSISTED
    delivery_date = Column(DateTime, nullable=False)
    gestational_age_weeks = Column(Float, nullable=True)
    complications = Column(Text, nullable=True)
    baby_gender = Column(String(10), nullable=True)
    baby_weight_kg = Column(Float, nullable=True)
    baby_apgar_1 = Column(String(10), nullable=True)  # APGAR at 1 min
    baby_apgar_5 = Column(String(10), nullable=True)  # APGAR at 5 min
    baby_health_status = Column(String(50), nullable=True)
    performed_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
