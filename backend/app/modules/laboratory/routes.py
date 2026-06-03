from fastapi import APIRouter

router = APIRouter(prefix="/laboratory", tags=["laboratory"])


@router.get("/tests")
def list_tests():
    return {"data": [], "message": "lab tests list"}


@router.post("/orders")
def create_order(payload: dict):
    return {"data": payload, "message": "lab order created"}


@router.post("/orders/{order_id}/results")
def create_result(order_id: str, payload: dict):
    return {"data": {"order_id": order_id, "result": payload}, "message": "result saved"}


@router.post("/results/{result_id}/validate")
def validate_result(result_id: str):
    return {"data": {"id": result_id, "status": "validated"}, "message": "result validated"}
