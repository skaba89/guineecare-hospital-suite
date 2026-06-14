from datetime import date
from typing import Optional

from pydantic import BaseModel


class PatientCreate(BaseModel):
    facility_id: str
    patient_number: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    national_id: Optional[str] = None
    insurance_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class PatientRead(BaseModel):
    id: str
    facility_id: str
    patient_number: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    national_id: Optional[str] = None
    insurance_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    status: str

    class Config:
        from_attributes = True
