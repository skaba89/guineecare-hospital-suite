from fastapi import APIRouter

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


@router.get("/products")
def list_products():
    return {"data": [], "message": "products list"}


@router.post("/products")
def create_product(payload: dict):
    return {"data": payload, "message": "product created"}


@router.get("/stock")
def get_stock():
    return {"data": [], "message": "stock list"}


@router.post("/stock/movements")
def create_stock_movement(payload: dict):
    return {"data": payload, "message": "stock movement created"}
