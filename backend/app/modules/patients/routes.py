from fastapi import APIRouter

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("")
def list_patients():
    return {"data": [], "message": "patients list"}


@router.post("")
def create_patient(payload: dict):
    return {"data": payload, "message": "patient created"}


@router.get("/{patient_id}")
def get_patient(patient_id: str):
    return {"data": {"id": patient_id}, "message": "patient detail"}
