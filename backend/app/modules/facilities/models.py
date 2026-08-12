from app.core.datetime import utcnow
from app.core.config import settings
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, String

from app.db.base import Base


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    category = Column(String(100), nullable=True)

    # ------------------------------------------------------------------
    # Guinea-first + multi-country geography
    # ------------------------------------------------------------------
    # Existing Guinea-specific columns are kept for backwards compatibility
    # with reporting, seeds and current frontend forms.
    region = Column(String(150), nullable=True, index=True)
    prefecture = Column(String(150), nullable=True, index=True)
    # v2.5.0 — Phase 5 : commune pour pilotage national granulaire
    # Hiérarchie administrative Guinée : Région > Préfecture > Commune > Quartier
    commune = Column(String(150), nullable=True, index=True)

    # Generic country-aware representation. For Guinea, routes keep these in
    # sync with region/prefecture/commune. Other countries can use their own
    # labels without schema changes.
    country_code = Column(String(2), nullable=False, default=lambda: settings.country_code, index=True)
    admin_level_1 = Column(String(150), nullable=True, index=True)
    admin_level_2 = Column(String(150), nullable=True, index=True)
    admin_level_3 = Column(String(150), nullable=True, index=True)
    admin_level_4 = Column(String(150), nullable=True, index=True)

    # Health-system hierarchy and national interoperability identifiers.
    health_district = Column(String(150), nullable=True, index=True)
    facility_type_code = Column(String(50), nullable=True, index=True)
    dhis2_org_unit_id = Column(String(128), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
