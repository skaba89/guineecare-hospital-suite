from pydantic import BaseModel


class AdmissionCreate(BaseModel):
    facility_id: str
    patient_id: str
    department_id: str | None = None
    admission_type: str


class AdmissionRead(BaseModel):
    id: str
    facility_id: str
    patient_id: str
    department_id: str | None = None
    admission_type: str
    status: str

    class Config:
        from_attributes = True
