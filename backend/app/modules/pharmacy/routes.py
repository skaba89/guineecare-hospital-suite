from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.db.session import get_db
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement
from app.modules.pharmacy.schemas import PharmacyProductCreate, StockMovementCreate
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


@router.get("/products")
def list_products(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.read")),
):
    query = db.query(PharmacyProduct).order_by(PharmacyProduct.name)
    if pagination.search:
        query = query.filter(
            (PharmacyProduct.name.ilike(f"%{pagination.search}%"))
            | (PharmacyProduct.code.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/products")
def create_product(
    payload: PharmacyProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.manage")),
):
    row = PharmacyProduct(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "product created"}


@router.get("/stock")
def get_stock(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.read")),
):
    query = db.query(PharmacyStock).order_by(PharmacyStock.updated_at.desc())
    if pagination.search:
        query = query.filter(PharmacyStock.product_id.ilike(f"%{pagination.search}%"))
    return paginate(query, pagination)


@router.post("/stock/movements")
def create_stock_movement(
    payload: StockMovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("pharmacy.manage")),
):
    product = db.query(PharmacyProduct).filter(PharmacyProduct.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    stock = db.query(PharmacyStock).filter(
        PharmacyStock.facility_id == payload.facility_id,
        PharmacyStock.product_id == payload.product_id,
    ).first()
    if not stock:
        stock = PharmacyStock(
            facility_id=payload.facility_id,
            product_id=payload.product_id,
            quantity_available=0,
            min_threshold=payload.min_threshold,
        )
        db.add(stock)
        db.flush()

    if payload.movement_type.upper() == "IN":
        stock.quantity_available += payload.quantity
    elif payload.movement_type.upper() == "OUT":
        if stock.quantity_available < payload.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        stock.quantity_available -= payload.quantity
    else:
        raise HTTPException(status_code=400, detail="movement_type must be IN or OUT")

    stock.updated_at = utcnow()
    movement = StockMovement(
        facility_id=payload.facility_id,
        product_id=payload.product_id,
        movement_type=payload.movement_type.upper(),
        quantity=payload.quantity,
        reason=payload.reason,
        performed_by=current_user.id,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    db.refresh(stock)
    return {"data": {"movement": movement, "stock": stock}, "message": "stock movement created"}
