from pydantic import BaseModel


class EmergencyVisitCreate(BaseModel):
    facility_id: str
    patient_id: str
    admission_id: str | None = None
    priority_level: str = "NORMAL"
    chief_complaint: str | None = None


class EmergencyTriageUpdate(BaseModel):
    priority_level: str


class EmergencyOrientationUpdate(BaseModel):
    orientation: str


class EmergencyCareUpdate(BaseModel):
    """Prise en charge médicale"""
    attending_doctor_id: str | None = None
    vital_signs: str | None = None  # JSON string
    treatment_notes: str | None = None


class EmergencyDischargeUpdate(BaseModel):
    """Sortie des urgences"""
    discharge_summary: str
    discharge_destination: str = "HOME"  # HOME, HOSPITALIZATION, TRANSFER, MORGUE
    orientation: str | None = None  # keep for backward compat
