from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.pagination import PaginationParams, paginate
from app.core.security import hash_password
from app.core.tenant import enforce_facility_access
from app.db.session import get_db
from app.modules.audit.service import audit_log
from app.modules.rbac.dependencies import require_role
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _safe_user_dict(row: User) -> dict:
    """Return a User dict safe for API response (never exposes password_hash)."""
    return row.to_read_dict()


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
    # Use paginate but transform each row to safe dict
    result = paginate(query, pagination)
    # Replace password-hash-containing rows with safe dicts
    if isinstance(result, dict) and "data" in result:
        result["data"] = [_safe_user_dict(r) for r in result["data"]]
    return result


@router.post("/bootstrap")
def bootstrap_first_user(
    payload: UserCreate,
    request: Request,
    x_bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"),
    db: Session = Depends(get_db),
):
    """Create the first SUPER_ADMIN. Only works when the users table is empty.

    SECURITY (A05-004 — v0.9.0): in non-local environments, this endpoint
    requires an `X-Bootstrap-Token` header matching the `BOOTSTRAP_TOKEN`
    env var. If `BOOTSTRAP_TOKEN` is unset in non-local, the endpoint is
    disabled entirely — operators MUST use `python -m app.cli create-superuser`
    instead. In local env, the endpoint is open (chicken-and-egg convenience).

    In all environments, the endpoint refuses to run if the users table is
    non-empty.
    """
    import hmac

    # Token gate (skipped in local for dev convenience).
    if settings.environment != "local":
        if not settings.bootstrap_token:
            raise HTTPException(
                status_code=403,
                detail="Bootstrap endpoint disabled. Use `python -m app.cli create-superuser` instead.",
            )
        if not x_bootstrap_token or not hmac.compare_digest(
            x_bootstrap_token, settings.bootstrap_token
        ):
            raise HTTPException(status_code=403, detail="Bootstrap token invalide ou manquant")

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

    # Audit log (no current_user since this is unauthenticated bootstrap)
    audit_log(
        db=db,
        user=None,
        action="user.bootstrap",
        resource_type="user",
        resource_id=str(row.id),
        request=request,
        status_code=201,
        payload={"email": row.email, "role": row.role},
    )

    return {"data": _safe_user_dict(row), "message": "Super administrateur créé"}


@router.post("")
def create_user(
    payload: UserCreate,
    request: Request,
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

    audit_log(
        db=db,
        user=current_user,
        action="user.create",
        resource_type="user",
        resource_id=str(row.id),
        request=request,
        status_code=201,
        payload={"email": row.email, "role": row.role, "facility_id": row.facility_id},
    )

    return {"data": _safe_user_dict(row), "message": "Utilisateur créé"}


@router.get("/me")
def get_current_user_info(current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN", "DOCTOR", "NURSE", "PHARMACIST", "LAB_TECH", "CASHIER", "MIDWIFE"))):
    return _safe_user_dict(current_user)


@router.put("/{user_id}")
def update_user(
    user_id: str,
    payload: UserUpdate,
    request: Request,
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

    # Build a redacted audit payload (never log the raw password)
    audit_payload: dict = {}
    for key, value in update_data.items():
        if key == "password" and value:
            row.password_hash = hash_password(value)
            audit_payload["password"] = "[REDACTED]"
        else:
            setattr(row, key, value)
            audit_payload[key] = value

    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        user=current_user,
        action="user.update",
        resource_type="user",
        resource_id=str(row.id),
        request=request,
        status_code=200,
        payload=audit_payload,
    )

    return {"data": _safe_user_dict(row), "message": "Utilisateur mis à jour"}
