from pydantic import BaseModel


class PatientCreate(BaseModel):
    facility_id: str
    patient_number: str
    first_name: str
    last_name: str


class PatientRead(BaseModel):
    id: str
    facility_id: str
    patient_number: str
    first_name: str
    last_name: str
    status: str

    class Config:
        from_attributes = True
