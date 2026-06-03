from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    facility_id: str | None = None
    role: str = "USER"


class UserRead(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    facility_id: str | None = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
