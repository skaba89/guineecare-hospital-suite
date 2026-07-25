"""Modèles Insurance — v2.9.1
Assurance / tiers payeur pour la facturation hospitalière guinéenne.
Supporte les assureurs locaux (CNAM, NSIA, etc.) et internationaux.
"""
from app.core.datetime import utcnow
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String

from app.db.base import Base


class InsuranceProvider(Base):
    """Fournisseur d'assurance (CNAM, NSIA, ACTIVA, etc.)."""
    __tablename__ = "insurance_providers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=False, index=True)
    coverage_rate = Column(Float, default=0, nullable=False)  # % couvert (0-100)
    contact_phone = Column(String(50), nullable=True)
    contact_email = Column(String(255), nullable=True)
    address = Column(String(500), nullable=True)
    status = Column(String(30), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class PatientInsurance(Base):
    """Police d'assurance d'un patient auprès d'un fournisseur."""
    __tablename__ = "patient_insurances"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False, index=True)
    provider_id = Column(String(36), ForeignKey('insurance_providers.id'), nullable=False, index=True)
    policy_number = Column(String(100), nullable=False)
    beneficiary_name = Column(String(255), nullable=True)
    coverage_rate = Column(Float, nullable=True)  # override du taux provider si différent
    is_active = Column(Boolean, default=True, nullable=False)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
