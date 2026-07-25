from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String

from app.db.base import Base


class Room(Base):
    __tablename__ = "rooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    department_id = Column(String(36), ForeignKey('departments.id'), index=True, nullable=False)
    code = Column(String(50), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    room_type = Column(String(50), nullable=True)  # INDIVIDUAL, DOUBLE, COLLECTIVE, ICU
    status = Column(String(50), default="ACTIVE")  # ACTIVE, INACTIVE, MAINTENANCE
    created_at = Column(DateTime, default=utcnow, nullable=False)


class Bed(Base):
    __tablename__ = "beds"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    room_id = Column(String(36), ForeignKey('rooms.id'), index=True, nullable=False)
    bed_number = Column(String(50), nullable=False)
    bed_status = Column(String(50), default="AVAILABLE")  # AVAILABLE, OCCUPIED, RESERVED, OUT_OF_SERVICE
    created_at = Column(DateTime, default=utcnow, nullable=False)


class HospitalStay(Base):
    __tablename__ = "hospital_stays"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    admission_id = Column(String(36), ForeignKey('admissions.id'), index=True, nullable=True)
    bed_id = Column(String(36), ForeignKey('beds.id'), index=True, nullable=True)
    reason = Column(String(255), nullable=True)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, DISCHARGED, TRANSFERRED
    admitted_at = Column(DateTime, default=utcnow, nullable=False)
    discharged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
