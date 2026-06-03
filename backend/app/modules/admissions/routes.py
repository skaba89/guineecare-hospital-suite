from fastapi import APIRouter

router = APIRouter(prefix="/admissions", tags=["admissions"])


@router.get("")
def list_admissions():
    return {"data": [], "message": "admissions list"}


@router.post("")
def create_admission(payload: dict):
    return {"data": payload, "message": "admission created"}


@router.post("/{admission_id}/close")
def close_admission(admission_id: str):
    return {"data": {"id": admission_id, "status": "closed"}, "message": "admission closed"}
