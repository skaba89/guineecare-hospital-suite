from datetime import datetime

from pydantic import BaseModel


# ── MaternityRecord ──────────────────────────────────────────────

class MaternityRecordCreate(BaseModel):
    facility_id: str
    patient_id: str
    gravidity: str | None = None
    parity: str | None = None
    last_menstrual_period: datetime | None = None
    expected_due_date: datetime | None = None
    blood_type: str | None = None
    rh_factor: str | None = None
    allergies: str | None = None
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    status: str = "ACTIVE"  # ACTIVE, DELIVERED, CLOSED


class MaternityRecordRead(BaseModel):
    id: str
    facility_id: str
    patient_id: str
    gravidity: str | None = None
    parity: str | None = None
    last_menstrual_period: datetime | None = None
    expected_due_date: datetime | None = None
    blood_type: str | None = None
    rh_factor: str | None = None
    allergies: str | None = None
    risk_level: str
    status: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# ── MaternityConsultation ────────────────────────────────────────

class MaternityConsultationCreate(BaseModel):
    facility_id: str
    consultation_type: str  # PRENATAL, POSTNATAL, FOLLOW_UP
    gestational_age_weeks: float | None = None
    weight_kg: float | None = None
    blood_pressure: str | None = None
    fetal_heart_rate: float | None = None
    fundal_height_cm: float | None = None
    notes: str | None = None


class MaternityConsultationRead(BaseModel):
    id: str
    facility_id: str
    record_id: str
    consultation_type: str
    gestational_age_weeks: float | None = None
    weight_kg: float | None = None
    blood_pressure: str | None = None
    fetal_heart_rate: float | None = None
    fundal_height_cm: float | None = None
    notes: str | None = None
    consulted_by: str | None = None
    consulted_at: datetime

    class Config:
        from_attributes = True


# ── DeliveryRecord ───────────────────────────────────────────────

class DeliveryRecordCreate(BaseModel):
    facility_id: str
    delivery_type: str  # VAGINAL, CESAREAN, ASSISTED
    delivery_date: datetime
    gestational_age_weeks: float | None = None
    complications: str | None = None
    baby_gender: str | None = None
    baby_weight_kg: float | None = None
    baby_apgar_1: str | None = None
    baby_apgar_5: str | None = None
    baby_health_status: str | None = None
    notes: str | None = None


class DeliveryRecordRead(BaseModel):
    id: str
    facility_id: str
    record_id: str
    delivery_type: str
    delivery_date: datetime
    gestational_age_weeks: float | None = None
    complications: str | None = None
    baby_gender: str | None = None
    baby_weight_kg: float | None = None
    baby_apgar_1: str | None = None
    baby_apgar_5: str | None = None
    baby_health_status: str | None = None
    performed_by: str | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
