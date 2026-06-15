from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
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
    except JWTError:
        raise HTTPException(status_code=401, detail="Jeton d'authentification invalide")

    if not user_id:
        raise HTTPException(status_code=401, detail="Jeton d'authentification invalide")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur inactif ou inconnu")

    # Attach JWT claims to the user object for downstream use
    user._token_facility_id = token_facility_id
    user._token_role = token_role

    return user
