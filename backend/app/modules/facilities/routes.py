from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.pagination import PaginationParams, paginate
from app.core.tenant import enforce_facility_access
from app.db.session import get_db
from app.modules.audit.service import audit_log
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.facilities.models import Facility
from app.modules.facilities.schemas import FacilityCreate, FacilityUpdate

router = APIRouter(prefix="/facilities", tags=["facilities"])


_GUINEA_GEO_PAIRS = (
    ("region", "admin_level_1"),
    ("prefecture", "admin_level_2"),
    ("commune", "admin_level_3"),
)


def _sync_country_geography(data: dict, facility: Facility | None = None) -> dict:
    """Keep Guinea legacy geography and generic levels compatible.

    Existing clients still send region/prefecture/commune. Newer clients can
    send admin_level_1..4. For GN deployments we mirror both representations,
    which lets national reporting continue to work during the migration.
    Other countries only use generic administrative levels.
    """
    country_code = str(
        data.get("country_code")
        or (getattr(facility, "country_code", None) if facility else None)
        or settings.country_code
    ).strip().upper()
    data["country_code"] = country_code

    if country_code == "GN":
        for legacy_key, generic_key in _GUINEA_GEO_PAIRS:
            legacy_value = data.get(legacy_key)
            generic_value = data.get(generic_key)
            if legacy_value and not generic_value:
                data[generic_key] = legacy_value
            elif generic_value and not legacy_value:
                data[legacy_key] = generic_value
    return data


def _facility_to_dict(facility: Facility) -> dict:
    return {
        "id": str(facility.id),
        "code": facility.code,
        "name": facility.name,
        "category": facility.category,
        "region": facility.region,
        "prefecture": facility.prefecture,
        "commune": facility.commune,
        "country_code": facility.country_code,
        "admin_level_1": facility.admin_level_1,
        "admin_level_2": facility.admin_level_2,
        "admin_level_3": facility.admin_level_3,
        "admin_level_4": facility.admin_level_4,
        "health_district": facility.health_district,
        "facility_type_code": facility.facility_type_code,
        "dhis2_org_unit_id": facility.dhis2_org_unit_id,
        "latitude": facility.latitude,
        "longitude": facility.longitude,
        "status": facility.status,
        "created_at": facility.created_at.isoformat() if facility.created_at else None,
    }


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
        search = f"%{pagination.search}%"
        search_filter = (
            (Facility.name.ilike(search))
            | (Facility.code.ilike(search))
            | (Facility.health_district.ilike(search))
            | (Facility.dhis2_org_unit_id.ilike(search))
        )
        query = query.filter(search_filter)
    return paginate(query, pagination)


@router.post("")
def create_facility(
    payload: FacilityCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.manage")),
):
    data = _sync_country_geography(payload.model_dump())
    facility = Facility(**data)
    db.add(facility)
    db.commit()
    db.refresh(facility)
    # Capture response data BEFORE audit_log — audit_log does its own commit
    # which expires the facility object in the session.
    facility_data = _facility_to_dict(facility)

    audit_log(
        db=db,
        user=current_user,
        action="facility.create",
        resource_type="facility",
        resource_id=str(facility.id),
        request=request,
        status_code=201,
        payload={
            "name": facility.name,
            "code": facility.code,
            "category": facility.category,
            "country_code": facility.country_code,
            "dhis2_org_unit_id": facility.dhis2_org_unit_id,
        },
    )
    return {"data": facility_data, "message": "Établissement créé"}


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
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("facility.manage")),
):
    enforce_facility_access(current_user, facility_id)
    facility = db.query(Facility).filter(Facility.id == facility_id).first()
    if not facility:
        raise HTTPException(status_code=404, detail="Établissement non trouvé")

    update_data = payload.model_dump(exclude_unset=True)
    update_data = _sync_country_geography(update_data, facility)
    for key, value in update_data.items():
        setattr(facility, key, value)
    db.commit()
    db.refresh(facility)
    # Capture response data BEFORE audit_log
    facility_data = _facility_to_dict(facility)

    audit_log(
        db=db,
        user=current_user,
        action="facility.update",
        resource_type="facility",
        resource_id=str(facility.id),
        request=request,
        status_code=200,
        payload=update_data,
    )
    return {"data": facility_data, "message": "Établissement mis à jour"}
