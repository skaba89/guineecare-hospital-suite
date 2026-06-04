from pydantic import BaseModel


class LabTestCreate(BaseModel):
    facility_id: str
    code: str
    name: str
    category: str | None = None
    sample_type: str | None = None


class LabOrderCreate(BaseModel):
    facility_id: str
    patient_id: str
    admission_id: str | None = None
    test_id: str
    priority: str = "NORMAL"


class LabResultCreate(BaseModel):
    facility_id: str
    result_value: str
    interpretation: str | None = None
