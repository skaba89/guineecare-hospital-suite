from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, String

from app.db.base import Base


class TariffItem(Base):
    __tablename__ = "tariff_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    unit_price = Column(Float, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), nullable=False, index=True)
    patient_id = Column(String(36), nullable=False, index=True)
    admission_id = Column(String(36), nullable=True, index=True)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(String(255), nullable=True)
    net_amount = Column(Float, default=0, nullable=False)
    paid_amount = Column(Float, default=0, nullable=False)
    balance_due = Column(Float, default=0, nullable=False)
    status = Column(String(50), default="DRAFT", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), nullable=False, index=True)
    invoice_id = Column(String(36), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50), nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False)
    received_by = Column(String(36), nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
