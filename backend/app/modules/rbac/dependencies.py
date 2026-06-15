from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.models import RolePermission
from app.modules.users.models import User


def require_role(*allowed_roles: str):
    """Require that the current user has one of the specified roles.
    This is a global role check (not facility-scoped).
    """
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Rôle insuffisant. Requis : {', '.join(allowed_roles)}",
            )
        return current_user

    return checker


def require_permission(permission_code: str):
    """Require that the current user has the specified permission.
    SUPER_ADMIN and ADMIN bypass all permission checks.
    Other roles are checked against the role_permissions table.
    This check is facility-agnostic — use tenant_query() for data isolation.
    """
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
            raise HTTPException(
                status_code=403,
                detail=f"Permission manquante : {permission_code}",
            )
        return current_user

    return checker


def require_facility_admin():
    """Require that the current user is an ADMIN or SUPER_ADMIN.
    Used for management endpoints that require elevated privileges.
    """
    return require_role("SUPER_ADMIN", "ADMIN")
