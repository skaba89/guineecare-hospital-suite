from pydantic import BaseModel, Field

from app.core.config import settings


class FacilityCreate(BaseModel):
    code: str
    name: str
    category: str | None = None

    # Guinea legacy geography — retained for backwards compatibility.
    region: str | None = None
    prefecture: str | None = None
    commune: str | None = None

    # Multi-country geography.
    country_code: str = Field(default_factory=lambda: settings.country_code)
    admin_level_1: str | None = None
    admin_level_2: str | None = None
    admin_level_3: str | None = None
    admin_level_4: str | None = None
    health_district: str | None = None

    # National interoperability / master facility registry fields.
    facility_type_code: str | None = None
    dhis2_org_unit_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class FacilityUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    region: str | None = None
    prefecture: str | None = None
    commune: str | None = None
    country_code: str | None = None
    admin_level_1: str | None = None
    admin_level_2: str | None = None
    admin_level_3: str | None = None
    admin_level_4: str | None = None
    health_district: str | None = None
    facility_type_code: str | None = None
    dhis2_org_unit_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str | None = None


class FacilityRead(BaseModel):
    id: str
    code: str
    name: str
    category: str | None = None
    region: str | None = None
    prefecture: str | None = None
    commune: str | None = None
    country_code: str
    admin_level_1: str | None = None
    admin_level_2: str | None = None
    admin_level_3: str | None = None
    admin_level_4: str | None = None
    health_district: str | None = None
    facility_type_code: str | None = None
    dhis2_org_unit_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    status: str

    class Config:
        from_attributes = True
