from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.rbac.dependencies import require_role
from app.modules.rbac.models import Permission, Role, RolePermission
from app.modules.rbac.schemas import PermissionCreate, RoleCreate, RolePermissionCreate
from app.modules.users.models import User

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.get("/roles")
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    rows = db.query(Role).order_by(Role.code).all()
    return {"data": rows, "message": "roles list"}


@router.post("/roles")
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    existing = db.query(Role).filter(Role.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")
    row = Role(**payload.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "role created"}


@router.get("/permissions")
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    rows = db.query(Permission).order_by(Permission.module, Permission.code).all()
    return {"data": rows, "message": "permissions list"}


@router.post("/permissions")
def create_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    existing = db.query(Permission).filter(Permission.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Permission already exists")
    row = Permission(**payload.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "permission created"}


@router.post("/role-permissions")
def assign_permission_to_role(
    payload: RolePermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    existing = (
        db.query(RolePermission)
        .filter(RolePermission.role_code == payload.role_code)
        .filter(RolePermission.permission_code == payload.permission_code)
        .first()
    )
    if existing:
        return {"data": existing, "message": "permission already assigned"}
    row = RolePermission(**payload.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "permission assigned"}
