from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.models import RolePermission
from app.modules.users.models import User


def require_role(*allowed_roles: str):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient role")
        return current_user

    return checker


def require_permission(permission_code: str):
    def checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ):
        if current_user.role in ["SUPER_ADMIN", "ADMIN"]:
            return current_user

        found = (
            db.query(RolePermission)
            .filter(RolePermission.role_code == current_user.role)
            .filter(RolePermission.permission_code == permission_code)
            .first()
        )
        if not found:
            raise HTTPException(status_code=403, detail="Missing permission")
        return current_user

    return checker
