from datetime import datetime

from pydantic import BaseModel


# ── ClinicalNote ──────────────────────────────────────────────

class ClinicalNoteCreate(BaseModel):
    facility_id: str | None = None  # auto-inféré depuis le patient si absent
    admission_id: str | None = None
    note_type: str  # OBSERVATION, CONSULTATION, PRESCRIPTION, NOTE
    content: str


class ClinicalNoteRead(BaseModel):
    id: str
    facility_id: str
    patient_id: str
    admission_id: str | None = None
    note_type: str
    content: str
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


# ── PatientMeasurement ────────────────────────────────────────

class PatientMeasurementCreate(BaseModel):
    facility_id: str | None = None  # auto-inféré depuis le patient si absent
    admission_id: str | None = None
    measurement_type: str  # TEMPERATURE, BLOOD_PRESSURE, HEART_RATE, WEIGHT, HEIGHT, OXYGEN_SAT, PAIN_LEVEL, GLASGOW
    value: str
    unit: str | None = None


class PatientMeasurementRead(BaseModel):
    id: str
    facility_id: str
    patient_id: str
    admission_id: str | None = None
    measurement_type: str
    value: str
    unit: str | None = None
    recorded_by: str | None = None
    recorded_at: datetime

    class Config:
        from_attributes = True


# ── Diagnosis ─────────────────────────────────────────────────

class DiagnosisCreate(BaseModel):
    facility_id: str | None = None  # auto-inféré depuis le patient si absent
    admission_id: str | None = None
    diagnosis_code: str | None = None  # CIM-10 code
    diagnosis_label: str
    diagnosis_type: str  # PRINCIPAL, SECONDARY, COMPLICATION
    status: str = "ACTIVE"  # ACTIVE, RESOLVED, CHRONIC


class DiagnosisRead(BaseModel):
    id: str
    facility_id: str
    patient_id: str
    admission_id: str | None = None
    diagnosis_code: str | None = None
    diagnosis_label: str
    diagnosis_type: str
    status: str
    created_by: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# v2.8.1 — P1-6 : Pydantic schemas pour prescriptions structurées

class PrescriptionCreate(BaseModel):
    patient_id: str
    admission_id: str | None = None
    clinical_note_id: str | None = None
    medication_name: str
    dosage: str
    frequency: str
    duration: str | None = None
    quantity: float | None = None
    instructions: str | None = None
