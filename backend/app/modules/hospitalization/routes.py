from datetime import datetime
from app.core.datetime import utcnow

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.hospitalization.models import Bed, HospitalStay, Room
from app.modules.hospitalization.schemas import (
    BedBoardItem,
    BedCreate,
    HospitalStayCreate,
    RoomCreate,
)
from app.modules.patients.models import Patient
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/hospitalization", tags=["hospitalization"])


# ── Rooms ─────────────────────────────────────────────────────────────

@router.get("/rooms")
def list_rooms(
    facility_id: str | None = None,
    department_id: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hospitalization.read")),
):
    query = tenant_query(db, Room, current_user)
    if facility_id:
        query = query.filter(Room.facility_id == facility_id)
    if department_id:
        query = query.filter(Room.department_id == department_id)
    query = query.order_by(Room.code)
    return paginate(query, pagination)


@router.post("/rooms")
def create_room(
    payload: RoomCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hospitalization.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = Room(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="hospitalization.room_created",
        entity_type="room",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "room created"}


# ── Beds ──────────────────────────────────────────────────────────────

@router.get("/beds")
def list_beds(
    room_id: str | None = None,
    bed_status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hospitalization.read")),
):
    query = tenant_query(db, Bed, current_user)
    if room_id:
        query = query.filter(Bed.room_id == room_id)
    if bed_status:
        query = query.filter(Bed.bed_status == bed_status)
    query = query.order_by(Bed.bed_number)
    return paginate(query, pagination)


@router.post("/beds")
def create_bed(
    payload: BedCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hospitalization.manage")),
):
    room = db.query(Room).filter(Room.id == payload.room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    enforce_facility_access(current_user, room.facility_id)
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = Bed(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="hospitalization.bed_created",
        entity_type="bed",
        entity_id=row.id,
        level="NORMAL",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "bed created"}


# ── Bed Board ─────────────────────────────────────────────────────────

@router.get("/bed-board")
def get_bed_board(
    facility_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hospitalization.read")),
):
    enforce_facility_access(current_user, facility_id)
    beds = (
        tenant_query(db, Bed, current_user)
        .filter(Bed.facility_id == facility_id)
        .order_by(Bed.bed_number)
        .all()
    )

    items: list[dict] = []
    for bed in beds:
        room = db.query(Room).filter(Room.id == bed.room_id).first()
        patient_name = None
        stay_id = None
        if bed.bed_status == "OCCUPIED":
            stay = (
                db.query(HospitalStay)
                .filter(HospitalStay.bed_id == bed.id)
                .filter(HospitalStay.status == "ACTIVE")
                .first()
            )
            if stay:
                patient = db.query(Patient).filter(Patient.id == stay.patient_id).first()
                if patient:
                    patient_name = f"{patient.first_name} {patient.last_name}"
                stay_id = stay.id

        items.append(
            BedBoardItem(
                room_code=room.code if room else "",
                room_name=room.name if room else "",
                bed_id=bed.id,
                bed_number=bed.bed_number,
                bed_status=bed.bed_status,
                patient_name=patient_name,
                stay_id=stay_id,
            ).model_dump()
        )

    return {"data": items, "message": "bed board"}


# ── Hospital Stays ────────────────────────────────────────────────────

@router.post("/stays")
def admit_patient(
    payload: HospitalStayCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hospitalization.manage")),
):
    # If a bed is assigned, mark it as OCCUPIED
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))

    if payload.bed_id:
        bed = db.query(Bed).filter(Bed.id == payload.bed_id).first()
        if not bed:
            raise HTTPException(status_code=404, detail="Bed not found")
        enforce_facility_access(current_user, bed.facility_id)
        if bed.bed_status == "OCCUPIED":
            raise HTTPException(status_code=409, detail="Bed is already occupied")
        bed.bed_status = "OCCUPIED"

    row = HospitalStay(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="hospitalization.patient_admitted",
        entity_type="hospital_stay",
        entity_id=row.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "patient admitted"}


@router.get("/stays")
def list_stays(
    patient_id: str | None = None,
    status: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hospitalization.read")),
):
    query = tenant_query(db, HospitalStay, current_user)
    if patient_id:
        query = query.filter(HospitalStay.patient_id == patient_id)
    if status:
        query = query.filter(HospitalStay.status == status)
    query = query.order_by(HospitalStay.admitted_at.desc())
    return paginate(query, pagination)


@router.post("/stays/{stay_id}/discharge")
def discharge_patient(
    stay_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("hospitalization.manage")),
):
    stay = db.query(HospitalStay).filter(HospitalStay.id == stay_id).first()
    if not stay:
        raise HTTPException(status_code=404, detail="Hospital stay not found")
    enforce_facility_access(current_user, stay.facility_id)
    if stay.status == "DISCHARGED":
        raise HTTPException(status_code=409, detail="Patient already discharged")

    stay.status = "DISCHARGED"
    stay.discharged_at = utcnow()

    # If the stay has a bed, mark it as AVAILABLE
    if stay.bed_id:
        bed = db.query(Bed).filter(Bed.id == stay.bed_id).first()
        if bed:
            bed.bed_status = "AVAILABLE"

    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="hospitalization.patient_discharged",
        entity_type="hospital_stay",
        entity_id=stay.id,
        level="IMPORTANT",
    )
    db.commit()
    db.refresh(stay)
    return {"data": stay, "message": "patient discharged"}
