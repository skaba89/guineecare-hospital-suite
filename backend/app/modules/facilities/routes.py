from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.db.session import get_db
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.facilities.models import Facility
from app.modules.facilities.schemas import FacilityCreate

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("")
def list_facilities(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.read")),
):
    query = db.query(Facility).order_by(Facility.name)
    if pagination.search:
        query = query.filter(
            (Facility.name.ilike(f"%{pagination.search}%"))
            | (Facility.code.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("")
def create_facility(
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.manage")),
):
    facility = Facility(**payload.model_dump())
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return {"data": facility, "message": "facility created"}
