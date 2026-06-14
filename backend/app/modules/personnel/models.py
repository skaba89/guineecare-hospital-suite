from app.core.datetime import utcnow
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from datetime import datetime
from uuid import uuid4

from app.db.base import Base


class StaffMember(Base):
    __tablename__ = "staff_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), index=True, nullable=True)  # Link to auth user
    employee_number = Column(String(50), unique=True, index=True, nullable=False)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    profession = Column(String(100), nullable=True)  # MEDECIN, INFIRMIER, SAGE_FEMME, PHARMACIEN, LABORANTIN, ADMINISTRATIF
    specialty = Column(String(100), nullable=True)
    department_id = Column(String(36), ForeignKey('departments.id'), index=True, nullable=True)
    phone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)
    hire_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="ACTIVE")  # ACTIVE, ON_LEAVE, RESIGNED, RETIRED
    created_at = Column(DateTime, default=utcnow, nullable=False)


class OnCallSchedule(Base):
    __tablename__ = "on_call_schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    department_id = Column(String(36), ForeignKey('departments.id'), index=True, nullable=True)
    staff_id = Column(String(36), ForeignKey('staff_members.id'), index=True, nullable=False)
    on_call_date = Column(DateTime, nullable=False)
    shift_type = Column(String(50), nullable=False)  # DAY, NIGHT, FULL_DAY
    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
