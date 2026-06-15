from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.laboratory.schemas import LabOrderCreate, LabResultCreate, LabTestCreate
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/laboratory", tags=["laboratory"])


@router.get("/tests")
def list_tests(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    query = tenant_query(db, LabTest, current_user).order_by(LabTest.name)
    if pagination.search:
        query = query.filter(
            (LabTest.name.ilike(f"%{pagination.search}%"))
            | (LabTest.code.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/tests")
def create_test(
    payload: LabTestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = LabTest(**data)
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
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = LabOrder(**data, ordered_by=current_user.id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "lab order created"}


@router.get("/orders")
def list_orders(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    query = tenant_query(db, LabOrder, current_user).order_by(LabOrder.ordered_at.desc())
    if pagination.search:
        query = query.filter(
            (LabOrder.status.ilike(f"%{pagination.search}%"))
            | (LabOrder.priority.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


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
    enforce_facility_access(current_user, order.facility_id)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = order.facility_id
    row = LabResult(**data, order_id=order_id, entered_by=current_user.id)
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
    enforce_facility_access(current_user, row.facility_id)
    row.status = "VALIDATED"
    row.validated_by = current_user.id
    row.validated_at = utcnow()
    order = db.query(LabOrder).filter(LabOrder.id == row.order_id).first()
    if order:
        order.status = "VALIDATED"
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "result validated"}


@router.get("/results")
def list_results(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    query = tenant_query(db, LabResult, current_user).order_by(LabResult.entered_at.desc())
    if pagination.search:
        query = query.filter(
            (LabResult.result_value.ilike(f"%{pagination.search}%"))
            | (LabResult.status.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)
