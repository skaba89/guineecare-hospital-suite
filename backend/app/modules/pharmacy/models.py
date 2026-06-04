from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, String

from app.db.base import Base


class PharmacyProduct(Base):
    __tablename__ = "pharmacy_products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    form = Column(String(100), nullable=True)
    dosage = Column(String(100), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PharmacyStock(Base):
    __tablename__ = "pharmacy_stock"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), nullable=False, index=True)
    product_id = Column(String(36), nullable=False, index=True)
    quantity_available = Column(Float, default=0, nullable=False)
    min_threshold = Column(Float, default=0, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), nullable=False, index=True)
    product_id = Column(String(36), nullable=False, index=True)
    movement_type = Column(String(50), nullable=False)
    quantity = Column(Float, nullable=False)
    reason = Column(String(255), nullable=True)
    performed_by = Column(String(36), nullable=True)
    performed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
