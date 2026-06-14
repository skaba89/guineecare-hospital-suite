from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    facility_id: str | None = None
    role: str = "USER"


class UserRead(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    facility_id: str | None = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
