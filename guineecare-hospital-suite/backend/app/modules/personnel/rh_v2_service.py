"""Service RH v2 v1.5.0 — génération de planning, conflits, soldes congés, swaps.

Responsabilités :
- `generate_assignments()` : génère des ShiftAssignments à partir d'un Shift
  récurrent sur une période (en respectant la récurrence WEEKDAYS/WEEKEND/CUSTOM).
- `check_conflicts()` : détecte les conflits (staff déjà affecté le même jour).
- `find_replacement()` : suggère un staff éligible pour remplacer (même
  profession, pas en congé, pas déjà affecté).
- `approve_swap()` : valide un swap → transfère l'affectation au remplaçant.
- `recompute_leave_balance()` : recalcule `used_days` et `pending_days` à
  partir des LeaveRequest.
- `get_planning()` : construit la vue planning hebdo (rows × cells).
"""
import logging
from datetime import date, datetime, time, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.datetime import utcnow
from app.modules.personnel.models import LeaveRequest, StaffMember
from app.modules.personnel.rh_v2_models import (
    LeaveBalance,
    OnCallDuty,
    Shift,
    ShiftAssignment,
    ShiftSwap,
)

logger = logging.getLogger("guineecare.rh_v2")


# ---------------------------------------------------------------------------
# Generate assignments from a recurring shift
# ---------------------------------------------------------------------------

def _parse_time(s: str | None) -> time | None:
    """Parse 'HH:MM' or 'HH:MM:SS' → time. None si vide."""
    if not s:
        return None
    parts = s.split(":")
    if len(parts) == 2:
        return time(int(parts[0]), int(parts[1]))
    if len(parts) == 3:
        return time(int(parts[0]), int(parts[1]), int(parts[2]))
    return None


def _matches_recurrence(shift: Shift, d: date) -> bool:
    """Vérifie si un shift récurrent s'applique à une date donnée."""
    weekday = d.weekday()  # 0=lundi, 6=dimanche
    # Convertir vers convention days_of_week : 0=dimanche...6=samedi
    dow_convention = (weekday + 1) % 7

    if shift.recurrence == "DAILY":
        return True
    if shift.recurrence == "WEEKDAYS":
        return weekday < 5  # lundi-vendredi
    if shift.recurrence == "WEEKEND":
        return weekday >= 5  # samedi-dimanche
    if shift.recurrence == "CUSTOM":
        if not shift.days_of_week:
            return False
        days = [int(x) for x in shift.days_of_week.split(",") if x.isdigit()]
        return dow_convention in days
    return True


def generate_assignments(
    db: Session,
    shift: Shift,
    start_date: date,
    end_date: date,
    staff_id: str | None = None,
    skip_weekends: bool = False,
    skip_weekdays: bool = False,
    created_by: str | None = None,
) -> tuple[list[ShiftAssignment], int]:
    """Génère des ShiftAssignments pour un shift récurrent sur une période.

    Pour chaque jour de la période, si le shift s'applique (selon sa récurrence),
    crée une affectation. Si `staff_id` est null, ne crée pas d'affectation
    (laissée pour affectation manuelle ultérieure).

    Returns:
        Tuple (assignments_created, days_skipped).
    """
    if end_date < start_date:
        return [], 0

    assignments: list[ShiftAssignment] = []
    skipped = 0
    current = start_date
    while current <= end_date:
        weekday = current.weekday()
        if skip_weekends and weekday >= 5:
            skipped += 1
            current += timedelta(days=1)
            continue
        if skip_weekdays and weekday < 5:
            skipped += 1
            current += timedelta(days=1)
            continue
        if not _matches_recurrence(shift, current):
            current += timedelta(days=1)
            continue

        # Vérifier qu'il n'y a pas déjà une affectation pour ce shift à cette date
        existing = (
            db.query(ShiftAssignment)
            .filter(ShiftAssignment.shift_id == shift.id)
            .filter(ShiftAssignment.assignment_date == current)
            .filter(ShiftAssignment.status != "CANCELLED")
            .first()
        )
        if existing:
            skipped += 1
            current += timedelta(days=1)
            continue

        assignment = ShiftAssignment(
            facility_id=shift.facility_id,
            department_id=shift.department_id,
            shift_id=shift.id,
            staff_id=staff_id or _find_eligible_staff(db, shift, current),
            assignment_date=current,
            start_time=shift.start_time,
            end_time=shift.end_time,
            status="SCHEDULED",
            created_by=created_by,
        )
        db.add(assignment)
        assignments.append(assignment)
        current += timedelta(days=1)

    db.commit()
    for a in assignments:
        db.refresh(a)
    return assignments, skipped


