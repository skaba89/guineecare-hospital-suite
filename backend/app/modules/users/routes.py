from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.security import hash_password
from app.core.tenant import enforce_facility_access
from app.db.session import get_db
from app.modules.rbac.dependencies import require_role
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def list_users(
    facility_id: str | None = None,
    role: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    query = db.query(User).order_by(User.created_at.desc())

    # Non-SUPER_ADMIN only see users from their facility
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(User.facility_id == current_user.facility_id)
    elif facility_id:
        query = query.filter(User.facility_id == facility_id)

    if role:
        query = query.filter(User.role == role)

    if pagination.search:
        query = query.filter(
            (User.first_name.ilike(f"%{pagination.search}%"))
            | (User.last_name.ilike(f"%{pagination.search}%"))
            | (User.email.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/bootstrap")
def bootstrap_first_user(payload: UserCreate, db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    if user_count > 0:
        raise HTTPException(status_code=403, detail="Bootstrap déjà effectué")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà existant")

    row = User(
        facility_id=payload.facility_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role="SUPER_ADMIN",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "Super administrateur créé"}


@router.post("")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email déjà existant")

    # Enforce tenant: non-SUPER_ADMIN can only create users in their facility
    facility_id = payload.facility_id
    if current_user.role != "SUPER_ADMIN":
        facility_id = current_user.facility_id
    else:
        enforce_facility_access(current_user, facility_id)

    # Non-SUPER_ADMIN cannot create SUPER_ADMIN users
    if payload.role == "SUPER_ADMIN" and current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Impossible de créer un super administrateur")

    row = User(
        facility_id=facility_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "Utilisateur créé"}


@router.get("/me")
def get_current_user_info(current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN", "DOCTOR", "NURSE", "PHARMACIST", "LAB_TECH", "CASHIER", "MIDWIFE"))):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "facility_id": current_user.facility_id,
        "is_active": current_user.is_active,
    }


@router.put("/{user_id}")
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    row = db.query(User).filter(User.id == user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

    # Enforce tenant access
    if current_user.role != "SUPER_ADMIN" and row.facility_id != current_user.facility_id:
        raise HTTPException(status_code=403, detail="Accès interdit")

    update_data = payload.model_dump(exclude_unset=True)

    # Cannot change role to SUPER_ADMIN unless you are SUPER_ADMIN
    if update_data.get("role") == "SUPER_ADMIN" and current_user.role != "SUPER_ADMIN":
        raise HTTPException(status_code=403, detail="Impossible de promouvoir au rang de super administrateur")

    for key, value in update_data.items():
        if key == "password" and value:
            row.password_hash = hash_password(value)
        else:
            setattr(row, key, value)

    db.commit()
    db.refresh(row)
    return {"data": row, "message": "Utilisateur mis à jour"}
