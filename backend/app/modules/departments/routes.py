from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.audit.service import audit_log
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
    request: Request,
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
    # Capture response data BEFORE audit_log (audit_log does its own commit
    # which expires the row object).
    row_data = {
        "id": str(row.id),
        "code": getattr(row, "code", None),
        "name": row.name,
        "facility_id": str(row.facility_id) if row.facility_id else None,
    }

    audit_log(
        db=db,
        user=current_user,
        action="department.create",
        resource_type="department",
        resource_id=str(row.id),
        request=request,
        status_code=201,
        payload={"name": row.name, "code": getattr(row, "code", None), "facility_id": str(row.facility_id) if row.facility_id else None},
    )
    return {"data": row_data, "message": "department created"}
