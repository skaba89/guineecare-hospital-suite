from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Constantes pour les valeurs par défaut "Non renseigné"
# (évite les champs vides en base — important pour la traçabilité médicale)
DEFAULT_BLOOD_TYPE = "NON_RENSEIGNE"
DEFAULT_MEDICAL_TEXT = "Non renseigné"

# Groupes sanguins valides (système ABO + Rhésus)
BLOOD_TYPES = [
    "NON_RENSEIGNE",
    "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-",
]


class PatientCreate(BaseModel):
    facility_id: Optional[str] = None
    patient_number: Optional[str] = None
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

    # v1.7.1 — Champs médicaux (tous avec valeur par défaut explicite)
    blood_type: str = Field(
        default=DEFAULT_BLOOD_TYPE,
        description="Groupe sanguin ABO+Rh : A+, A-, B+, B-, AB+, AB-, O+, O- ou NON_RENSEIGNE",
    )
    allergies: str = Field(
        default=DEFAULT_MEDICAL_TEXT,
        description="Allergies connues. 'Non renseigné' si inconnu à la création.",
    )
    medical_history: str = Field(
        default=DEFAULT_MEDICAL_TEXT,
        description="Antécédents médicaux (chirurgicaux, familiaux). 'Non renseigné' si inconnu.",
    )
    current_medication: str = Field(
        default=DEFAULT_MEDICAL_TEXT,
        description="Traitement en cours. 'Non renseigné' si inconnu.",
    )
    chronic_conditions: str = Field(
        default=DEFAULT_MEDICAL_TEXT,
        description="Maladies chroniques (diabète, HTA, etc.). 'Non renseigné' si inconnu.",
    )

    # Convertir les chaînes vides en None (le frontend SimpleForm envoie "" pour les champs vides)
    @field_validator("date_of_birth", "gender", "phone", "address", "national_id",
                     "insurance_number", "emergency_contact_name", "emergency_contact_phone",
                     "facility_id", "patient_number", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "" or v is None:
            return None
        return v


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

    # v1.7.1 — Champs médicaux
    blood_type: str = DEFAULT_BLOOD_TYPE
    allergies: str = DEFAULT_MEDICAL_TEXT
    medical_history: str = DEFAULT_MEDICAL_TEXT
    current_medication: str = DEFAULT_MEDICAL_TEXT
    chronic_conditions: str = DEFAULT_MEDICAL_TEXT

    model_config = ConfigDict(from_attributes=True)
