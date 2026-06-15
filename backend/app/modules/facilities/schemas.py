from pydantic import BaseModel


class FacilityCreate(BaseModel):
    code: str
    name: str
    category: str | None = None
    region: str | None = None
    prefecture: str | None = None


class FacilityUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    region: str | None = None
    prefecture: str | None = None
    status: str | None = None


class FacilityRead(BaseModel):
    id: str
    code: str
    name: str
    category: str | None = None
    region: str | None = None
    prefecture: str | None = None
    status: str

    class Config:
        from_attributes = True
