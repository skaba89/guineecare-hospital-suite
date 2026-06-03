from pydantic import BaseModel


class DepartmentCreate(BaseModel):
    facility_id: str
    code: str
    name: str
    category: str | None = None


class DepartmentRead(BaseModel):
    id: str
    facility_id: str
    code: str
    name: str
    category: str | None = None
    status: str

    class Config:
        from_attributes = True
