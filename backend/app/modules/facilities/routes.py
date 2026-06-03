from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.facilities.models import Facility
from app.modules.facilities.schemas import FacilityCreate

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("")
def list_facilities(db: Session = Depends(get_db)):
    facilities = db.query(Facility).order_by(Facility.name).all()
    return {"data": facilities, "message": "facilities list"}


@router.post("")
def create_facility(payload: FacilityCreate, db: Session = Depends(get_db)):
    facility = Facility(**payload.dict())
    db.add(facility)
    db.commit()
    db.refresh(facility)
    return {"data": facility, "message": "facility created"}
