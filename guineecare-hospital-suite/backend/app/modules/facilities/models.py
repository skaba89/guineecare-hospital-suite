from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String

from app.db.base import Base


class Facility(Base):
    __tablename__ = "facilities"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), index=True, nullable=False)
    category = Column(String(100), nullable=True)
    region = Column(String(150), nullable=True, index=True)
    prefecture = Column(String(150), nullable=True, index=True)
    # v2.5.0 — Phase 5 : commune pour pilotage national granulaire
    # Hiérarchie administrative Guinée : Région > Préfecture > Commune > Quartier
    commune = Column(String(150), nullable=True, index=True)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
