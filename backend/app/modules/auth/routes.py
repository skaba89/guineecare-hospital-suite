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

# Refresh rate-limit — 30/minute per IP. Even though refresh tokens are
# 32-byte random secrets (impractical to brute-force), rate-limiting prevents
# audit-log flooding and DoS via repeated 401 responses.
_REFRESH_LIMIT = (
    limiter.limit("30/minute")
    if settings.environment not in ("local", "test", "dev")
    else (lambda f: f)  # no-op decorator
)


# Account lockout configuration (A04-001)
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15


def _extract_request_meta(request: Request) -> tuple[str | None, str | None]:
    """Extract client IP and User-Agent from request.

    SECURITY (A05-001 — v0.9.0): only honors X-Forwarded-For when the
    direct peer is a configured TRUSTED_PROXY. Falls back to remote_addr
    otherwise — prevents IP spoofing when the backend is exposed directly.
    """
    from app.core.config import is_ip_trusted, settings

    remote_addr = request.client.host if request.client else None
    if is_ip_trusted(remote_addr, settings.trusted_proxies):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = remote_addr
    else:
        ip = remote_addr
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


def _is_locked(user: User) -> bool:
    """Check if the user account is currently locked due to failed logins."""
    if user.locked_until is None:
        return False
    now = utcnow()
    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        now = now.replace(tzinfo=None)
    return locked_until > now


def _register_failed_login(db: Session, user: User) -> None:
    """Increment failed_login_count; lock the account after MAX_FAILED_LOGIN_ATTEMPTS."""
    user.failed_login_count = (user.failed_login_count or 0) + 1
    if user.failed_login_count >= MAX_FAILED_LOGIN_ATTEMPTS:
        from datetime import timedelta
        user.locked_until = utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
    db.commit()


def _reset_failed_logins(db: Session, user: User) -> None:
    """Reset the failed-login counter after a successful login."""
    if user.failed_login_count or user.locked_until:
        user.failed_login_count = 0
        user.locked_until = None
        db.commit()


@router.post("/login", response_model=TokenResponse)
@_LOGIN_LIMIT
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # If user exists and is locked, refuse early
    if user and _is_locked(user):
        audit_log(
            db=db,
            user=user,
            action="auth.login_locked",
            resource_type="user",
            resource_id=str(user.id),
            request=request,
            status_code=423,
            payload={"email": payload.email},
        )
        raise HTTPException(
            status_code=423,
            detail=f"Compte verrouillé après {MAX_FAILED_LOGIN_ATTEMPTS} tentatives échouées. Réessayez dans {LOCKOUT_DURATION_MINUTES} minutes.",
        )

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
        # Increment failed login count if user exists
        if user:
            _register_failed_login(db, user)
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    if not user.is_active:
        audit_log(
            db=db,
            user=user,
            action="auth.login_inactive",
            resource_type="user",
            resource_id=str(user.id),
            request=request,
            status_code=403,
        )
        raise HTTPException(status_code=403, detail="Utilisateur inactif")

    # Successful login — reset failed-login counter
    _reset_failed_logins(db, user)

    # Check 2FA requirement
    from app.modules.auth.two_factor_service import is_2fa_enabled
    if is_2fa_enabled(db, user.id):
        # Don't issue tokens yet — require 2FA challenge
        audit_log(
            db=db, action="auth.login_2fa_required",
            user=user, resource_type="user", resource_id=str(user.id),
            request=request, status_code=200,
        )
        return {
            "requires_2fa": True,
            "user_id": str(user.id),
            "email": user.email,
            "message": "Code 2FA requis",
        }

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
@_REFRESH_LIMIT
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
        audit_log(
            db=db,
            action="auth.refresh_failed",
            resource_type="refresh_token",
            request=request,
            status_code=401,
            payload={"reason": "unknown_token"},
        )
        raise HTTPException(status_code=401, detail="Refresh token invalide ou révoqué")

    if record.revoked_at is not None:
        audit_log(
            db=db,
            action="auth.refresh_failed",
            resource_type="refresh_token",
            resource_id=str(record.id),
            request=request,
            status_code=401,
            payload={"reason": "revoked", "user_id": str(record.user_id)},
        )
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
        audit_log(
            db=db,
            action="auth.refresh_failed",
            resource_type="refresh_token",
            resource_id=str(record.id),
            request=request,
            status_code=401,
            payload={"reason": "expired", "user_id": str(record.user_id)},
        )
        raise HTTPException(status_code=401, detail="Refresh token expiré")

    # Load the user (refresh only works for active users)
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or not user.is_active:
        record.revoked_at = utcnow()
        db.commit()
        audit_log(
            db=db,
            action="auth.refresh_failed",
            resource_type="refresh_token",
            resource_id=str(record.id),
            request=request,
            status_code=401,
            payload={"reason": "user_inactive", "user_id": str(record.user_id)},
        )
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
    """Revoke a refresh token (explicit logout) and optionally the access token jti.

    SECURITY (A07 — v0.9.0): if `access_token` is provided in the request,
    its jti is added to the `revoked_jtis` blacklist. This means the
    access_token becomes immediately unusable — even if it was leaked.
    Without `access_token`, the access_token stays valid until its natural
    expiry (60 min) — only the refresh_token is revoked.
    """
    # Optionally revoke the access token's jti (immediate invalidation).
    if payload.access_token:
        try:
            from app.core.security import decode_access_token
            from app.modules.auth.jti import revoke_jti
            from jose import JWTError

            token_payload = decode_access_token(payload.access_token)
            token_jti = token_payload.get("jti")
            token_exp = token_payload.get("exp")
            from datetime import datetime, timezone
            expires_at = (
                datetime.fromtimestamp(token_exp, tz=timezone.utc)
                if token_exp
                else None
            )
            revoke_jti(
                db=db,
                jti=token_jti,
                user_id=str(current_user.id),
                reason="logout",
                expires_at=expires_at,
            )
        except JWTError:
            # Token might be expired or invalid — nothing to revoke.
            pass
        except Exception as e:
            # Audit-log the failure but don't fail the logout request.
            import logging
            logging.getLogger("guineecare.auth").warning(
                "Failed to revoke jti on logout: %s", e
            )

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
    from app.modules.auth.two_factor_service import is_2fa_enabled, get_remaining_backup_codes
    from app.db.session import get_db as _get_db
    db = next(_get_db())
    try:
        two_fa_enabled = is_2fa_enabled(db, current_user.id)
        backup_remaining = get_remaining_backup_codes(db, current_user.id) if two_fa_enabled else 0
    finally:
        db.close()
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "facility_id": current_user.facility_id,
        "is_active": current_user.is_active,
        "two_factor_enabled": two_fa_enabled,
        "backup_codes_remaining": backup_remaining,
    }