def _find_eligible_staff(db: Session, shift: Shift, d: date) -> str | None:
    """Trouve un staff éligible pour un shift à une date donnée.

    Critères :
    - Même facility_id et department_id (si défini sur le shift).
    - Profession requise correspondante (si définie).
    - Statut ACTIVE.
    - Pas déjà affecté ce jour-là (conflit).
    - Pas en congé approuvé.
    """
    q = (
        db.query(StaffMember)
        .filter(StaffMember.facility_id == shift.facility_id)
        .filter(StaffMember.status == "ACTIVE")
    )
    if shift.department_id:
        q = q.filter(StaffMember.department_id == shift.department_id)
    if shift.required_profession:
        q = q.filter(StaffMember.profession == shift.required_profession)

    candidates = q.all()
    for staff in candidates:
        # Conflit : déjà affecté ce jour-là (sauf si annulé)
        conflict = (
            db.query(ShiftAssignment)
            .filter(ShiftAssignment.staff_id == staff.id)
            .filter(ShiftAssignment.assignment_date == d)
            .filter(ShiftAssignment.status != "CANCELLED")
            .first()
        )
        if conflict:
            continue

        # En congé approuvé ?
        on_leave = (
            db.query(LeaveRequest)
            .filter(LeaveRequest.staff_id == staff.id)
            .filter(LeaveRequest.status == "APPROVED")
            .filter(LeaveRequest.start_date <= d)
            .filter(LeaveRequest.end_date >= d)
            .first()
        )
        if on_leave:
            continue

        return staff.id

    return None


# ---------------------------------------------------------------------------
# Conflicts detection
# ---------------------------------------------------------------------------

def check_conflicts(
    db: Session,
    staff_id: str,
    assignment_date: date,
    start_time: time | None = None,
    end_time: time | None = None,
    exclude_assignment_id: str | None = None,
) -> list[ShiftAssignment]:
    """Détecte les conflits pour un staff à une date donnée.

    Conflit = staff déjà affecté à un autre shift le même jour (non annulé).
    Si start_time/end_time fournis, vérifie aussi le chevauchement horaire.
    """
    q = (
        db.query(ShiftAssignment)
        .filter(ShiftAssignment.staff_id == staff_id)
        .filter(ShiftAssignment.assignment_date == assignment_date)
        .filter(ShiftAssignment.status != "CANCELLED")
    )
    if exclude_assignment_id:
        q = q.filter(ShiftAssignment.id != exclude_assignment_id)
    candidates = q.all()

    if not start_time or not end_time:
        return candidates  # conflit simple (même jour)

    # Conflit horaire : chevauchement
    conflicts = []
    for c in candidates:
        c_start = c.start_time or time(0, 0)
        c_end = c.end_time or time(23, 59)
        if start_time < c_end and end_time > c_start:
            conflicts.append(c)
    return conflicts


# ---------------------------------------------------------------------------
# Leave balance recomputation
# ---------------------------------------------------------------------------

def recompute_leave_balance(db: Session, balance: LeaveBalance) -> LeaveBalance:
    """Recalcule `used_days` et `pending_days` à partir des LeaveRequest.

    - `used_days` : somme des jours de LeaveRequest approuvés sur l'année.
    - `pending_days` : somme des jours de LeaveRequest en attente (PENDING).
    """
    year_start = date(balance.year, 1, 1)
    year_end = date(balance.year, 12, 31)

    leaves = (
        db.query(LeaveRequest)
        .filter(LeaveRequest.staff_id == balance.staff_id)
        .filter(LeaveRequest.start_date <= year_end)
        .filter(LeaveRequest.end_date >= year_start)
        .all()
    )

    used = 0
    pending = 0
    for leave in leaves:
        # Calculer le nombre de jours dans l'année
        effective_start = max(leave.start_date, year_start)
        effective_end = min(leave.end_date, year_end)
        days = (effective_end - effective_start).days + 1

        if leave.status == "APPROVED":
            used += days
        elif leave.status == "PENDING":
            pending += days

    balance.used_days = used
    balance.pending_days = pending
    db.commit()
    db.refresh(balance)
    return balance


def get_or_create_balance(
    db: Session, staff_id: str, facility_id: str, year: int
) -> LeaveBalance:
    """Récupère ou crée le solde de congés d'un staff pour une année."""
    balance = (
        db.query(LeaveBalance)
        .filter(LeaveBalance.staff_id == staff_id)
        .filter(LeaveBalance.year == year)
        .first()
    )
    if balance:
        return recompute_leave_balance(db, balance)

    balance = LeaveBalance(
        facility_id=facility_id,
        staff_id=staff_id,
        year=year,
        accumulated_days=26,  # défaut légal Guinée
        used_days=0,
        carried_over_days=0,
        pending_days=0,
    )
    db.add(balance)
    db.commit()
    db.refresh(balance)
    return recompute_leave_balance(db, balance)


# ---------------------------------------------------------------------------
# Swap workflow
# ---------------------------------------------------------------------------

def create_swap(
    db: Session,
    *,
    assignment: ShiftAssignment,
    replacement_id: str,
    requester_id: str | None = None,
    reason: str | None = None,
) -> ShiftSwap:
    """Crée une demande de swap. Le requester est déduit de l'affectation."""
    # Le requester est le staff actuellement affecté
    actual_requester = requester_id or assignment.staff_id
    swap = ShiftSwap(
        facility_id=assignment.facility_id,
        assignment_id=assignment.id,
        requester_id=actual_requester,
        replacement_id=replacement_id,
        reason=reason,
        status="REQUESTED",
    )
    db.add(swap)
    db.commit()
    db.refresh(swap)
    return swap


