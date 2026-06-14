from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.db.session import get_db
from app.modules.rbac.dependencies import require_role
from app.modules.rbac.models import Permission, Role, RolePermission
from app.modules.rbac.schemas import PermissionCreate, RoleCreate, RolePermissionCreate
from app.modules.users.models import User

router = APIRouter(prefix="/rbac", tags=["rbac"])


@router.get("/roles")
def list_roles(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    query = db.query(Role).order_by(Role.code)
    if pagination.search:
        query = query.filter(
            (Role.name.ilike(f"%{pagination.search}%"))
            | (Role.code.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/roles")
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    existing = db.query(Role).filter(Role.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role already exists")
    row = Role(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "role created"}


@router.get("/permissions")
def list_permissions(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    query = db.query(Permission).order_by(Permission.module, Permission.code)
    if pagination.search:
        query = query.filter(
            (Permission.name.ilike(f"%{pagination.search}%"))
            | (Permission.code.ilike(f"%{pagination.search}%"))
            | (Permission.module.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/permissions")
def create_permission(
    payload: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("SUPER_ADMIN", "ADMIN")),
):
    existing = db.query(Permission).filter(Permission.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Permission already exists")
    row = Permission(**payload.model_dump())
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
    row = RolePermission(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "permission assigned"}
