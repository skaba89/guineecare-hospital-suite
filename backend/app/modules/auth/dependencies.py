from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.tenant import bind_tenant_context
from app.db.session import get_db
from app.modules.auth.jti import is_jti_revoked
from app.modules.users.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Jeton d'authentification manquant")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.auth_secret,
            algorithms=[settings.auth_algorithm],
        )
        user_id = payload.get("sub")
        token_facility_id = payload.get("facility_id")
        token_role = payload.get("role")
        token_jti = payload.get("jti")
        token_iat = payload.get("iat")  # issued-at (unix timestamp)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Jeton d'authentification invalide")

    if not user_id:
        raise HTTPException(status_code=401, detail="Jeton d'authentification invalide")

    # SECURITY (A07 — v0.9.0): check jti blacklist. If the token was
    # explicitly revoked (logout, admin disable, suspected theft), refuse.
    if is_jti_revoked(db, token_jti):
        raise HTTPException(status_code=401, detail="Jeton révoqué")

    # Identity/control-plane tables are intentionally outside the first RLS
    # policy set so authentication can resolve the user before tenant context
    # exists. Once this trusted DB row is loaded, all protected business data
    # is scoped using the CURRENT database values below, not request input.
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur inactif ou inconnu")

    # SECURITY (v2.2.0 — Phase 6) : session invalidation forte.
    # Si l'utilisateur a été désactivé puis réactivé, tous les tokens émis
    # avant `last_disabled_at` doivent être refusés. Cela complète la
    # protection is_active (qui ne bloque que pendant la désactivation)
    # en invalidant rétroactivement les tokens déjà émis.
    last_disabled_at = getattr(user, "last_disabled_at", None)
    if last_disabled_at is not None and token_iat is not None:
        from datetime import datetime, timezone
        try:
            iat_dt = datetime.fromtimestamp(int(token_iat), tz=timezone.utc)
            disabled_dt = last_disabled_at
            if disabled_dt.tzinfo is None:
                disabled_dt = disabled_dt.replace(tzinfo=timezone.utc)
            if iat_dt < disabled_dt:
                raise HTTPException(
                    status_code=401,
                    detail="Session expirée — veuillez vous reconnecter",
                )
        except (ValueError, TypeError):
            raise HTTPException(status_code=401, detail="Jeton d'authentification invalide")

    # Bind the authoritative facility/role from the database to PostgreSQL RLS.
    # A stale JWT claim therefore cannot move a user to another tenant.
    bind_tenant_context(db, user)

    # Attach JWT claims to the user object for downstream compatibility. These
    # claims are informational; RLS authorization uses the database row above.
    user._token_facility_id = token_facility_id
    user._token_role = token_role
    user._token_jti = token_jti

    return user
