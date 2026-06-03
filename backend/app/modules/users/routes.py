from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.dependencies import require_role
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("")
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    rows = db.query(User).order_by(User.created_at.desc()).all()
    return {"data": rows, "message": "users list"}


@router.post("")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user_count = db.query(User).count()
    if user_count > 0:
        current_user = next(get_current_user(db=db)) if False else None
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    row = User(
        facility_id=payload.facility_id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "user created"}
