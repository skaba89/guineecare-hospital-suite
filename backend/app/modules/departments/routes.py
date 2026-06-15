from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User
from app.modules.departments.models import Department
from app.modules.departments.schemas import DepartmentCreate

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("")
def list_departments(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("department.read")),
):
    query = tenant_query(db, Department, current_user).order_by(Department.name)
    if pagination.search:
        query = query.filter(
            (Department.name.ilike(f"%{pagination.search}%"))
            | (Department.code.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("")
def create_department(
    payload: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("department.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = Department(**data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "department created"}
