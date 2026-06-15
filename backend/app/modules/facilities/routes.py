from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import enforce_facility_access, tenant_query
from app.db.session import get_db
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.facilities.models import Facility
from app.modules.facilities.schemas import FacilityCreate, FacilityUpdate

router = APIRouter(prefix="/facilities", tags=["facilities"])


@router.get("")
def list_facilities(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.read")),
):
    # SUPER_ADMIN sees all facilities; others see only their own
    if current_user.role == "SUPER_ADMIN":
        query = db.query(Facility).order_by(Facility.name)
    else:
        query = db.query(Facility).filter(
            Facility.id == current_user.facility_id
        ).order_by(Facility.name)

    if pagination.search:
        search_filter = (
            (Facility.name.ilike(f"%{pagination.search}%"))
            | (Facility.code.ilike(f"%{pagination.search}%"))
        )
        query = query.filter(search_filter)
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
    return {"data": facility, "message": "Établissement créé"}


@router.get("/{facility_id}")
def get_facility(
    facility_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.read")),
):
    enforce_facility_access(current_user, facility_id)
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Établissement non trouvé")
    return {"data": facility}


@router.put("/{facility_id}")
def update_facility(
    facility_id: str,
    payload: FacilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.manage")),
):
    enforce_facility_access(current_user, facility_id)
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Établissement non trouvé")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(facility, key, value)
    db.commit()
    db.refresh(facility)
    return {"data": facility, "message": "Établissement mis à jour"}
