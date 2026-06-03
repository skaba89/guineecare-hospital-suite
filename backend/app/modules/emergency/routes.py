from fastapi import APIRouter

router = APIRouter(prefix="/emergency", tags=["emergency"])


@router.get("/queue")
def get_emergency_queue():
    return {"data": [], "message": "emergency queue"}


@router.post("/visits")
def create_emergency_visit(payload: dict):
    return {"data": payload, "message": "emergency visit created"}


@router.post("/visits/{visit_id}/triage")
def triage_visit(visit_id: str, payload: dict):
    return {"data": {"id": visit_id, "triage": payload}, "message": "triage saved"}


@router.post("/visits/{visit_id}/orientation")
def orient_visit(visit_id: str, payload: dict):
    return {"data": {"id": visit_id, "orientation": payload}, "message": "orientation saved"}