def accept_swap(db: Session, swap: ShiftSwap) -> ShiftSwap:
    """Le remplaçant accepte la demande → ACCEPTED."""
    if swap.status != "REQUESTED":
        return swap
    swap.status = "ACCEPTED"
    swap.accepted_at = utcnow()
    db.commit()
    db.refresh(swap)
    return swap


def approve_swap(
    db: Session, swap: ShiftSwap, approver_id: str, note: str | None = None
) -> ShiftSwap:
    """Le manager approuve le swap → APPROVED. Transfère l'affectation au remplaçant."""
    if swap.status not in ("REQUESTED", "ACCEPTED"):
        return swap

    # Transférer l'affectation
    assignment = (
        db.query(ShiftAssignment)
        .filter(ShiftAssignment.id == swap.assignment_id)
        .first()
    )
    if assignment:
        assignment.staff_id = swap.replacement_id
        assignment.status = "SCHEDULED"  # reset pour le nouveau titulaire

    swap.status = "APPROVED"
    swap.approved_at = utcnow()
    swap.approved_by = approver_id
    swap.manager_note = note
    db.commit()
    db.refresh(swap)
    return swap


def reject_swap(
    db: Session, swap: ShiftSwap, rejecter_id: str, note: str | None = None
) -> ShiftSwap:
    """Le manager (ou le remplaçant lui-même) refuse le swap → REJECTED."""
    if swap.status in ("APPROVED", "COMPLETED", "CANCELLED"):
        return swap
    swap.status = "REJECTED"
    swap.rejected_at = utcnow()
    swap.rejected_by = rejecter_id
    swap.manager_note = note
    db.commit()
    db.refresh(swap)
    return swap


def cancel_swap(db: Session, swap: ShiftSwap) -> ShiftSwap:
    """Le requester annule sa demande → CANCELLED."""
    if swap.status in ("APPROVED", "COMPLETED"):
        return swap  # trop tard pour annuler
    swap.status = "CANCELLED"
    swap.cancelled_at = utcnow()
    db.commit()
    db.refresh(swap)
    return swap


# ---------------------------------------------------------------------------
# Planning view
# ---------------------------------------------------------------------------

def get_planning(
    db: Session,
    *,
    facility_id: str | None = None,
    department_id: str | None = None,
    start_date: date,
    end_date: date,
    staff_ids: list[str] | None = None,
) -> dict:
    """Construit la vue planning hebdo/mensuel.

    Returns un dict avec :
    - rows : une ligne par staff, contenant une cellule par jour.
    - summary : compteurs par statut.
    """
    # Récupérer les staffs éligibles
    staff_q = db.query(StaffMember).filter(StaffMember.status == "ACTIVE")
    if facility_id:
        staff_q = staff_q.filter(StaffMember.facility_id == facility_id)
    if department_id:
        staff_q = staff_q.filter(StaffMember.department_id == department_id)
    if staff_ids:
        staff_q = staff_q.filter(StaffMember.id.in_(staff_ids))
    staffs = staff_q.order_by(StaffMember.last_name, StaffMember.first_name).all()

    # Récupérer les affectations sur la période
    assign_q = (
        db.query(ShiftAssignment)
        .filter(ShiftAssignment.assignment_date >= start_date)
        .filter(ShiftAssignment.assignment_date <= end_date)
        .filter(ShiftAssignment.status != "CANCELLED")
    )
    if facility_id:
        assign_q = assign_q.filter(ShiftAssignment.facility_id == facility_id)
    if department_id:
        assign_q = assign_q.filter(ShiftAssignment.department_id == department_id)
    assignments = assign_q.all()

    # Indexer par (staff_id, date)
    by_staff_date: dict[tuple[str, date], list[ShiftAssignment]] = {}
    for a in assignments:
        key = (a.staff_id, a.assignment_date)
        by_staff_date.setdefault(key, []).append(a)

    # Construire les rows
    rows = []
    summary = {"total_assignments": len(assignments), "by_status": {}, "by_staff": {}}
    for a in assignments:
        summary["by_status"][a.status] = summary["by_status"].get(a.status, 0) + 1

    current = start_date
    days = []
    while current <= end_date:
        days.append(current)
        current += timedelta(days=1)

    for staff in staffs:
        cells = []
        staff_count = 0
        for d in days:
            cell_assignments = by_staff_date.get((staff.id, d), [])
            staff_count += len(cell_assignments)
            cells.append({
                "staff_id": staff.id,
                "date": d.isoformat(),
                "assignments": [a.to_dict() for a in cell_assignments],
            })
        summary["by_staff"][staff.id] = staff_count
        rows.append({
            "staff_id": staff.id,
            "staff_name": f"{staff.first_name} {staff.last_name}",
            "employee_number": staff.employee_number,
            "profession": staff.profession,
            "cells": cells,
        })

    return {
        "facility_id": facility_id,
        "department_id": department_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "days": [d.isoformat() for d in days],
        "rows": rows,
        "summary": summary,
    }
