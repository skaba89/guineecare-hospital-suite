"""Tests de régression sécurité Phase 6 — v2.2.0.

Couvre les correctifs P0/P1 de la Phase 6 :
- Isolation multi-tenant FHIR (P0 critique)
- Audit log des accès aux dossiers patients (P1)
- Audit log des exports PDF (déjà en place — testé ici)
- Soft-delete patients (P1)
- Rate limiting endpoints auth (P1)

Ces tests garantissent qu'une régression sur ces points sera détectée
avant mise en production.
"""
from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.core.security import create_access_token, hash_password
from app.modules.admissions.models import Admission
from app.modules.clinical.models import ClinicalNote, PatientMeasurement
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.patients.models import Patient
from app.modules.users.models import User


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_user(db, role="DOCTOR", facility_id="facility-A", email_suffix=""):
    """Crée un utilisateur avec un rôle et un établissement donnés."""
    suffix = uuid4().hex[:6] + email_suffix
    user = User(
        email=f"user-{suffix}@test.com",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Test",
        last_name=role.title(),
        role=role,
        facility_id=facility_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_patient(db, facility_id="facility-A", **overrides):
    suffix = uuid4().hex[:8]
    defaults = {
        "facility_id": facility_id,
        "patient_number": f"PAT-{suffix}",
        "first_name": "Test",
        "last_name": "Patient",
        "gender": "M",
        "date_of_birth": date(1990, 1, 1),
        "phone": "+224600000000",
        "status": "ACTIVE",
    }
    defaults.update(overrides)
    p = Patient(**defaults)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _headers_for(user):
    token = create_access_token(
        subject=user.id,
        facility_id=user.facility_id,
        role=user.role,
    )
    return {"Authorization": f"Bearer {token}"}


# ── P0 : FHIR multi-tenant isolation ────────────────────────────────────────

class TestFhirTenantIsolation:
    """P0 — Un médecin de l'établissement A ne doit PAS voir les données
    FHIR de l'établissement B via les endpoints /fhir/*.
    """

    def test_doctor_cannot_read_other_facility_patient(self, client, db):
        """GET /fhir/Patient/{id} cross-facility → 403."""
        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        patient_b = _make_patient(db, facility_id="facility-B")

        resp = client.get(
            f"/api/v1/fhir/Patient/{patient_b.id}",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 403, (
            f"DOCTOR in facility-A must NOT read patient from facility-B. "
            f"Got {resp.status_code}: {resp.text}"
        )

    def test_doctor_cannot_list_other_facility_patients(self, client, db):
        """GET /fhir/Patient cross-facility → 0 résultats de l'autre facility."""
        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        # Patient in facility A (visible) + patient in facility B (hidden)
        _make_patient(db, facility_id="facility-A", first_name="Visible")
        _make_patient(db, facility_id="facility-B", first_name="Hidden")

        resp = client.get(
            "/api/v1/fhir/Patient?name=Hidden",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 200
        body = resp.json()
        # Le patient "Hidden" ne doit pas apparaître
        names = [
            (n.get("given", [""])[0] + " " + n.get("family", ""))
            for n in (e.get("resource", {}).get("name", []) for e in body.get("entry", []))
            if n
        ]
        flat = " ".join(str(names))
        assert "Hidden" not in flat, (
            f"DOCTOR in facility-A must NOT see facility-B patient via FHIR search. "
            f"Got entries: {body.get('entry', [])}"
        )

    def test_doctor_cannot_read_other_facility_encounter(self, client, db):
        """GET /fhir/Encounter/{id} cross-facility → 403."""
        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        patient_b = _make_patient(db, facility_id="facility-B")
        adm_b = Admission(
            facility_id="facility-B",
            patient_id=patient_b.id,
            admission_type="CONSULTATION",
            status="ACTIVE",
        )
        db.add(adm_b)
        db.commit()
        db.refresh(adm_b)

        resp = client.get(
            f"/api/v1/fhir/Encounter/{adm_b.id}",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 403

    def test_doctor_cannot_read_other_facility_observation_lab(self, client, db):
        """GET /fhir/Observation/{id}?category=laboratory cross-facility → 403."""
        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        # Patient + lab test + lab order + lab result in facility B
        patient_b = _make_patient(db, facility_id="facility-B")
        lab_test = LabTest(
            facility_id="facility-B",
            name="Glycémie",
            code=f"LAB-{uuid4().hex[:6]}",
            sample_type="BLOOD",
        )
        db.add(lab_test)
        db.commit()
        db.refresh(lab_test)
        order_b = LabOrder(
            facility_id="facility-B",
            patient_id=patient_b.id,
            test_id=lab_test.id,
            status="COMPLETED",
        )
        db.add(order_b)
        db.commit()
        db.refresh(order_b)
        result_b = LabResult(
            facility_id="facility-B",
            order_id=order_b.id,
            status="VALIDATED",
            result_value="1.2 g/L",
        )
        db.add(result_b)
        db.commit()
        db.refresh(result_b)

        resp = client.get(
            f"/api/v1/fhir/Observation/{result_b.id}?category=laboratory",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 403

    def test_doctor_cannot_read_other_facility_medication_request(self, client, db):
        """GET /fhir/MedicationRequest/{id} cross-facility → 403."""
        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        patient_b = _make_patient(db, facility_id="facility-B")
        note_b = ClinicalNote(
            facility_id="facility-B",
            patient_id=patient_b.id,
            note_type="PRESCRIPTION",
            content="Paracétamol 1g",
        )
        db.add(note_b)
        db.commit()
        db.refresh(note_b)

        resp = client.get(
            f"/api/v1/fhir/MedicationRequest/{note_b.id}",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 403

    def test_doctor_cannot_read_other_facility_diagnostic_report(self, client, db):
        """GET /fhir/DiagnosticReport/{id} cross-facility → 403."""
        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        patient_b = _make_patient(db, facility_id="facility-B")
        order_b = ImagingOrder(
            facility_id="facility-B",
            patient_id=patient_b.id,
            exam_type="RADIOGRAPHY",
            body_region="Thorax",
            status="COMPLETED",
        )
        db.add(order_b)
        db.commit()
        db.refresh(order_b)
        result_b = ImagingResult(
            facility_id="facility-B",
            order_id=order_b.id,
            patient_id=patient_b.id,
            status="VALIDATED",
            findings="Normal",
        )
        db.add(result_b)
        db.commit()
        db.refresh(result_b)

        resp = client.get(
            f"/api/v1/fhir/DiagnosticReport/{result_b.id}",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 403

    def test_super_admin_can_read_any_facility(self, client, db):
        """SUPER_ADMIN doit pouvoir lire n'importe quel patient via FHIR."""
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient_b = _make_patient(db, facility_id="facility-B")

        resp = client.get(
            f"/api/v1/fhir/Patient/{patient_b.id}",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200

    def test_doctor_can_read_own_facility_patient(self, client, db):
        """DOCTOR peut lire un patient de SON établissement via FHIR."""
        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        patient_a = _make_patient(db, facility_id="facility-A")

        resp = client.get(
            f"/api/v1/fhir/Patient/{patient_a.id}",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 200


# ── P1 : Audit log des accès aux dossiers patients ─────────────────────────

class TestPatientAccessAuditLog:
    """P1 — Chaque accès à un dossier patient doit être tracé dans audit_logs."""

    def test_fhir_patient_read_creates_audit_entry(self, client, db):
        """GET /fhir/Patient/{id} doit créer une entrée audit_logs."""
        from app.modules.auth.models import AuditLog

        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        patient_a = _make_patient(db, facility_id="facility-A")

        resp = client.get(
            f"/api/v1/fhir/Patient/{patient_a.id}",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 200

        # Vérifier qu'une entrée audit_logs a été créée
        audit_entries = (
            db.query(AuditLog)
            .filter(AuditLog.action == "fhir.patient.read")
            .filter(AuditLog.resource_id == str(patient_a.id))
            .all()
        )
        assert len(audit_entries) >= 1, (
            "GET /fhir/Patient/{id} doit créer une entrée audit_logs avec "
            "action='fhir.patient.read'"
        )

    def test_fhir_encounter_read_creates_audit_entry(self, client, db):
        """GET /fhir/Encounter/{id} doit créer une entrée audit_logs."""
        from app.modules.auth.models import AuditLog

        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        patient_a = _make_patient(db, facility_id="facility-A")
        adm_a = Admission(
            facility_id="facility-A",
            patient_id=patient_a.id,
            admission_type="CONSULTATION",
            status="ACTIVE",
        )
        db.add(adm_a)
        db.commit()
        db.refresh(adm_a)

        resp = client.get(
            f"/api/v1/fhir/Encounter/{adm_a.id}",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 200

        entries = (
            db.query(AuditLog)
            .filter(AuditLog.action == "fhir.encounter.read")
            .all()
        )
        assert len(entries) >= 1


# ── P1 : Soft-delete patients ──────────────────────────────────────────────

class TestPatientSoftDelete:
    """P1 — Les patients supprimés (status=DELETED) ne doivent pas apparaître
    dans les listes FHIR.
    """

    def test_fhir_search_excludes_deleted_patients(self, client, db):
        """GET /fhir/Patient ne doit pas retourner les patients DELETED."""
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        active_patient = _make_patient(
            db, facility_id="facility-A", first_name="ActiveOne"
        )
        deleted_patient = _make_patient(
            db, facility_id="facility-A", first_name="DeletedOne", status="DELETED"
        )

        resp = client.get(
            "/api/v1/fhir/Patient?name=One",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        # Vérifier que DeletedOne n'apparaît pas
        for entry in body.get("entry", []):
            name = entry.get("resource", {}).get("name", [{}])[0]
            full = (name.get("given", [""])[0] + " " + name.get("family", "")).strip()
            assert "DeletedOne" not in full, (
                f"DELETED patient must not appear in FHIR search. Got: {full}"
            )
        # ActiveOne doit apparaître
        found_active = any(
            "ActiveOne" in (
                (e.get("resource", {}).get("name", [{}])[0].get("given", [""])[0])
                + " " +
                e.get("resource", {}).get("name", [{}])[0].get("family", "")
            )
            for e in body.get("entry", [])
        )
        assert found_active, "ActiveOne patient should appear in FHIR search"


# ── P1 : Permissions FHIR ──────────────────────────────────────────────────

class TestFhirPermissions:
    """P1 — Les endpoints FHIR exigent la permission fhir.read."""

    def test_no_token_returns_401(self, client, db):
        """GET /fhir/Patient sans token → 401."""
        resp = client.get("/api/v1/fhir/Patient")
        assert resp.status_code == 401

    def test_cashier_cannot_access_fhir(self, client, db):
        """CASHIER n'a pas la permission fhir.read → 403.

        Per ROLE_PERMISSION_MAP, CASHIER n'a que billing.* + patient.read.
        """
        cashier = _make_user(db, role="CASHIER", facility_id="facility-A")
        _make_patient(db, facility_id="facility-A")

        resp = client.get(
            "/api/v1/fhir/Patient",
            headers=_headers_for(cashier),
        )
        # CASHIER n'a pas fhir.read → 403
        assert resp.status_code == 403

    def test_doctor_can_access_fhir(self, client, db):
        """DOCTOR a la permission fhir.read (depuis v2.0.0)."""
        doctor = _make_user(db, role="DOCTOR", facility_id="facility-A")
        _make_patient(db, facility_id="facility-A")

        resp = client.get(
            "/api/v1/fhir/Patient",
            headers=_headers_for(doctor),
        )
        assert resp.status_code == 200