# ─── 2FA / MFA endpoints (v1.8.0) ──────────────────────────────────

@router.post("/2fa/setup")
def setup_2fa(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Démarre le setup 2FA : génère secret TOTP + QR URI + backup codes.

    L'utilisateur doit ensuite :
    1. Scanner le QR code avec Google Authenticator / Authy
    2. Appeler /auth/2fa/verify avec un code TOTP pour activer
    3. Sauvegarder les backup codes en lieu sûr
    """
    from app.modules.auth.two_factor_service import setup_2fa as _setup_2fa
    result = _setup_2fa(db, current_user.id)
    audit_log(
        db=db, user=current_user, action="auth.2fa.setup",
        resource_type="user", resource_id=current_user.id,
        request=request, status_code=200,
    )
    return result


@router.post("/2fa/verify")
def verify_2fa(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Active le 2FA après vérification du code TOTP saisi par l'utilisateur."""
    from app.modules.auth.two_factor_service import enable_2fa
    code = payload.get("code", "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Code TOTP requis")
    success, message = enable_2fa(db, current_user.id, code)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    audit_log(
        db=db, user=current_user, action="auth.2fa.enabled",
        resource_type="user", resource_id=current_user.id,
        request=request, status_code=200,
    )
    return {"message": message, "two_factor_enabled": True}


@router.post("/2fa/disable")
def disable_2fa(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Désactive le 2FA (le secret est conservé pour réactivation rapide)."""
    from app.modules.auth.two_factor_service import disable_2fa as _disable_2fa
    _disable_2fa(db, current_user.id)
    audit_log(
        db=db, user=current_user, action="auth.2fa.disabled",
        resource_type="user", resource_id=current_user.id,
        request=request, status_code=200,
    )
    return {"message": "2FA désactivé", "two_factor_enabled": False}


@router.post("/2fa/challenge")
def verify_2fa_challenge(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db),
):
    """Vérifie un code 2FA au login.

    Workflow :
    1. POST /auth/login → si 2FA activé, retourne {requires_2fa: true, user_id: ...}
    2. POST /auth/2fa/challenge {user_id, code} → retourne le token pair
    """
    from app.modules.auth.two_factor_service import verify_2fa_challenge as _verify
    user_id = payload.get("user_id", "")
    code = payload.get("code", "").strip()
    if not user_id or not code:
        raise HTTPException(status_code=400, detail="user_id et code requis")

    success, message = _verify(db, user_id, code)
    if not success:
        audit_log(
            db=db, action="auth.2fa.failed",
            resource_type="user", resource_id=user_id,
            request=request, status_code=401,
        )
        raise HTTPException(status_code=401, detail=message)

    # Issue token pair after successful 2FA
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    response = _issue_token_pair(db, user, request)
    audit_log(
        db=db, action="auth.2fa.success",
        user=user, resource_type="user", resource_id=user.id,
        request=request, status_code=200,
    )
    return response
