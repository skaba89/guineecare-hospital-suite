from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.facilities.models import Facility
from app.modules.facilities.schemas import FacilityCreate

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("")
def list_facilities(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.read")),
):
    facilities = db.query(Facility).order_by(Facility.name).all()
    return {"data": facilities, "message": "facilities list"}


@router.post("")
def create_facility(
    payload: FacilityCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.manage")),
):
    facility = Facility(**payload.dict())
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return {"data": facility, "message": "facility created"}
