from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import create_access_token, verify_password
from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import LoginRequest
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


# En dev/test, on désactive le rate-limit pour permettre les tests E2E et Playwright.
# En production, le rate-limit reste actif (5/minute par IP).
_LOGIN_LIMIT = (
    limiter.limit("5/minute")
    if settings.environment not in ("local", "test", "dev")
    else (lambda f: f)  # no-op decorator
)


@router.post("/login")
@_LOGIN_LIMIT
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Utilisateur inactif")

    token = create_access_token(
        subject=user.id,
        facility_id=user.facility_id,
        role=user.role,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role,
            "facility_id": user.facility_id,
            "is_active": user.is_active,
        },
    }


@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "facility_id": current_user.facility_id,
        "is_active": current_user.is_active,
    }
