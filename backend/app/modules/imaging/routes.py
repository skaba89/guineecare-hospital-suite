from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.imaging.schemas import (
    ImagingOrderCreate,
    ImagingResultCreate,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/imaging", tags=["imaging"])


# ── Imaging Orders ────────────────────────────────────────────────────

@router.get("/orders")
def list_imaging_orders(
    patient_id: str | None = None,
    status: str | None = None,
    exam_type: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.read")),
):
    query = tenant_query(db, ImagingOrder, current_user)
    if patient_id:
        query = query.filter(ImagingOrder.patient_id == patient_id)
    if status:
        query = query.filter(ImagingOrder.status == status)
    if exam_type:
        query = query.filter(ImagingOrder.exam_type == exam_type)
    query = query.order_by(ImagingOrder.ordered_at.desc())
    return paginate(query, pagination)


@router.post("/orders")
def create_imaging_order(
    payload: ImagingOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    if not data.get("requesting_doctor_id"):
        data["requesting_doctor_id"] = current_user.id
    row = ImagingOrder(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="imaging.order_created",
        entity_type="imaging_order",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "imaging order created"}


@router.get("/orders/{order_id}")
def get_imaging_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.read")),
):
    row = db.query(ImagingOrder).filter(ImagingOrder.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Imaging order not found")
    enforce_facility_access(current_user, row.facility_id)
    return {"data": row, "message": "imaging order detail"}


@router.post("/orders/{order_id}/start")
def start_imaging_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.manage")),
):
    row = db.query(ImagingOrder).filter(ImagingOrder.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Imaging order not found")
    enforce_facility_access(current_user, row.facility_id)
    if row.status != "PENDING":
        raise HTTPException(status_code=409, detail="Order is not in PENDING status")

    row.status = "IN_PROGRESS"
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="imaging.order_started",
        entity_type="imaging_order",
        entity_id=row.id,
        level="NORMAL",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "imaging order started"}


@router.post("/orders/{order_id}/complete")
def complete_imaging_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.manage")),
):
    row = db.query(ImagingOrder).filter(ImagingOrder.id == order_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Imaging order not found")
    enforce_facility_access(current_user, row.facility_id)
    if row.status != "IN_PROGRESS":
        raise HTTPException(status_code=409, detail="Order is not in IN_PROGRESS status")

    row.status = "COMPLETED"
    row.performed_at = utcnow()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="imaging.order_completed",
        entity_type="imaging_order",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "imaging order completed"}


# ── Imaging Results ───────────────────────────────────────────────────

@router.get("/results")
def list_imaging_results(
    patient_id: str | None = None,
    order_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.read")),
):
    query = tenant_query(db, ImagingResult, current_user)
    if patient_id:
        query = query.filter(ImagingResult.patient_id == patient_id)
    if order_id:
        query = query.filter(ImagingResult.order_id == order_id)
    query = query.order_by(ImagingResult.created_at.desc())
    return paginate(query, pagination)


@router.post("/results")
def create_imaging_result(
    payload: ImagingResultCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.manage")),
):
    order = db.query(ImagingOrder).filter(ImagingOrder.id == payload.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Imaging order not found")
    enforce_facility_access(current_user, order.facility_id)

    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = order.facility_id
    if not data.get("patient_id"):
        data["patient_id"] = order.patient_id
    if not data.get("radiologist_id"):
        data["radiologist_id"] = current_user.id
    row = ImagingResult(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="imaging.result_created",
        entity_type="imaging_result",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "imaging result created"}


@router.post("/results/{result_id}/validate")
def validate_imaging_result(
    result_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.manage")),
):
    row = db.query(ImagingResult).filter(ImagingResult.id == result_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Imaging result not found")
    enforce_facility_access(current_user, row.facility_id)
    if row.status == "VALIDATED":
        raise HTTPException(status_code=409, detail="Result already validated")

    row.status = "VALIDATED"
    row.validated_at = utcnow()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="imaging.result_validated",
        entity_type="imaging_result",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "imaging result validated"}
