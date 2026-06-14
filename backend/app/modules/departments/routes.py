from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
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
    query = db.query(Department).order_by(Department.name)
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
    row = Department(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "department created"}
