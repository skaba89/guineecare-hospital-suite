from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db.base import Base


class NationalReport(Base):
    """Rapport national soumis au Ministère de la Santé"""
    __tablename__ = "national_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    report_type = Column(String(100), nullable=False)  # MONTHLY, QUARTERLY, ANNUAL, EPIDEMIC_ALERT
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_admissions = Column(String(20), nullable=True)
    total_discharges = Column(String(20), nullable=True)
    total_deaths = Column(String(20), nullable=True)
    total_births = Column(String(20), nullable=True)
    total_surgeries = Column(String(20), nullable=True)
    total_emergency_visits = Column(String(20), nullable=True)
    bed_occupancy_rate = Column(String(20), nullable=True)
    average_stay_days = Column(String(20), nullable=True)
    disease_distribution = Column(Text, nullable=True)  # JSON string: top diagnoses
    status = Column(String(50), default="DRAFT")  # DRAFT, SUBMITTED, VALIDATED, REJECTED
    submitted_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    validated_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class EpidemicAlert(Base):
    """Alerte épidémique"""
    __tablename__ = "epidemic_alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    disease_name = Column(String(255), nullable=False)
    case_count = Column(String(20), nullable=False)
    threshold_exceeded = Column(String(10), default="YES")  # YES/NO
    alert_level = Column(String(50), default="WARNING")  # WATCH, WARNING, ALERT, EMERGENCY
    region = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    measures_taken = Column(Text, nullable=True)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, UNDER_CONTROL, CLOSED
    reported_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)


class HealthStatistic(Base):
    """Statistique sanitaire agrégée (SNIS)"""
    __tablename__ = "health_statistics"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    category = Column(String(100), nullable=False)  # CONSULTATION, HOSPITALIZATION, MATERNITY, SURGERY, EMERGENCY, PHARMACY
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(String(100), nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    unit = Column(String(50), nullable=True)  # count, rate, percentage
    source = Column(String(100), nullable=True)  # SNIS, DHIS2, MANUAL
    created_at = Column(DateTime, default=utcnow, nullable=False)
