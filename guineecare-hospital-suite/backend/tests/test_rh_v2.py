"""Tests du module RH v2 v1.5.0 — shifts, assignments, planning, soldes, swaps."""
from datetime import date, datetime, time, timedelta

import pytest

from app.modules.personnel.models import LeaveRequest, StaffMember
from app.modules.personnel.rh_v2_models import (
    LeaveBalance,
    OnCallDuty,
    Shift,
    ShiftAssignment,
    ShiftSwap,
)
from app.modules.personnel.rh_v2_service import (
    _matches_recurrence,
    check_conflicts,
)
from app.modules.personnel.rh_v2_service import (
    accept_swap,
    approve_swap,
    cancel_swap,
    create_swap,
    generate_assignments,
    get_or_create_balance,
    get_planning,
    recompute_leave_balance,
    reject_swap,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _create_staff(db, facility_id="facility-pers-001", employee_number="EMP-001", profession="MEDECIN"):
    """Crée un staff de test."""
    s = StaffMember(
        facility_id=facility_id,
        employee_number=employee_number,
        first_name="Test",
        last_name="Staff",
        profession=profession,
        status="ACTIVE",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _create_shift(
    db,
    facility_id="facility-pers-001",
    code="GARDE_NUIT",
    shift_type="NIGHT",
    recurrence="DAILY",
):
    """Crée un shift de test."""
    s = Shift(
        facility_id=facility_id,
        code=code,
        name=f"Shift {code}",
        shift_type=shift_type,
        start_time=time(20, 0),
        end_time=time(8, 0),
        duration_hours=12,
        recurrence=recurrence,
        required_staff_count=1,
        required_profession="MEDECIN",
        enabled=True,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ── Shifts CRUD ─────────────────────────────────────────────────────────────

def test_list_shifts_empty(auth_headers, client):
    """GET /personnel/shifts — liste vide au début."""
    response = client.get("/api/v1/personnel/shifts", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_create_shift(auth_headers, client):
    """POST /personnel/shifts — crée un template de shift."""
    payload = {
        "facility_id": "facility-pers-001",
        "code": "GARDE_MED_NUIT",
        "name": "Garde médecine nuit",
        "shift_type": "NIGHT",
        "color": "#0ea5e9",
        "start_time": "20:00",
        "end_time": "08:00",
        "duration_hours": 12,
        "recurrence": "DAILY",
        "required_staff_count": 1,
        "required_profession": "MEDECIN",
    }
    response = client.post(
        "/api/v1/personnel/shifts", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "GARDE_MED_NUIT"
    assert data["shift_type"] == "NIGHT"
    assert data["start_time"] == "20:00:00"
    assert data["end_time"] == "08:00:00"
    assert data["enabled"] is True


def test_update_shift(auth_headers, client):
    """PATCH /personnel/shifts/{id} — met à jour un shift."""
    create = client.post(
        "/api/v1/personnel/shifts",
        json={
            "facility_id": "facility-pers-001",
            "code": "CONSULT_MORNING",
            "name": "Consultation matin",
            "shift_type": "DAY",
            "start_time": "08:00",
            "end_time": "13:00",
        },
        headers=auth_headers,
    )
    shift_id = create.json()["id"]
    response = client.patch(
        f"/api/v1/personnel/shifts/{shift_id}",
        json={"name": "Consultation matin (étendu)", "end_time": "14:00"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Consultation matin (étendu)"
    assert data["end_time"] == "14:00:00"


def test_delete_shift(auth_headers, client):
    """DELETE /personnel/shifts/{id} — supprime un shift."""
    create = client.post(
        "/api/v1/personnel/shifts",
        json={"facility_id": "facility-pers-001", "code": "TO_DELETE", "name": "Tmp", "shift_type": "DAY"},
        headers=auth_headers,
    )
    shift_id = create.json()["id"]
    response = client.delete(
        f"/api/v1/personnel/shifts/{shift_id}", headers=auth_headers
    )
    assert response.status_code == 204


# ── Generate assignments ────────────────────────────────────────────────────

def test_generate_assignments_weekdays(auth_headers, client, db):
    """POST /personnel/shifts/{id}/generate — génère des affectations sur jours ouvrés."""
    staff = _create_staff(db, employee_number="EMP-GEN-01")
    shift = _create_shift(db, code="GARDE_WEEKDAYS", recurrence="WEEKDAYS")

    payload = {
        "start_date": "2026-06-01",  # lundi
        "end_date": "2026-06-07",    # dimanche
        "staff_id": staff.id,
    }
    response = client.post(
        f"/api/v1/personnel/shifts/{shift.id}/generate",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    # 5 jours ouvrés (lun-ven)
    assert data["generated"] == 5
    assert len(data["assignments"]) == 5


def test_generate_assignments_daily(auth_headers, client, db):
    """POST /personnel/shifts/{id}/generate — récurrence DAILY = tous les jours."""
    staff = _create_staff(db, employee_number="EMP-GEN-02")
    shift = _create_shift(db, code="GARDE_DAILY", recurrence="DAILY")

    payload = {
        "start_date": "2026-06-01",
        "end_date": "2026-06-03",
        "staff_id": staff.id,
    }
    response = client.post(
        f"/api/v1/personnel/shifts/{shift.id}/generate",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["generated"] == 3


def test_generate_assignments_skip_weekends(auth_headers, client, db):
    """POST /personnel/shifts/{id}/generate — skip_weekends=true exclut sam/dim."""
    staff = _create_staff(db, employee_number="EMP-GEN-03")
    shift = _create_shift(db, code="GARDE_SKIP_WE", recurrence="DAILY")

    payload = {
        "start_date": "2026-06-01",  # lundi
        "end_date": "2026-06-07",    # dimanche
        "staff_id": staff.id,
        "skip_weekends": True,
    }
    response = client.post(
        f"/api/v1/personnel/shifts/{shift.id}/generate",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["generated"] == 5


def test_generate_assignments_auto_staff(auth_headers, client, db):
    """POST /personnel/shifts/{id}/generate — staff_id null → auto-sélection."""
    staff = _create_staff(db, employee_number="EMP-GEN-04")
    shift = _create_shift(db, code="GARDE_AUTO", recurrence="DAILY")

    payload = {
        "start_date": "2026-06-01",
        "end_date": "2026-06-01",
        # pas de staff_id → auto
    }
    response = client.post(
        f"/api/v1/personnel/shifts/{shift.id}/generate",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["generated"] == 1
    assert response.json()["assignments"][0]["staff_id"] == staff.id


def test_matches_recurrence_weekdays():
    """_matches_recurrence — WEEKDAYS ne match pas le weekend."""
    shift = Shift(
        facility_id="x", code="x", name="x", shift_type="DAY",
        recurrence="WEEKDAYS", required_staff_count=1, enabled=True,
    )
    monday = date(2026, 6, 1)  # lundi
    sunday = date(2026, 6, 7)  # dimanche
    assert _matches_recurrence(shift, monday) is True
    assert _matches_recurrence(shift, sunday) is False


def test_matches_recurrence_custom():
    """_matches_recurrence — CUSTOM avec days_of_week."""
    shift = Shift(
        facility_id="x", code="x", name="x", shift_type="DAY",
        recurrence="CUSTOM", days_of_week="1,3",  # lundi, mercredi
        required_staff_count=1, enabled=True,
    )
    monday = date(2026, 6, 1)
    tuesday = date(2026, 6, 2)
    wednesday = date(2026, 6, 3)
    assert _matches_recurrence(shift, monday) is True
    assert _matches_recurrence(shift, tuesday) is False
    assert _matches_recurrence(shift, wednesday) is True


# ── Assignments CRUD + conflicts ────────────────────────────────────────────

def test_create_assignment(auth_headers, client, db):
    """POST /personnel/assignments — crée une affectation."""
    staff = _create_staff(db, employee_number="EMP-ASG-01")
    shift = _create_shift(db, code="SHIFT_ASG_TEST")

    payload = {
        "facility_id": "facility-pers-001",
        "shift_id": shift.id,
        "staff_id": staff.id,
        "assignment_date": "2026-06-15",
        "start_time": "20:00",
        "end_time": "08:00",
    }
    response = client.post(
        "/api/v1/personnel/assignments", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["staff_id"] == staff.id
    assert data["assignment_date"] == "2026-06-15"
    assert data["status"] == "SCHEDULED"


def test_list_assignments_filter_staff(auth_headers, client, db):
    """GET /personnel/assignments?staff_id=... — filtre par staff."""
    staff = _create_staff(db, employee_number="EMP-ASG-02")
    shift = _create_shift(db, code="SHIFT_LIST")

    client.post(
        "/api/v1/personnel/assignments",
        json={
            "facility_id": "facility-pers-001",
            "shift_id": shift.id,
            "staff_id": staff.id,
            "assignment_date": "2026-06-15",
        },
        headers=auth_headers,
    )

    response = client.get(
        f"/api/v1/personnel/assignments?staff_id={staff.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(a["staff_id"] == staff.id for a in data["data"])


def test_update_assignment_status(auth_headers, client, db):
    """PATCH /personnel/assignments/{id} — passe de SCHEDULED à CONFIRMED."""
    staff = _create_staff(db, employee_number="EMP-ASG-03")
    shift = _create_shift(db, code="SHIFT_UPD")

    create = client.post(
        "/api/v1/personnel/assignments",
        json={
            "facility_id": "facility-pers-001",
            "shift_id": shift.id,
            "staff_id": staff.id,
            "assignment_date": "2026-06-15",
        },
        headers=auth_headers,
    )
    assignment_id = create.json()["id"]

    response = client.patch(
        f"/api/v1/personnel/assignments/{assignment_id}",
        json={"status": "CONFIRMED"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"
    assert response.json()["confirmed_at"] is not None


def test_check_conflicts_no_overlap(db):
    """check_conflicts — pas de conflit si staff libre ce jour."""
    staff = _create_staff(db, employee_number="EMP-CFL-01")
    # Aucune affectation existante → pas de conflit
    conflicts = check_conflicts(
        db=db,
        staff_id=staff.id,
        assignment_date=date(2026, 6, 15),
        start_time=time(8, 0),
        end_time=time(12, 0),
    )
    assert conflicts == []


def test_check_conflicts_same_day(db):
    """check_conflicts — conflit si staff déjà affecté ce jour (sans horaire)."""
    staff = _create_staff(db, employee_number="EMP-CFL-02")
    shift = _create_shift(db, code="SHIFT_CFL")
    # Affectation existante
    existing = ShiftAssignment(
        facility_id="facility-pers-001",
        shift_id=shift.id,
        staff_id=staff.id,
        assignment_date=date(2026, 6, 15),
        status="SCHEDULED",
    )
    db.add(existing)
    db.commit()

    conflicts = check_conflicts(
        db=db,
        staff_id=staff.id,
        assignment_date=date(2026, 6, 15),
    )
    assert len(conflicts) == 1


# ── Planning view ───────────────────────────────────────────────────────────

def test_get_planning(auth_headers, client, db):
    """GET /personnel/planning — retourne rows × cells pour la période."""
    staff = _create_staff(db, employee_number="EMP-PLN-01")
    shift = _create_shift(db, code="SHIFT_PLN")

    # Créer 2 affectations
    for d in ["2026-06-15", "2026-06-16"]:
        client.post(
            "/api/v1/personnel/assignments",
            json={
                "facility_id": "facility-pers-001",
                "shift_id": shift.id,
                "staff_id": staff.id,
                "assignment_date": d,
            },
            headers=auth_headers,
        )

    response = client.get(
        "/api/v1/personnel/planning?start_date=2026-06-15&end_date=2026-06-16",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert "days" in data
    assert len(data["days"]) == 2
    # Au moins 1 staff dans les rows
    assert len(data["rows"]) >= 1
    # Le staff a 2 affectations au total sur la période
    assert data["summary"]["total_assignments"] >= 2


def test_get_planning_invalid_period(auth_headers, client):
    """GET /personnel/planning — 400 si end < start."""
    response = client.get(
        "/api/v1/personnel/planning?start_date=2026-06-16&end_date=2026-06-15",
        headers=auth_headers,
    )
    assert response.status_code == 400


def test_get_planning_period_too_long(auth_headers, client):
    """GET /personnel/planning — 400 si période > 90 jours."""
    response = client.get(
        "/api/v1/personnel/planning?start_date=2026-01-01&end_date=2026-06-30",
        headers=auth_headers,
    )
    assert response.status_code == 400


# ── Leave Balances ──────────────────────────────────────────────────────────

def test_create_leave_balance(auth_headers, client, db):
    """POST /personnel/leave-balances — crée un solde de congés."""
    staff = _create_staff(db, employee_number="EMP-LB-01")
    payload = {
        "facility_id": "facility-pers-001",
        "staff_id": staff.id,
        "year": 2026,
        "accumulated_days": 30,
        "carried_over_days": 5,
    }
    response = client.post(
        "/api/v1/personnel/leave-balances", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["year"] == 2026
    assert data["accumulated_days"] == 30
    assert data["carried_over_days"] == 5
    # remaining = 30 + 5 - 0 - 0 = 35
    assert data["remaining_days"] == 35


def test_get_staff_balance_auto_create(auth_headers, client, db):
    """GET /personnel/leave-balances/by-staff/{id}?year=... — crée le solde s'il n'existe pas."""
    staff = _create_staff(db, employee_number="EMP-LB-02")
    response = client.get(
        f"/api/v1/personnel/leave-balances/by-staff/{staff.id}?year=2026",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["year"] == 2026
    assert data["accumulated_days"] == 26  # default Guinée
    assert data["remaining_days"] == 26


def test_recompute_leave_balance_with_approved_leave(db):
    """recompute_leave_balance — used_days mis à jour avec LeaveRequest APPROVED."""
    staff = _create_staff(db, employee_number="EMP-LB-03")
    balance = LeaveBalance(
        facility_id="facility-pers-001",
        staff_id=staff.id,
        year=2026,
        accumulated_days=26,
    )
    db.add(balance)
    db.commit()
    db.refresh(balance)

    # Ajouter un congé approuvé de 5 jours
    leave = LeaveRequest(
        facility_id="facility-pers-001",
        staff_id=staff.id,
        leave_type="CONGE_ANNUEL",
        start_date=date(2026, 7, 1),
        end_date=date(2026, 7, 5),
        status="APPROVED",
    )
    db.add(leave)
    db.commit()

    recompute_leave_balance(db, balance)
    assert balance.used_days == 5
    assert balance.pending_days == 0
    assert balance.accumulated_days == 26
    # remaining = 26 + 0 - 5 - 0 = 21
    # (calculé dans to_dict / from_model)


def test_recompute_leave_balance_with_pending_leave(db):
    """recompute_leave_balance — pending_days mis à jour avec LeaveRequest PENDING."""
    staff = _create_staff(db, employee_number="EMP-LB-04")
    balance = LeaveBalance(
        facility_id="facility-pers-001",
        staff_id=staff.id,
        year=2026,
        accumulated_days=26,
    )
    db.add(balance)
    db.commit()
    db.refresh(balance)

    leave = LeaveRequest(
        facility_id="facility-pers-001",
        staff_id=staff.id,
        leave_type="CONGE_ANNUEL",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 3),
        status="PENDING",
    )
    db.add(leave)
    db.commit()

    recompute_leave_balance(db, balance)
    assert balance.used_days == 0
    assert balance.pending_days == 3


# ── On-Call Duties ──────────────────────────────────────────────────────────

def test_create_on_call_duty(auth_headers, client, db):
    """POST /personnel/on-call-duties — planifie une astreinte."""
    staff = _create_staff(db, employee_number="EMP-OC-01")
    payload = {
        "facility_id": "facility-pers-001",
        "staff_id": staff.id,
        "start_at": "2026-06-20T18:00:00",
        "end_at": "2026-06-21T08:00:00",
        "duty_type": "TELEPHONIC",
        "reason": "Astreinte week-end cardiologie",
        "compensation_days": 1,
    }
    response = client.post(
        "/api/v1/personnel/on-call-duties", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["duty_type"] == "TELEPHONIC"
    assert data["status"] == "SCHEDULED"
    assert data["compensation_days"] == 1


def test_on_call_duty_invalid_dates(auth_headers, client, db):
    """POST /personnel/on-call-duties — 400 si end_at <= start_at."""
    staff = _create_staff(db, employee_number="EMP-OC-02")
    payload = {
        "facility_id": "facility-pers-001",
        "staff_id": staff.id,
        "start_at": "2026-06-20T18:00:00",
        "end_at": "2026-06-20T18:00:00",  # égal à start_at
    }
    response = client.post(
        "/api/v1/personnel/on-call-duties", json=payload, headers=auth_headers
    )
    assert response.status_code == 400


def test_list_on_call_duties(auth_headers, client, db):
    """GET /personnel/on-call-duties — liste filtrée."""
    staff = _create_staff(db, employee_number="EMP-OC-03")
    client.post(
        "/api/v1/personnel/on-call-duties",
        json={
            "facility_id": "facility-pers-001",
            "staff_id": staff.id,
            "start_at": "2026-06-20T18:00:00",
            "end_at": "2026-06-21T08:00:00",
        },
        headers=auth_headers,
    )

    response = client.get(
        f"/api/v1/personnel/on-call-duties?staff_id={staff.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1


# ── Shift Swaps ─────────────────────────────────────────────────────────────

def test_create_swap_request(auth_headers, client, db):
    """POST /personnel/swaps — crée une demande de remplacement."""
    staff1 = _create_staff(db, employee_number="EMP-SW-01")
    staff2 = _create_staff(db, employee_number="EMP-SW-02", profession="MEDECIN")
    shift = _create_shift(db, code="SHIFT_SWAP_TEST")

    # Créer une affectation pour staff1
    create = client.post(
        "/api/v1/personnel/assignments",
        json={
            "facility_id": "facility-pers-001",
            "shift_id": shift.id,
            "staff_id": staff1.id,
            "assignment_date": "2026-06-25",
        },
        headers=auth_headers,
    )
    assignment_id = create.json()["id"]

    # Demander un swap vers staff2
    response = client.post(
        "/api/v1/personnel/swaps",
        json={
            "facility_id": "facility-pers-001",
            "assignment_id": assignment_id,
            "replacement_id": staff2.id,
            "reason": "Congé imprévu",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "REQUESTED"
    assert data["requester_id"] == staff1.id
    assert data["replacement_id"] == staff2.id


def test_swap_workflow_accept_approve(auth_headers, client, db):
    """Workflow complet : REQUESTED → ACCEPTED → APPROVED."""
    staff1 = _create_staff(db, employee_number="EMP-SW-03")
    staff2 = _create_staff(db, employee_number="EMP-SW-04")
    shift = _create_shift(db, code="SHIFT_SWAP_WF")

    create = client.post(
        "/api/v1/personnel/assignments",
        json={
            "facility_id": "facility-pers-001",
            "shift_id": shift.id,
            "staff_id": staff1.id,
            "assignment_date": "2026-06-26",
        },
        headers=auth_headers,
    )
    assignment_id = create.json()["id"]

    swap = client.post(
        "/api/v1/personnel/swaps",
        json={
            "facility_id": "facility-pers-001",
            "assignment_id": assignment_id,
            "replacement_id": staff2.id,
        },
        headers=auth_headers,
    )
    swap_id = swap.json()["id"]

    # Accept
    response = client.post(
        f"/api/v1/personnel/swaps/{swap_id}/accept", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"

    # Approve
    response = client.post(
        f"/api/v1/personnel/swaps/{swap_id}/approve",
        json={"manager_note": "OK pour échange"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    assert response.json()["approved_by"] is not None

    # Vérifier que l'affectation est transférée à staff2
    assign_resp = client.get(
        f"/api/v1/personnel/assignments?staff_id={staff2.id}",
        headers=auth_headers,
    )
    assert any(a["id"] == assignment_id for a in assign_resp.json()["data"])


def test_swap_reject(auth_headers, client, db):
    """POST /personnel/swaps/{id}/reject — manager refuse."""
    staff1 = _create_staff(db, employee_number="EMP-SW-05")
    staff2 = _create_staff(db, employee_number="EMP-SW-06")
    shift = _create_shift(db, code="SHIFT_SWAP_REJ")

    create = client.post(
        "/api/v1/personnel/assignments",
        json={
            "facility_id": "facility-pers-001",
            "shift_id": shift.id,
            "staff_id": staff1.id,
            "assignment_date": "2026-06-27",
        },
        headers=auth_headers,
    )
    assignment_id = create.json()["id"]

    swap = client.post(
        "/api/v1/personnel/swaps",
        json={
            "facility_id": "facility-pers-001",
            "assignment_id": assignment_id,
            "replacement_id": staff2.id,
        },
        headers=auth_headers,
    )
    swap_id = swap.json()["id"]

    response = client.post(
        f"/api/v1/personnel/swaps/{swap_id}/reject",
        json={"manager_note": "Effectif insuffisant"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_swap_cancel(auth_headers, client, db):
    """POST /personnel/swaps/{id}/cancel — requester annule."""
    staff1 = _create_staff(db, employee_number="EMP-SW-07")
    staff2 = _create_staff(db, employee_number="EMP-SW-08")
    shift = _create_shift(db, code="SHIFT_SWAP_CANC")

    create = client.post(
        "/api/v1/personnel/assignments",
        json={
            "facility_id": "facility-pers-001",
            "shift_id": shift.id,
            "staff_id": staff1.id,
            "assignment_date": "2026-06-28",
        },
        headers=auth_headers,
    )
    assignment_id = create.json()["id"]

    swap = client.post(
        "/api/v1/personnel/swaps",
        json={
            "facility_id": "facility-pers-001",
            "assignment_id": assignment_id,
            "replacement_id": staff2.id,
        },
        headers=auth_headers,
    )
    swap_id = swap.json()["id"]

    response = client.post(
        f"/api/v1/personnel/swaps/{swap_id}/cancel", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


# ── Permissions ─────────────────────────────────────────────────────────────

def test_rh_v2_endpoints_require_auth(client):
    """GET /personnel/shifts sans auth → 401."""
    response = client.get("/api/v1/personnel/shifts")
    assert response.status_code == 401
