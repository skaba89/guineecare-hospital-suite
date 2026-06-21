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
from app.modules.realtime import publish_kpi_update
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
    status: str | None = None,
    patient_id: str | None = None,
    test_id: str | None = None,
    priority: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    """Liste paginée des demandes laboratoire avec filtres serveur.

    Filtres : `status`, `patient_id`, `test_id`, `priority`,
    `date_from`/`date_to` (sur ordered_at), `search`.
    """
    query = tenant_query(db, LabOrder, current_user).order_by(LabOrder.ordered_at.desc())
    if pagination.search:
        query = query.filter(
            (LabOrder.status.ilike(f"%{pagination.search}%"))
            | (LabOrder.priority.ilike(f"%{pagination.search}%"))
        )
    if status:
        query = query.filter(LabOrder.status == status.upper())
    if patient_id:
        query = query.filter(LabOrder.patient_id == patient_id)
    if test_id:
        query = query.filter(LabOrder.test_id == test_id)
    if priority:
        query = query.filter(LabOrder.priority == priority.upper())
    if date_from:
        try:
            from datetime import datetime as _dt
            query = query.filter(LabOrder.ordered_at >= _dt.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime as _dt
            query = query.filter(LabOrder.ordered_at <= _dt.fromisoformat(date_to))
        except ValueError:
            pass
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
    # v1.3.0 — push realtime KPI update so the dashboard live-counts validated lab results
    publish_kpi_update(
        facility_id=row.facility_id or (order.facility_id if order else None) or "*",
        kpi="lab.results.validated.count",
        value=1,
        delta=1,
        extra={"result_id": row.id, "order_id": row.order_id},
    )
    return {"data": row, "message": "result validated"}


@router.get("/results")
def list_results(
    pagination: PaginationParams = Depends(),
    status: str | None = None,
    order_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    """Liste paginée des résultats labo avec filtres serveur.

    Filtres : `status`, `order_id`, `date_from`/`date_to` (sur entered_at), `search`.
    """
    query = tenant_query(db, LabResult, current_user).order_by(LabResult.entered_at.desc())
    if pagination.search:
        query = query.filter(
            (LabResult.result_value.ilike(f"%{pagination.search}%"))
            | (LabResult.status.ilike(f"%{pagination.search}%"))
        )
    if status:
        query = query.filter(LabResult.status == status.upper())
    if order_id:
        query = query.filter(LabResult.order_id == order_id)
    if date_from:
        try:
            from datetime import datetime as _dt
            query = query.filter(LabResult.entered_at >= _dt.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime as _dt
            query = query.filter(LabResult.entered_at <= _dt.fromisoformat(date_to))
        except ValueError:
            pass
    return paginate(query, pagination)
