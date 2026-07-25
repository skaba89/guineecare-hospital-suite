"""Tests Phase 7 — Améliorations métier (v2.6.0).

Couvre :
- Prescriptions structurées (POST /clinical/prescriptions)
- Lab panel (POST /laboratory/orders/panel)
- Maternity risk alerts auto (GET /maternity/alerts)
"""
from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.core.security import create_access_token, hash_password
from app.modules.clinical.models import Prescription
from app.modules.laboratory.models import LabOrder, LabOrderTest, LabTest
from app.modules.maternity.models import MaternityConsultation, MaternityRecord
from app.modules.patients.models import Patient
from app.modules.users.models import User


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_user(db, role="SUPER_ADMIN", facility_id=None):
    suffix = uuid4().hex[:6]
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


def _make_patient(db, facility_id="facility-A"):
    suffix = uuid4().hex[:8]
    p = Patient(
        facility_id=facility_id,
        patient_number=f"PAT-{suffix}",
        first_name="Test",
        last_name="Patient",
        gender="F",
        date_of_birth=date(1995, 1, 1),
        phone="+224600000000",
        status="ACTIVE",
    )
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


# ── Prescriptions structurées ──────────────────────────────────────────────

class TestStructuredPrescriptions:
    def test_create_prescription_success(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        resp = client.post(
            "/api/v1/clinical/prescriptions",
            json={
                "patient_id": str(patient.id),
                "medication_name": "Paracétamol",
                "dosage": "500mg",
                "frequency": "3 fois par jour",
                "duration": "7 jours",
                "quantity": 21,
                "instructions": "À prendre avec un grand verre d'eau",
            },
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["medication_name"] == "Paracétamol"
        assert body["data"]["dosage"] == "500mg"
        assert body["data"]["status"] == "ACTIVE"
        assert body["data"]["quantity"] == 21

    def test_create_prescription_missing_fields(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        resp = client.post(
            "/api/v1/clinical/prescriptions",
            json={
                "patient_id": str(patient.id),
                "medication_name": "Amoxicilline",
                # dosage + frequency manquants
            },
            headers=_headers_for(admin),
        )
        assert resp.status_code == 422

    def test_list_prescriptions(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        # Créer 2 prescriptions
        for med in ["Paracétamol", "Ibuprofène"]:
            rx = Prescription(
                facility_id="facility-A",
                patient_id=patient.id,
                medication_name=med,
                dosage="500mg",
                frequency="2 fois par jour",
                status="ACTIVE",
                prescribed_by=str(admin.id),
            )
            db.add(rx)
        db.commit()

        resp = client.get(
            "/api/v1/clinical/prescriptions",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 2

    def test_list_patient_prescriptions(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        rx = Prescription(
            facility_id="facility-A",
            patient_id=patient.id,
            medication_name="Amoxicilline",
            dosage="1g",
            frequency="2 fois par jour",
            status="ACTIVE",
        )
        db.add(rx)
        db.commit()

        resp = client.get(
            f"/api/v1/clinical/patients/{patient.id}/prescriptions",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] >= 1
        assert body["data"][0]["medication_name"] == "Amoxicilline"

    def test_cancel_prescription(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        rx = Prescription(
            facility_id="facility-A",
            patient_id=patient.id,
            medication_name="Métronidazole",
            dosage="500mg",
            frequency="3 fois par jour",
            status="ACTIVE",
        )
        db.add(rx)
        db.commit()
        db.refresh(rx)

        resp = client.patch(
            f"/api/v1/clinical/prescriptions/{rx.id}/cancel",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "CANCELLED"


# ── Lab panel (1 commande = N tests) ───────────────────────────────────────

class TestLabPanel:
    def test_create_panel_with_multiple_tests(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        # Créer 3 tests
        tests = []
        for name in ["NFS", "CRP", "Glycémie"]:
            t = LabTest(
                facility_id="facility-A",
                code=f"LAB-{uuid4().hex[:6]}",
                name=name,
                sample_type="BLOOD",
            )
            db.add(t)
            tests.append(t)
        db.commit()

        resp = client.post(
            "/api/v1/laboratory/orders/panel",
            json={
                "patient_id": str(patient.id),
                "priority": "URGENT",
                "test_ids": [str(t.id) for t in tests],
            },
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["total_tests"] == 3
        assert body["data"]["priority"] == "URGENT"
        assert len(body["data"]["panel_tests"]) == 3

        # Vérifier que les LabOrderTest ont été créés
        order_id = body["data"]["order_id"]
        items = db.query(LabOrderTest).filter(LabOrderTest.order_id == order_id).all()
        assert len(items) == 3

    def test_create_panel_empty_tests_list(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        resp = client.post(
            "/api/v1/laboratory/orders/panel",
            json={
                "patient_id": str(patient.id),
                "test_ids": [],
            },
            headers=_headers_for(admin),
        )
        assert resp.status_code == 422

    def test_get_panel_details(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        test1 = LabTest(facility_id="facility-A", code=f"T1-{uuid4().hex[:6]}", name="NFS", sample_type="BLOOD")
        test2 = LabTest(facility_id="facility-A", code=f"T2-{uuid4().hex[:6]}", name="CRP", sample_type="BLOOD")
        db.add_all([test1, test2])
        db.commit()
        db.refresh(test1)
        db.refresh(test2)

        # Créer le panel
        create_resp = client.post(
            "/api/v1/laboratory/orders/panel",
            json={
                "patient_id": str(patient.id),
                "test_ids": [str(test1.id), str(test2.id)],
            },
            headers=_headers_for(admin),
        )
        order_id = create_resp.json()["data"]["order_id"]

        # Récupérer les détails
        resp = client.get(
            f"/api/v1/laboratory/orders/{order_id}/panel",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total_tests"] == 2
        test_names = [t["test_name"] for t in body["data"]["tests"]]
        assert "NFS" in test_names
        assert "CRP" in test_names

    def test_enter_panel_result(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        test = LabTest(facility_id="facility-A", code=f"T-{uuid4().hex[:6]}", name="Glycémie", sample_type="BLOOD")
        db.add(test)
        db.commit()
        db.refresh(test)

        # Créer panel
        create_resp = client.post(
            "/api/v1/laboratory/orders/panel",
            json={
                "patient_id": str(patient.id),
                "test_ids": [str(test.id)],
            },
            headers=_headers_for(admin),
        )
        order_id = create_resp.json()["data"]["order_id"]
        item_id = create_resp.json()["data"]["panel_tests"][0]["item_id"]

        # Saisir résultat
        resp = client.patch(
            f"/api/v1/laboratory/orders/{order_id}/panel/{item_id}/result",
            json={
                "result_value": "1.2 g/L",
                "interpretation": "Normal",
            },
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["result_value"] == "1.2 g/L"
        assert body["data"]["status"] == "RESULT_ENTERED"


# ── Maternity risk alerts ──────────────────────────────────────────────────

class TestMaternityAlerts:
    def test_alerts_detects_hypertension(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        # Créer un MaternityRecord actif
        record = MaternityRecord(
            facility_id="facility-A",
            patient_id=patient.id,
            last_menstrual_period=date(2026, 1, 1),
            expected_due_date=date(2026, 10, 8),
            gravidity=1,
            parity=0,
            risk_level="LOW",
            status="ACTIVE",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # Consultation prénatale avec HTA (150/95)
        consult = MaternityConsultation(
            facility_id="facility-A",
            record_id=record.id,
            consultation_type="PRENATAL",
            blood_pressure="150/95",
            weight_kg=65,
        )
        db.add(consult)
        db.commit()

        resp = client.get(
            "/api/v1/maternity/alerts",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["alerts_count"] >= 1
        # Doit détecter HTA gravidique (150 ≥ 140)
        hta_alerts = [a for a in body["data"]["alerts"] if a["type"] == "HYPERTENSION_GRAVIDIQUE"]
        assert len(hta_alerts) >= 1
        assert body["data"]["high_count"] >= 1

    def test_alerts_detects_severe_hypertension(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        record = MaternityRecord(
            facility_id="facility-A",
            patient_id=patient.id,
            last_menstrual_period=date(2026, 1, 1),
            expected_due_date=date(2026, 10, 8),
            gravidity=2,
            parity=1,
            risk_level="LOW",
            status="ACTIVE",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # HTA sévère 170/115
        consult = MaternityConsultation(
            facility_id="facility-A",
            record_id=record.id,
            consultation_type="PRENATAL",
            blood_pressure="170/115",
            weight_kg=70,
        )
        db.add(consult)
        db.commit()

        resp = client.get(
            "/api/v1/maternity/alerts",
            headers=_headers_for(admin),
        )
        body = resp.json()
        severe = [a for a in body["data"]["alerts"] if a["type"] == "HYPERTENSION_SEVERE"]
        assert len(severe) >= 1
        assert body["data"]["critical_count"] >= 1

    def test_alerts_detects_low_weight(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        record = MaternityRecord(
            facility_id="facility-A",
            patient_id=patient.id,
            last_menstrual_period=date(2026, 1, 1),
            expected_due_date=date(2026, 10, 8),
            gravidity=1,
            parity=0,
            risk_level="LOW",
            status="ACTIVE",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        consult = MaternityConsultation(
            facility_id="facility-A",
            record_id=record.id,
            consultation_type="PRENATAL",
            blood_pressure="110/70",
            weight_kg=42,  # < 45 kg
        )
        db.add(consult)
        db.commit()

        resp = client.get(
            "/api/v1/maternity/alerts",
            headers=_headers_for(admin),
        )
        body = resp.json()
        low_weight = [a for a in body["data"]["alerts"] if a["type"] == "LOW_WEIGHT"]
        assert len(low_weight) >= 1

    def test_alerts_no_false_positive_normal_bp(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        record = MaternityRecord(
            facility_id="facility-A",
            patient_id=patient.id,
            last_menstrual_period=date(2026, 1, 1),
            expected_due_date=date(2026, 10, 8),
            gravidity=1,
            parity=0,
            risk_level="LOW",
            status="ACTIVE",
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        # PA normale 118/76, poids normal 68 kg
        consult = MaternityConsultation(
            facility_id="facility-A",
            record_id=record.id,
            consultation_type="PRENATAL",
            blood_pressure="118/76",
            weight_kg=68,
        )
        db.add(consult)
        db.commit()

        resp = client.get(
            "/api/v1/maternity/alerts",
            headers=_headers_for(admin),
        )
        body = resp.json()
        # Aucune alerte ne doit être levée pour des valeurs normales
        # (mais d'autres consultations d'autres tests peuvent générer des alertes)
        # On vérifie juste qu'aucune alerte de type HTA ou LOW_WEIGHT n'est pour cette consultation
        alerts_for_this = [a for a in body["data"]["alerts"] if a.get("consultation_id") == str(consult.id)]
        assert len(alerts_for_this) == 0, (
            f"Pas d'alerte attendue pour PA normale 118/76, poids 68kg — got {alerts_for_this}"
        )
