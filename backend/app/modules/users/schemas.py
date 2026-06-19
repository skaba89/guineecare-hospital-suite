from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    facility_id: str | None = None
    role: str = "USER"


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    facility_id: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserRead(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    facility_id: str | None = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
