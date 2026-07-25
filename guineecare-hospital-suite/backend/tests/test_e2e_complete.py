"""Test E2E complet — GuinéeCare Hospital Suite v2.7.0.

Parcours bout-en-bout : login → patient → admission → consultation →
prescription → labo → pharmacie → facturation → sortie → historique →
reporting national → PDF.

Ce test simule le parcours réel d'un patient dans un hôpital guinéen.
Il utilise le client TestClient de FastAPI (pas de serveur externe requis).

Usage :
    cd backend
    source .venv/bin/activate
    python -m pytest tests/test_e2e_complete.py -v
"""
from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.core.security import create_access_token, hash_password
from app.modules.admissions.models import Admission
from app.modules.billing.models import Invoice
from app.modules.clinical.models import ClinicalNote, Prescription
from app.modules.facilities.models import Facility
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.patients.models import Patient
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock
from app.modules.users.models import User


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_user(db, role="SUPER_ADMIN", facility_id=None):
    suffix = uuid4().hex[:6]
    user = User(
        email=f"e2e-{role}-{suffix}@test.com",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="E2E",
        last_name=role.title(),
        role=role,
        facility_id=facility_id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_facility(db, code=None, name=None):
    f = Facility(
        code=code or f"E2E-{uuid4().hex[:6]}",
        name=name or f"E2E Facility {uuid4().hex[:4]}",
        category="CHU",
        region="Conakry",
        prefecture="Conakry",
        commune="Kaloum",
        status="ACTIVE",
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _make_patient(db, facility_id, **overrides):
    suffix = uuid4().hex[:8]
    defaults = {
        "facility_id": facility_id,
        "patient_number": f"E2E-PAT-{suffix}",
        "first_name": "Aminata",
        "last_name": "Diallo",
        "gender": "F",
        "date_of_birth": date(1995, 3, 15),
        "phone": "+224622334455",
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


# ── Test E2E : Parcours patient complet ─────────────────────────────────────

class TestE2EPatientJourney:
    """Parcours patient bout-en-bout : de l'arrivée à la sortie avec documents.

    Scénario : Mme Aminata Diallo arrive aux urgences du CHU Donka avec
    fièvre et douleurs abdominales. Elle est admise, consultée, reçoit une
    prescription, passe au laboratoire, à la pharmacie, paie, puis sort.
    """

    def test_complete_patient_journey(self, client, db):
        """Test intégral du parcours patient — 15 étapes."""
        # ── Setup : facility + users ──
        facility = _make_facility(db, code="E2E-CHU", name="CHU E2E Test")
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)

        # ── Étape 1 : Login ──
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": admin.email, "password": "TestPassword1!xx"},
        )
        assert resp.status_code == 200, f"Login failed: {resp.text}"
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # ── Étape 2 : Création patient ──
        resp = client.post(
            "/api/v1/patients",
            json={
                "facility_id": str(facility.id),
                "first_name": "Aminata",
                "last_name": "Diallo",
                "gender": "F",
                "date_of_birth": "1995-03-15",
                "phone": "+224622334455",
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Patient creation failed: {resp.text}"
        patient_id = resp.json()["data"]["id"]
        patient_number = resp.json()["data"]["patient_number"]

        # ── Étape 3 : Recherche patient ──
        resp = client.get(
            f"/api/v1/patients?search=Aminata",
            headers=headers,
        )
        assert resp.status_code == 200
        assert any(p["id"] == patient_id for p in resp.json().get("data", []))

        # ── Étape 4 : Fiche patient ──
        resp = client.get(
            f"/api/v1/patients/{patient_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["first_name"] == "Aminata"

        # ── Étape 5 : Admission ──
        resp = client.post(
            "/api/v1/admissions",
            json={
                "facility_id": str(facility.id),
                "patient_id": patient_id,
                "admission_type": "EMERGENCY",
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Admission failed: {resp.text}"
        admission_id = resp.json()["data"]["id"]

        # ── Étape 6 : Consultation (clinical note) ──
        resp = client.post(
            f"/api/v1/clinical/patients/{patient_id}/notes",
            json={
                "note_type": "CONSULTATION",
                "content": "Patient présente fièvre 38.5°C, douleurs abdominales FID. Suspicione appendicite.",
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Consultation failed: {resp.text}"
        consultation_id = resp.json()["data"]["id"]

        # ── Étape 7 : Prescription structurée ──
        resp = client.post(
            "/api/v1/clinical/prescriptions",
            json={
                "patient_id": patient_id,
                "admission_id": admission_id,
                "clinical_note_id": consultation_id,
                "medication_name": "Paracétamol",
                "dosage": "500mg",
                "frequency": "3 fois par jour",
                "duration": "7 jours",
                "quantity": 21,
                "instructions": "À prendre avec un grand verre d'eau",
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Prescription failed: {resp.text}"
        prescription_id = resp.json()["data"]["id"]

        # ── Étape 8 : Demande laboratoire ──
        lab_test = LabTest(
            facility_id=str(facility.id),
            code=f"E2E-LAB-{uuid4().hex[:6]}",
            name="NFS",
            sample_type="BLOOD",
        )
        db.add(lab_test)
        db.commit()
        db.refresh(lab_test)

        resp = client.post(
            "/api/v1/laboratory/orders",
            json={
                "patient_id": patient_id,
                "test_id": str(lab_test.id),
                "priority": "URGENT",
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Lab order failed: {resp.text}"
        lab_order_id = resp.json()["data"]["id"]

        # ── Étape 9 : Prélèvement labo ──
        resp = client.post(
            f"/api/v1/laboratory/orders/{lab_order_id}/collect",
            json={"sample_id": "E2E-SAM-001"},
            headers=headers,
        )
        assert resp.status_code == 200, f"Sample collection failed: {resp.text}"
        assert resp.json()["data"]["status"] == "SAMPLE_COLLECTED"

        # ── Étape 10 : Saisie résultat labo ──
        resp = client.post(
            f"/api/v1/laboratory/orders/{lab_order_id}/results",
            json={"result_value": "Leucocytes 12.5 G/L", "interpretation": "Leucocytose élevée"},
            headers=headers,
        )
        assert resp.status_code == 200, f"Lab result failed: {resp.text}"

        # ── Étape 11 : Dispensation pharmacie ──
        product = PharmacyProduct(
            facility_id=str(facility.id),
            code=f"E2E-MED-{uuid4().hex[:6]}",
            name="Paracétamol 500mg",
            unit_price=500,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        stock = PharmacyStock(
            facility_id=str(facility.id),
            product_id=product.id,
            quantity_available=100,
            min_threshold=10,
        )
        db.add(stock)
        db.commit()

        resp = client.post(
            "/api/v1/pharmacy/dispense",
            json={
                "product_id": str(product.id),
                "quantity": 21,
                "patient_id": patient_id,
                "prescription_id": prescription_id,
                "admission_id": admission_id,
                "reason": "Selon prescription",
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Dispensation failed: {resp.text}"
        assert resp.json()["data"]["remaining_stock"] == 79  # 100 - 21

        # ── Étape 12 : Facturation ──
        resp = client.post(
            "/api/v1/billing/invoices",
            json={
                "patient_id": patient_id,
                "admission_id": admission_id,
                "description": "Consultation urgences + bilan bio + médicaments",
                "net_amount": 150000,
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Invoice creation failed: {resp.text}"
        invoice_id = resp.json()["data"]["id"]

        # ── Étape 13 : Paiement partiel ──
        resp = client.post(
            f"/api/v1/billing/invoices/{invoice_id}/payments",
            json={
                "amount": 80000,
                "payment_method": "CASH",
            },
            headers=headers,
        )
        assert resp.status_code == 200, f"Payment failed: {resp.text}"
        payment_id = resp.json()["data"]["payment"]["id"]
        assert resp.json()["data"]["invoice"]["status"] == "PARTIALLY_PAID"

        # ── Étape 14 : Clôture admission ──
        resp = client.post(
            f"/api/v1/admissions/{admission_id}/close",
            headers=headers,
        )
        assert resp.status_code == 200, f"Admission close failed: {resp.text}"
        assert resp.json()["data"]["status"] == "CLOSED"

        # ── Étape 15 : Historique patient ──
        resp = client.get(
            f"/api/v1/patients/{patient_id}/history",
            headers=headers,
        )
        assert resp.status_code == 200, f"History failed: {resp.text}"
        events = resp.json()["events"]
        event_types = [e["type"] for e in events]
        assert "admission" in event_types
        assert "clinical_note" in event_types
        assert "lab_order" in event_types
        assert "invoice" in event_types


class TestE2EDashboards:
    """Test tous les dashboards métier."""

    def test_billing_dashboard(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-BILL")
        patient = _make_patient(db, facility.id)

        inv = Invoice(
            facility_id=facility.id,
            patient_id=patient.id,
            invoice_number=f"E2E-INV-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=30000,
            balance_due=20000,
            status="PARTIALLY_PAID",
        )
        db.add(inv)
        db.commit()

        resp = client.get(
            "/api/v1/billing/dashboard",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["outstanding_total"] >= 20000

    def test_lab_stats(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-LAB")
        patient = _make_patient(db, facility.id)
        lab_test = LabTest(facility_id=facility.id, code=f"LT-{uuid4().hex[:6]}", name="CRP")
        db.add(lab_test)
        db.commit()
        db.refresh(lab_test)

        for status in ["ORDERED", "VALIDATED", "VALIDATED"]:
            db.add(LabOrder(
                facility_id=facility.id,
                patient_id=patient.id,
                test_id=lab_test.id,
                status=status,
            ))
        db.commit()

        resp = client.get(
            "/api/v1/laboratory/stats",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total_orders"] >= 3

    def test_emergency_indicators(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-EMG")
        patient = _make_patient(db, facility.id)

        from app.modules.emergency.models import EmergencyVisit
        for status in ["WAITING", "TRIAGED", "DISCHARGED"]:
            db.add(EmergencyVisit(
                facility_id=facility.id,
                patient_id=patient.id,
                priority_level="NORMAL",
                status=status,
            ))
        db.commit()

        resp = client.get(
            "/api/v1/emergency/indicators",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["total_today"] >= 3

    def test_pharmacy_alerts(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-PHA")
        product = PharmacyProduct(
            facility_id=facility.id,
            code=f"PA-{uuid4().hex[:6]}",
            name="Ibuprofène",
            unit_price=800,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Stock en rupture
        db.add(PharmacyStock(
            facility_id=facility.id,
            product_id=product.id,
            quantity_available=2,
            min_threshold=10,
        ))
        db.commit()

        resp = client.get(
            "/api/v1/pharmacy/alerts",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["low_stock_count"] >= 1

    def test_national_dashboard(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        f1 = _make_facility(db, code="E2E-NAT-1", name="CHU National 1")
        f2 = _make_facility(db, code="E2E-NAT-2", name="CHU National 2")
        _make_patient(db, f1.id)
        _make_patient(db, f2.id)

        resp = client.get(
            "/api/v1/reporting/national",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["facilities_count"] >= 2
        assert resp.json()["indicators"]["total_patients"] >= 2

    def test_national_excel_export(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        f1 = _make_facility(db, code="E2E-XLSX")
        _make_patient(db, f1.id)

        resp = client.get(
            "/api/v1/reporting/export/xlsx",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.content[:2] == b"PK"  # ZIP magic (xlsx)


class TestE2EPDFGeneration:
    """Test génération PDF de tous les documents."""

    def test_prescription_pdf(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-PDF-RX")
        patient = _make_patient(db, facility.id)
        note = ClinicalNote(
            facility_id=facility.id,
            patient_id=patient.id,
            note_type="PRESCRIPTION",
            content="Paracétamol 1g x3/jour",
        )
        db.add(note)
        db.commit()
        db.refresh(note)

        resp = client.get(
            f"/api/v1/documents/prescriptions/{note.id}/pdf",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:4] == b"%PDF"

    def test_invoice_pdf(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-PDF-INV")
        patient = _make_patient(db, facility.id)
        inv = Invoice(
            facility_id=facility.id,
            patient_id=patient.id,
            invoice_number=f"E2E-PDF-INV-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=50000,
            balance_due=0,
            status="PAID",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        resp = client.get(
            f"/api/v1/documents/invoices/{inv.id}/pdf",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"

    def test_payment_receipt_pdf(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-PDF-REC")
        patient = _make_patient(db, facility.id)
        inv = Invoice(
            facility_id=facility.id,
            patient_id=patient.id,
            invoice_number=f"E2E-PDF-REC-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=50000,
            balance_due=0,
            status="PAID",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        from app.modules.billing.models import Payment
        pay = Payment(
            facility_id=facility.id,
            invoice_id=inv.id,
            amount=50000,
            payment_method="CASH",
            status="COMPLETED",
        )
        db.add(pay)
        db.commit()
        db.refresh(pay)

        resp = client.get(
            f"/api/v1/documents/payments/{pay.id}/pdf",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.content[:4] == b"%PDF"


class TestE2ESecurity:
    """Test sécurité : multi-tenant, RBAC, audit."""

    def test_cross_tenant_patient_access_blocked(self, client, db):
        """Un DOCTOR de facility A ne peut pas lire un patient de facility B."""
        f_a = _make_facility(db, code="E2E-SEC-A")
        f_b = _make_facility(db, code="E2E-SEC-B")
        doctor_a = _make_user(db, role="DOCTOR", facility_id=f_a.id)
        patient_b = _make_patient(db, f_b.id)

        resp = client.get(
            f"/api/v1/patients/{patient_b.id}",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 403

    def test_cashier_cannot_access_clinical(self, client, db):
        """CASHIER n'a pas la permission clinical.read."""
        f = _make_facility(db, code="E2E-SEC-CASH")
        cashier = _make_user(db, role="CASHIER", facility_id=f.id)
        patient = _make_patient(db, f.id)

        resp = client.get(
            f"/api/v1/clinical/patients/{patient.id}/notes",
            headers=_headers_for(cashier),
        )
        assert resp.status_code == 403

    def test_no_token_returns_401(self, client, db):
        """Pas de token → 401."""
        resp = client.get("/api/v1/patients")
        assert resp.status_code == 401

    def test_patient_access_audit_logged(self, client, db):
        """GET /patients/{id} doit créer une entrée audit_logs."""
        from app.modules.auth.models import AuditLog

        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-SEC-AUDIT")
        patient = _make_patient(db, facility.id)

        client.get(
            f"/api/v1/patients/{patient.id}",
            headers=_headers_for(admin),
        )
        entries = db.query(AuditLog).filter(
            AuditLog.action == "patient.read",
            AuditLog.resource_id == str(patient.id),
        ).all()
        assert len(entries) >= 1

    def test_invoice_cancel_with_reason(self, client, db):
        """Annulation facture nécessite une raison ≥ 5 caractères."""
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-SEC-CANCEL")
        patient = _make_patient(db, facility.id)
        inv = Invoice(
            facility_id=facility.id,
            patient_id=patient.id,
            invoice_number=f"E2E-CANCEL-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=0,
            balance_due=50000,
            status="ISSUED",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        # Raison trop courte → 422
        resp = client.post(
            f"/api/v1/billing/invoices/{inv.id}/cancel",
            json={"reason": "ok"},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 422

        # Raison valide → 200
        resp = client.post(
            f"/api/v1/billing/invoices/{inv.id}/cancel",
            json={"reason": "Facture dupliquée — erreur de saisie"},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "CANCELLED"

    def test_paid_invoice_cannot_be_cancelled(self, client, db):
        """Facture payée ne peut pas être annulée → 409."""
        admin = _make_user(db, role="SUPER_ADMIN")
        facility = _make_facility(db, code="E2E-SEC-PAID")
        patient = _make_patient(db, facility.id)
        inv = Invoice(
            facility_id=facility.id,
            patient_id=patient.id,
            invoice_number=f"E2E-PAID-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=50000,
            balance_due=0,
            status="PAID",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        resp = client.post(
            f"/api/v1/billing/invoices/{inv.id}/cancel",
            json={"reason": "Test annulation facture payée"},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 409
