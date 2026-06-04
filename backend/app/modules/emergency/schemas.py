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
