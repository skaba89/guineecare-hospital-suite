from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.datetime import utcnow
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token_expiry,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.modules.audit.service import audit_log
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import RefreshToken
from app.modules.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
    UserInfo,
)
from app.modules.users.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


# En dev/test, on désactive le rate-limit pour permettre les tests E2E et Playwright.
# En production, le rate-limit reste actif (5/minute par IP).
_LOGIN_LIMIT = (
    limiter.limit("5/minute")
    if settings.environment not in ("local", "test", "dev")
    else (lambda f: f)  # no-op decorator
)


def _extract_request_meta(request: Request) -> tuple[str | None, str | None]:
    """Extract client IP and User-Agent from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    if ua and len(ua) > 512:
        ua = ua[:512]
    return ip, ua


def _issue_token_pair(db: Session, user: User, request: Request) -> TokenResponse:
    """Issue a new access token + refresh token pair and persist the refresh token.

    Also includes the user object in the response for backward compatibility
    with existing clients that read `response.user` after login.
    """
    access_token = create_access_token(
        subject=user.id,
        facility_id=user.facility_id,
        role=user.role,
    )

    raw_refresh = generate_refresh_token()
    ip, ua = _extract_request_meta(request)
    refresh_record = RefreshToken(
        user_id=user.id,
        facility_id=user.facility_id,
        token_hash=hash_refresh_token(raw_refresh),
        expires_at=create_refresh_token_expiry(),
        created_ip=ip,
        created_user_agent=ua,
    )
    db.add(refresh_record)
    db.commit()
    db.refresh(refresh_record)

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        token_type="bearer",
        expires_in=settings.token_expire_minutes * 60,
        user=UserInfo(
            id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            facility_id=user.facility_id,
            is_active=user.is_active,
        ),
    )


@router.post("/login", response_model=TokenResponse)
@_LOGIN_LIMIT
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        # Audit failed login attempt (user may be None — log email as resource_id)
        audit_log(
            db=db,
            action="auth.login_failed",
            resource_type="user",
            resource_id=str(user.id) if user else None,
            request=request,
            status_code=401,
            payload={"email": payload.email},
        )
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    if not user.is_active:
        audit_log(
            db=db,
            action="auth.login_inactive",
            user=user,
            resource_type="user",
            resource_id=str(user.id),
            request=request,
            status_code=403,
        )
        raise HTTPException(status_code=403, detail="Utilisateur inactif")

    response = _issue_token_pair(db, user, request)
    audit_log(
        db=db,
        action="auth.login",
        user=user,
        resource_type="user",
        resource_id=str(user.id),
        request=request,
        status_code=200,
    )
    return response


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh token pair.

    Implements refresh token rotation: the presented refresh token is revoked
    and replaced by a new one. This limits the impact of a leaked refresh token.
    """
    if not payload.refresh_token:
        raise HTTPException(status_code=400, detail="refresh_token manquant")

    token_hash = hash_refresh_token(payload.refresh_token)
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )

    # Possible token reuse or unknown token
    if not record:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou révoqué")

    if record.revoked_at is not None:
        raise HTTPException(status_code=401, detail="Refresh token invalide ou révoqué")

    # Handle both tz-aware (PostgreSQL) and tz-naive (SQLite) datetimes
    now = utcnow()
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        # SQLite returns naive datetime — strip tz from now for comparison
        now = now.replace(tzinfo=None)

    if expires_at <= now:
        record.revoked_at = utcnow()
        db.commit()
        raise HTTPException(status_code=401, detail="Refresh token expiré")

    # Load the user (refresh only works for active users)
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or not user.is_active:
        record.revoked_at = utcnow()
        db.commit()
        raise HTTPException(status_code=401, detail="Utilisateur inactif ou inconnu")

    # Rotate: revoke the current refresh token
    record.last_used_at = utcnow()
    record.revoked_at = utcnow()
    db.commit()

    # Issue a new pair
    return _issue_token_pair(db, user, request)


@router.post("/logout", response_model=MessageResponse)
def logout(
    payload: LogoutRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke a refresh token (explicit logout).

    The access token remains valid until expiry (short-lived, 60 min).
    For immediate revocation of access tokens, see roadmap: token blacklist (v0.7).
    """
    if not payload.refresh_token:
        audit_log(
            db=db,
            action="auth.logout",
            user=current_user,
            resource_type="user",
            resource_id=str(current_user.id),
            request=request,
            status_code=200,
        )
        return MessageResponse(message="Déconnexion réussie (aucun refresh token fourni)")

    token_hash = hash_refresh_token(payload.refresh_token)
    record = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .first()
    )
    if record and record.revoked_at is None:
        record.revoked_at = utcnow()
        db.commit()

    audit_log(
        db=db,
        action="auth.logout",
        user=current_user,
        resource_type="user",
        resource_id=str(current_user.id),
        request=request,
        status_code=200,
    )

    return MessageResponse(message="Déconnexion réussie")


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
