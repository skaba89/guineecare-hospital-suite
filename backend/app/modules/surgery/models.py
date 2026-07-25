from app.core.datetime import utcnow
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.db.base import Base


class OperatingRoom(Base):
    """Salle d'opération"""
    __tablename__ = "operating_rooms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    code = Column(String(50), index=True, nullable=False)
    name = Column(String(255), nullable=False)
    room_type = Column(String(50), nullable=True)  # GENERAL, ORTHOPEDIC, CARDIAC, NEURO, PEDIATRIC
    status = Column(String(50), default="AVAILABLE")  # AVAILABLE, OCCUPIED, MAINTENANCE, CLEANING
    created_at = Column(DateTime, default=utcnow, nullable=False)


class SurgerySchedule(Base):
    """Programmation opératoire"""
    __tablename__ = "surgery_schedules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    operating_room_id = Column(String(36), ForeignKey('operating_rooms.id'), index=True, nullable=True)
    surgeon_id = Column(String(36), ForeignKey('users.id'), index=True, nullable=True)
    anesthesiologist_id = Column(String(36), ForeignKey('users.id'), index=True, nullable=True)
    procedure_name = Column(String(255), nullable=False)
    procedure_code = Column(String(50), nullable=True)  # code CCAM / acte
    laterality = Column(String(20), nullable=True)  # LEFT, RIGHT, BILATERAL, NOT_APPLICABLE
    urgency = Column(String(50), default="PLANNED")  # PLANNED, URGENT, EMERGENCY
    status = Column(String(50), default="SCHEDULED")  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED, POSTPONED
    scheduled_date = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)


class SurgeryTeamMember(Base):
    """Membre de l'équipe opératoire"""
    __tablename__ = "surgery_team_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    schedule_id = Column(String(36), ForeignKey('surgery_schedules.id'), index=True, nullable=False)
    user_id = Column(String(36), ForeignKey('users.id'), index=True, nullable=True)
    role = Column(String(100), nullable=False)  # SURGEON, ANESTHESIOLOGIST, NURSE_INSTRUMENTIST, NURSE_ANESTHETIST, AIDE_OPERATOR, CIRCULATING_NURSE
    created_at = Column(DateTime, default=utcnow, nullable=False)


class SurgeryReport(Base):
    """Compte rendu opératoire"""
    __tablename__ = "surgery_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), index=True, nullable=False)
    schedule_id = Column(String(36), ForeignKey('surgery_schedules.id'), index=True, nullable=False)
    patient_id = Column(String(36), ForeignKey('patients.id'), index=True, nullable=False)
    surgeon_id = Column(String(36), ForeignKey('users.id'), index=True, nullable=True)
    operative_findings = Column(Text, nullable=True)  # constatations per-opératoires
    procedure_performed = Column(Text, nullable=True)  # geste réalisé
    complications = Column(Text, nullable=True)
    specimens = Column(Text, nullable=True)  # pièces opératoires
    blood_loss = Column(String(100), nullable=True)
    anesthesia_type = Column(String(100), nullable=True)  # GENERAL, REGIONAL, LOCAL
    status = Column(String(50), default="DRAFT")  # DRAFT, VALIDATED
    created_at = Column(DateTime, default=utcnow, nullable=False)
    validated_at = Column(DateTime, nullable=True)
