from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
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
        # token_iat est en secondes unix ; last_disabled_at est un datetime.
        # Si le token a été émis AVANT la dernière désactivation → refuser.
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
            # iat malformé — refuser par sécurité
            raise HTTPException(status_code=401, detail="Jeton d'authentification invalide")

    # Attach JWT claims to the user object for downstream use
    user._token_facility_id = token_facility_id
    user._token_role = token_role
    user._token_jti = token_jti

    return user
