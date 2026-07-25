from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String

from app.db.base import Base


class LabTest(Base):
    __tablename__ = "lab_tests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=True)
    sample_type = Column(String(100), nullable=True)
    status = Column(String(50), default="ACTIVE", nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), nullable=False, index=True)
    patient_id = Column(String(36), ForeignKey('patients.id'), nullable=False, index=True)
    admission_id = Column(String(36), ForeignKey('admissions.id'), nullable=True, index=True)
    # test_id reste pour rétro-compat (commandes à un seul test existantes)
    test_id = Column(String(36), ForeignKey('lab_tests.id'), nullable=True, index=True)
    priority = Column(String(50), default="NORMAL", nullable=False)
    status = Column(String(50), default="ORDERED", nullable=False)
    ordered_by = Column(String(36), nullable=True)
    ordered_at = Column(DateTime, default=utcnow, nullable=False)
    # v2.8.3 — P2-2 : colonne dédiée pour le prélèvement (au lieu du hack ordered_by)
    sample_id = Column(String(100), nullable=True)
    collected_by = Column(String(36), nullable=True)
    collected_at = Column(DateTime, nullable=True)


# v2.6.0 — Phase 7 : Panel labo (1 commande = N tests)
# Table de jointure pour permettre à une commande labo de contenir
# plusieurs tests (ex: NFS + CRP + Glycémie en une seule demande).
class LabOrderTest(Base):
    __tablename__ = "lab_order_tests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id = Column(String(36), ForeignKey('lab_orders.id'), nullable=False, index=True)
    test_id = Column(String(36), ForeignKey('lab_tests.id'), nullable=False, index=True)
    # Statut individuel par test dans le panel (permet validation séparée)
    status = Column(String(50), default="ORDERED", nullable=False)
    # Résultat peut être saisi ici directement (alternative à LabResult séparé)
    result_value = Column(String(255), nullable=True)
    interpretation = Column(String(255), nullable=True)
    validated_by = Column(String(36), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class LabResult(Base):
    __tablename__ = "lab_results"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), nullable=False, index=True)
    order_id = Column(String(36), ForeignKey('lab_orders.id'), nullable=False, index=True)
    result_value = Column(String(255), nullable=False)
    interpretation = Column(String(255), nullable=True)
    status = Column(String(50), default="DRAFT", nullable=False)
    entered_by = Column(String(36), nullable=True)
    validated_by = Column(String(36), nullable=True)
    entered_at = Column(DateTime, default=utcnow, nullable=False)
    validated_at = Column(DateTime, nullable=True)
