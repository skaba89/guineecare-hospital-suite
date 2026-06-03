from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.modules.rbac.dependencies import require_role
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate

router = APIRouter(prefix="/users", tags=["users"])

BOOTSTRAP_HEADER = "X-GuineeCare-Bootstrap"
BOOTSTRAP_VALUE = "init-first-admin"


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    rows = db.query(User).order_by(User.created_at.desc()).all()
    return {"data": rows, "message": "users list"}


@router.post("")
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    bootstrap_token: str | None = Header(default=None, alias=BOOTSTRAP_HEADER),
):
    user_count = db.query(User).count()
    if user_count > 0 and bootstrap_token != BOOTSTRAP_VALUE:
        raise HTTPException(status_code=403, detail="User creation requires admin flow")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    role = payload.role
    if user_count == 0:
        role = "SUPER_ADMIN"

    row = User(
        facility_id=payload.facility_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=role,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "user created"}
