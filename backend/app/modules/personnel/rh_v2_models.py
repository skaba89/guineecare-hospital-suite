"""Modèles RH v2 v1.5.0 — plannings, gardes, congés, astreintes, remplacements.

Le module RH v1 (StaffMember, OnCallSchedule, LeaveRequest, Contract) couvre
les effectifs et les congés basiques. Le RH v2 ajoute la planification
opérationnelle :

- `Shift` : créneau de travail récurrent (ex: "Garde médecine nuit", "Consultation matin").
  Sert de template pour générer les affectations.
- `ShiftAssignment` : affectation concrète d'un staff à un shift à une date
  précise. C'est l'unité atomique du planning.
- `LeaveBalance` : solde de congés par staff et par année (cumul, pris, restant).
- `OnCallDuty` : astreinte (téléphonique ou physique), distincte du shift
  classique car sans présence continue mais engagement de joignabilité.
- `ShiftSwap` : demande de remplacement entre deux staffs (workflow : REQUESTED
  → ACCEPTED → APPROVED → COMPLETED | REJECTED).

Conventions :
- Multi-tenant via `facility_id`.
- Audit trail via `record_activity()` dans les routes.
- Notifications : à la création d'un ShiftAssignment, le staff reçoit une
  notification in-app (catégorie `shift_assignment`). À la demande de swap,
  le remplaçant potentiel reçoit une notification `shift_swap_request`.
"""
from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from app.core.datetime import utcnow
from app.db.base import Base


def _uuid() -> str:
    return str(uuid4())


class Shift(Base):
    """Template de créneau de travail récurrent.

    Exemples :
    - "Garde médecine nuit" — service Médecine interne, 20h00 → 08h00
    - "Consultation externe matin" — service Cardiologie, 08h00 → 13h00
    - "Tour de garde urgences week-end" — service Urgences, 12h (FULL_DAY)

    Les Shifts sont utilisés pour générer massivement des ShiftAssignments
    via `POST /personnel/shifts/{id}/generate?start=...&end=...`.
    """
    __tablename__ = "shifts"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Périmètre
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)

    # Identification
    code = Column(String(64), nullable=False, index=True)  # e.g. GARDE_MED_NUIT
    name = Column(String(200), nullable=False)
    shift_type = Column(String(32), nullable=False)  # DAY | NIGHT | FULL_DAY | ON_CALL
    color = Column(String(16), nullable=True)  # hex code pour l'affichage UI (#0ea5e9)

    # Horaires (récurrents — la date est portée par ShiftAssignment)
    start_time = Column(Time, nullable=True)  # null pour FULL_DAY/ON_CALL
    end_time = Column(Time, nullable=True)
    duration_hours = Column(Integer, nullable=True)  # denormalized pour stats

    # Récurrence (cron-like simplifié)
    # WEEKDAYS = lundi-vendredi, WEEKEND = samedi-dimanche, DAILY = tous les jours,
    # CUSTOM = jours spécifiques dans days_of_week (CSV: 0=dimanche, 1=lundi, ...)
    recurrence = Column(String(32), nullable=False, default="DAILY")
    days_of_week = Column(String(32), nullable=True)  # CSV si recurrence=CUSTOM

    # Staffing requis
    required_staff_count = Column(Integer, nullable=False, default=1)
    required_profession = Column(String(100), nullable=True)  # MEDECIN, INFIRMIER, etc.

    enabled = Column(Boolean, nullable=False, default=True, index=True)
    description = Column(Text, nullable=True)

    assignments = relationship("ShiftAssignment", back_populates="shift", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "facility_id": self.facility_id,
            "department_id": self.department_id,
            "code": self.code,
            "name": self.name,
            "shift_type": self.shift_type,
            "color": self.color,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_hours": self.duration_hours,
            "recurrence": self.recurrence,
            "days_of_week": [int(d) for d in (self.days_of_week or "").split(",") if d.isdigit()],
            "required_staff_count": self.required_staff_count,
            "required_profession": self.required_profession,
            "enabled": bool(self.enabled),
            "description": self.description,
        }


