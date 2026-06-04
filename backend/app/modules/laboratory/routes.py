from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.laboratory.schemas import LabOrderCreate, LabResultCreate, LabTestCreate
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/laboratory", tags=["laboratory"])


@router.get("/tests")
def list_tests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    rows = db.query(LabTest).order_by(LabTest.name).all()
    return {"data": rows, "message": "lab tests list"}


@router.post("/tests")
def create_test(
    payload: LabTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.manage")),
):
    row = LabTest(**payload.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "lab test created"}


@router.post("/orders")
def create_order(
    payload: LabOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.order")),
):
    test = db.query(LabTest).filter(LabTest.id == payload.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    row = LabOrder(**payload.dict(), ordered_by=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "lab order created"}


@router.get("/orders")
def list_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    rows = db.query(LabOrder).order_by(LabOrder.ordered_at.desc()).all()
    return {"data": rows, "message": "lab orders list"}


@router.post("/orders/{order_id}/results")
def create_result(
    order_id: str,
    payload: LabResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.result")),
):
    order = db.query(LabOrder).filter(LabOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    row = LabResult(**payload.dict(), order_id=order_id, entered_by=current_user.id)
    order.status = "RESULT_ENTERED"
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "result saved"}


@router.post("/results/{result_id}/validate")
def validate_result(
    result_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.validate")),
):
    row = db.query(LabResult).filter(LabResult.id == result_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Lab result not found")
    row.status = "VALIDATED"
    row.validated_by = current_user.id
    row.validated_at = datetime.utcnow()
    order = db.query(LabOrder).filter(LabOrder.id == row.order_id).first()
    if order:
        order.status = "VALIDATED"
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "result validated"}
