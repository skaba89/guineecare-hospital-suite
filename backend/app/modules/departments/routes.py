from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.departments.models import Department
from app.modules.departments.schemas import DepartmentCreate

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("")
def list_departments(db: Session = Depends(get_db)):
    rows = db.query(Department).order_by(Department.name).all()
    return {"data": rows, "message": "departments list"}


@router.post("")
def create_department(payload: DepartmentCreate, db: Session = Depends(get_db)):
    row = Department(**payload.dict())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "department created"}