class ShiftAssignment(Base):
    """Affectation concrète d'un staff à un shift à une date donnée.

    C'est l'unité atomique du planning. Une affectation peut avoir un statut :
    - SCHEDULED : planifiée (défaut)
    - CONFIRMED : confirmée par le staff
    - COMPLETED : effective (post-shift)
    - ABSENT : staff absent (à qualifier)
    - CANCELLED : annulée
    """
    __tablename__ = "shift_assignments"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Périmètre
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)

    # Liens
    shift_id = Column(String(36), ForeignKey("shifts.id"), nullable=False, index=True)
    staff_id = Column(String(36), ForeignKey("staff_members.id"), nullable=False, index=True)

    # Date effective
    assignment_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=True)  # hérité du shift, mais overridable
    end_time = Column(Time, nullable=True)

    # État
    status = Column(String(32), nullable=False, default="SCHEDULED", index=True)
    # SCHEDULED | CONFIRMED | COMPLETED | ABSENT | CANCELLED

    # Note libre
    notes = Column(Text, nullable=True)

    # Audit
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    shift = relationship("Shift", back_populates="assignments", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "facility_id": self.facility_id,
            "department_id": self.department_id,
            "shift_id": self.shift_id,
            "staff_id": self.staff_id,
            "assignment_date": self.assignment_date.isoformat() if self.assignment_date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "notes": self.notes,
            "created_by": self.created_by,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class LeaveBalance(Base):
    """Solde de congés par staff et par année civile.

    Calculé à partir des LeaveRequest approuvées :
    - `accumulated_days` : cumul annuel (droits acquis, généralement 26j/an en Guinée).
    - `used_days` : somme des jours pris (LeaveRequest approuvés sur l'année).
    - `remaining_days = accumulated_days - used_days - pending_days` (calculé à la volée).
    - `pending_days` : jours en attente de validation.
    """
    __tablename__ = "leave_balances"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=False, index=True)
    staff_id = Column(String(36), ForeignKey("staff_members.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)  # 2026, 2027...

    accumulated_days = Column(Integer, nullable=False, default=26)  # droit annuel
    used_days = Column(Integer, nullable=False, default=0)
    carried_over_days = Column(Integer, nullable=False, default=0)  # report de l'année N-1
    pending_days = Column(Integer, nullable=False, default=0)  # recalculé par le service

    notes = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        remaining = self.accumulated_days + self.carried_over_days - self.used_days - self.pending_days
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "facility_id": self.facility_id,
            "staff_id": self.staff_id,
            "year": self.year,
            "accumulated_days": self.accumulated_days,
            "used_days": self.used_days,
            "carried_over_days": self.carried_over_days,
            "pending_days": self.pending_days,
            "remaining_days": remaining,
            "notes": self.notes,
        }


class OnCallDuty(Base):
    """Astreinte (joignabilité, sans présence continue).

    Distincte du Shift classique car :
    - Pas d'horaire fixe (juste une plage de joignabilité).
    - Pas de présentiel requis (sauf `duty_type=PHYSICAL`).
    - Compensée différemment (généralement en jours de récupération).

    Types :
    - TELEPHONIC : astreinte téléphonique (joignable 24h).
    - PHYSICAL : astreinte physique (présent sur site).
    - MIXED : combiné.
    """
    __tablename__ = "on_call_duties"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=False, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)
    staff_id = Column(String(36), ForeignKey("staff_members.id"), nullable=False, index=True)

    # Période d'astreinte (généralement 24h ou week-end)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=False)

    duty_type = Column(String(32), nullable=False, default="TELEPHONIC")
    # TELEPHONIC | PHYSICAL | MIXED

    reason = Column(String(255), nullable=True)  # "Astreinte week-end cardiologie"
    status = Column(String(32), nullable=False, default="SCHEDULED", index=True)
    # SCHEDULED | ACTIVE | COMPLETED | CANCELLED

    compensation_days = Column(Integer, nullable=False, default=1)  # jours de récup accordés
    notes = Column(Text, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "facility_id": self.facility_id,
            "department_id": self.department_id,
            "staff_id": self.staff_id,
            "start_at": self.start_at.isoformat() if self.start_at else None,
            "end_at": self.end_at.isoformat() if self.end_at else None,
            "duty_type": self.duty_type,
            "reason": self.reason,
            "status": self.status,
            "compensation_days": self.compensation_days,
            "notes": self.notes,
            "created_by": self.created_by,
        }


class ShiftSwap(Base):
    """Demande de remplacement entre deux staffs.

    Workflow :
    1. `REQUESTED` : le staff A demande à B de le remplacer sur une affectation.
    2. `ACCEPTED` : B accepte. En attente de validation manager.
    3. `APPROVED` : le manager valide → l'affectation est transférée à B.
       (statut → `COMPLETED` une fois le shift passé)
    4. `REJECTED` : B refuse, ou le manager refuse.
    5. `CANCELLED` : A annule sa demande.

    À l'approbation, le `ShiftAssignment.staff_id` est mis à jour vers B.
    """
    __tablename__ = "shift_swaps"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=False, index=True)
    assignment_id = Column(String(36), ForeignKey("shift_assignments.id"), nullable=False, index=True)

    requester_id = Column(String(36), ForeignKey("staff_members.id"), nullable=False, index=True)
    replacement_id = Column(String(36), ForeignKey("staff_members.id"), nullable=False, index=True)

    reason = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="REQUESTED", index=True)
    # REQUESTED | ACCEPTED | APPROVED | REJECTED | CANCELLED | COMPLETED

    # Workflow timestamps
    accepted_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Approvers
    approved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    rejected_by = Column(String(36), ForeignKey("users.id"), nullable=True)

    manager_note = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "facility_id": self.facility_id,
            "assignment_id": self.assignment_id,
            "requester_id": self.requester_id,
            "replacement_id": self.replacement_id,
            "reason": self.reason,
            "status": self.status,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejected_at": self.rejected_at.isoformat() if self.rejected_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "approved_by": self.approved_by,
            "rejected_by": self.rejected_by,
            "manager_note": self.manager_note,
        }
