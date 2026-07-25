"""Tests Phase 4 — parcours métiers hospitaliers (v2.4.0).

Couvre les nouveaux endpoints ajoutés en Phase 4 :
- GET /patients/{id}/history (timeline agrégée)
- POST /pharmacy/dispense (dispensation liée patient)
- GET /pharmacy/alerts (ruptures + péremptions)
- GET /pharmacy/valuation (valorisation stock GNF)
- GET /billing/dashboard (tableau de bord caisse)
- POST /billing/invoices/{id}/cancel (annulation contrôlée)
- GET /laboratory/stats (statut demandes)
- POST /laboratory/orders/{id}/collect (prélèvement)
- GET /emergency/indicators (temps d'attente)
- POST /emergency/visits/{id}/hospitalize (transfert hospitalisation)
- GET /documents/payments/{id}/pdf (reçu PDF)
"""
from __future__ import annotations

from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.core.security import create_access_token, hash_password
from app.core.datetime import utcnow
from app.modules.admissions.models import Admission
from app.modules.billing.models import Invoice, Payment, TariffItem
from app.modules.clinical.models import ClinicalNote
from app.modules.emergency.models import EmergencyVisit
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.patients.models import Patient
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement
from app.modules.users.models import User


# ── Helpers ─────────────────────────────────────────────────────────────────

def _make_user(db, role="DOCTOR", facility_id="facility-A"):
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
        gender="M",
        date_of_birth=date(1990, 1, 1),
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


# ── GET /patients/{id}/history ─────────────────────────────────────────────

class TestPatientHistory:
    def test_history_returns_aggregated_events(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        # Créer une admission + une note clinique + une facture
        adm = Admission(
            facility_id="facility-A",
            patient_id=patient.id,
            admission_type="CONSULTATION",
            status="ACTIVE",
            admitted_at=utcnow(),
        )
        db.add(adm)
        db.flush()

        note = ClinicalNote(
            facility_id="facility-A",
            patient_id=patient.id,
            admission_id=adm.id,
            note_type="CONSULTATION",
            content="Patient présente fièvre 38.5°C",
        )
        db.add(note)

        invoice = Invoice(
            facility_id="facility-A",
            patient_id=patient.id,
            admission_id=adm.id,
            invoice_number=f"INV-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=0,
            balance_due=50000,
            status="ISSUED",
        )
        db.add(invoice)
        db.commit()

        resp = client.get(
            f"/api/v1/patients/{patient.id}/history",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["patient_id"] == str(patient.id)
        assert body["data"]["total_events"] >= 3
        types = [e["type"] for e in body["events"]]
        assert "admission" in types
        assert "clinical_note" in types
        assert "invoice" in types

    def test_history_cross_facility_forbidden(self, client, db):
        doctor_a = _make_user(db, role="DOCTOR", facility_id="facility-A")
        patient_b = _make_patient(db, facility_id="facility-B")

        resp = client.get(
            f"/api/v1/patients/{patient_b.id}/history",
            headers=_headers_for(doctor_a),
        )
        assert resp.status_code == 403

    def test_history_creates_audit_log(self, client, db):
        from app.modules.auth.models import AuditLog

        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        client.get(
            f"/api/v1/patients/{patient.id}/history",
            headers=_headers_for(admin),
        )
        entries = (
            db.query(AuditLog)
            .filter(AuditLog.action == "patient.history.read")
            .filter(AuditLog.resource_id == str(patient.id))
            .all()
        )
        assert len(entries) >= 1


# ── POST /pharmacy/dispense ────────────────────────────────────────────────

class TestPharmacyDispense:
    def test_dispense_to_patient_success(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        product = PharmacyProduct(
            facility_id="facility-A",
            code=f"MED-{uuid4().hex[:6]}",
            name="Paracétamol 500mg",
            unit_price=500,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        stock = PharmacyStock(
            facility_id="facility-A",
            product_id=product.id,
            quantity_available=100,
            min_threshold=10,
        )
        db.add(stock)
        db.commit()

        resp = client.post(
            "/api/v1/pharmacy/dispense",
            json={
                "product_id": product.id,
                "quantity": 10,
                "patient_id": patient.id,
                "reason": "Traitement fièvre",
            },
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["quantity_dispensed"] == 10
        assert body["data"]["patient_id"] == str(patient.id)
        assert body["data"]["remaining_stock"] == 90

        # Vérifier que le StockMovement a le patient_id
        mvts = db.query(StockMovement).filter(
            StockMovement.patient_id == patient.id
        ).all()
        assert len(mvts) == 1
        assert mvts[0].movement_type == "OUT"

    def test_dispense_insufficient_stock(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        product = PharmacyProduct(
            facility_id="facility-A",
            code=f"MED-{uuid4().hex[:6]}",
            name="Amoxicilline",
            unit_price=1500,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        stock = PharmacyStock(
            facility_id="facility-A",
            product_id=product.id,
            quantity_available=5,
            min_threshold=10,
        )
        db.add(stock)
        db.commit()

        resp = client.post(
            "/api/v1/pharmacy/dispense",
            json={
                "product_id": product.id,
                "quantity": 10,
                "patient_id": patient.id,
            },
            headers=_headers_for(admin),
        )
        assert resp.status_code == 409

    def test_dispense_missing_fields(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        resp = client.post(
            "/api/v1/pharmacy/dispense",
            json={"product_id": "x", "quantity": 1},  # missing patient_id
            headers=_headers_for(admin),
        )
        assert resp.status_code == 422


# ── GET /pharmacy/alerts ───────────────────────────────────────────────────

class TestPharmacyAlerts:
    def test_alerts_returns_low_stock(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)

        product = PharmacyProduct(
            facility_id="facility-A",
            code=f"MED-{uuid4().hex[:6]}",
            name="Ibuprofène",
            unit_price=800,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Stock en rupture
        stock = PharmacyStock(
            facility_id="facility-A",
            product_id=product.id,
            quantity_available=2,  # < min_threshold
            min_threshold=10,
        )
        db.add(stock)
        db.commit()

        resp = client.get(
            "/api/v1/pharmacy/alerts",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["low_stock_count"] >= 1
        assert any(p["product_name"] == "Ibuprofène" for p in body["data"]["low_stock"])

    def test_alerts_returns_near_expiry(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)

        product = PharmacyProduct(
            facility_id="facility-A",
            code=f"MED-{uuid4().hex[:6]}",
            name="Métronidazole",
            unit_price=1200,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Stock expirant dans 15 jours (< 30j = near_expiry)
        soon = utcnow() + timedelta(days=15)
        stock = PharmacyStock(
            facility_id="facility-A",
            product_id=product.id,
            quantity_available=50,
            min_threshold=5,
            batch_number="LOT-2024-001",
            expiry_date=soon,
        )
        db.add(stock)
        db.commit()

        resp = client.get(
            "/api/v1/pharmacy/alerts",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["near_expiry_count"] >= 1


# ── GET /pharmacy/valuation ────────────────────────────────────────────────

class TestPharmacyValuation:
    def test_valuation_total(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)

        # 2 produits avec stock
        for qty, price in [(100, 500), (50, 1500)]:
            p = PharmacyProduct(
                facility_id="facility-A",
                code=f"MED-{uuid4().hex[:6]}",
                name=f"Med-{qty}-{price}",
                unit_price=price,
            )
            db.add(p)
            db.commit()
            db.refresh(p)
            db.add(PharmacyStock(
                facility_id="facility-A",
                product_id=p.id,
                quantity_available=qty,
                min_threshold=0,
            ))
            db.commit()

        resp = client.get(
            "/api/v1/pharmacy/valuation",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        # Total = 100*500 + 50*1500 = 50000 + 75000 = 125000
        # (les tests précédents ont pu ajouter d'autres produits)
        assert body["data"]["total_stock_value_gnf"] >= 125000
        assert body["data"]["currency"] == "GNF"


# ── GET /billing/dashboard ─────────────────────────────────────────────────

class TestBillingDashboard:
    def test_dashboard_returns_kpis(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        # Créer facture + paiement aujourd'hui
        inv = Invoice(
            facility_id="facility-A",
            patient_id=patient.id,
            invoice_number=f"INV-{uuid4().hex[:8]}",
            net_amount=100000,
            paid_amount=50000,
            balance_due=50000,
            status="PARTIALLY_PAID",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        pay = Payment(
            facility_id="facility-A",
            invoice_id=inv.id,
            amount=50000,
            payment_method="CASH",
            status="COMPLETED",
            received_at=utcnow(),
        )
        db.add(pay)
        db.commit()

        resp = client.get(
            "/api/v1/billing/dashboard",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["revenue_today"] >= 50000
        assert body["data"]["outstanding_total"] >= 50000
        assert "PARTIALLY_PAID" in body["data"]["invoices_count_by_status"]
        assert body["data"]["payments_count_today"] >= 1


# ── POST /billing/invoices/{id}/cancel ─────────────────────────────────────

class TestInvoiceCancel:
    def test_cancel_unpaid_invoice(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")
        inv = Invoice(
            facility_id="facility-A",
            patient_id=patient.id,
            invoice_number=f"INV-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=0,
            balance_due=50000,
            status="ISSUED",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        resp = client.post(
            f"/api/v1/billing/invoices/{inv.id}/cancel",
            json={"reason": "Erreur de saisie — facture dupliquée"},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["status"] == "CANCELLED"
        assert body["data"]["cancellation_reason"] is not None

    def test_cancel_paid_invoice_forbidden(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")
        inv = Invoice(
            facility_id="facility-A",
            patient_id=patient.id,
            invoice_number=f"INV-{uuid4().hex[:8]}",
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
            json={"reason": "Annulation test"},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 409

    def test_cancel_short_reason_rejected(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")
        inv = Invoice(
            facility_id="facility-A",
            patient_id=patient.id,
            invoice_number=f"INV-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=0,
            balance_due=50000,
            status="ISSUED",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        resp = client.post(
            f"/api/v1/billing/invoices/{inv.id}/cancel",
            json={"reason": "ok"},  # trop court (< 5 chars)
            headers=_headers_for(admin),
        )
        assert resp.status_code == 422


# ── GET /laboratory/stats ──────────────────────────────────────────────────

class TestLabStats:
    def test_stats_returns_status_counts(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")
        lab_test = LabTest(
            facility_id="facility-A",
            code=f"LAB-{uuid4().hex[:6]}",
            name="Glycémie",
            sample_type="BLOOD",
        )
        db.add(lab_test)
        db.commit()
        db.refresh(lab_test)

        # Créer 3 commandes : 2 ORDERED + 1 VALIDATED
        for _ in range(2):
            db.add(LabOrder(
                facility_id="facility-A",
                patient_id=patient.id,
                test_id=lab_test.id,
                status="ORDERED",
                priority="NORMAL",
            ))
        db.add(LabOrder(
            facility_id="facility-A",
            patient_id=patient.id,
            test_id=lab_test.id,
            status="VALIDATED",
            priority="URGENT",
        ))
        db.commit()

        resp = client.get(
            "/api/v1/laboratory/stats",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["count_by_status"].get("ORDERED", 0) >= 2
        assert body["data"]["count_by_status"].get("VALIDATED", 0) >= 1
        assert body["data"]["total_orders"] >= 3


# ── POST /laboratory/orders/{id}/collect ───────────────────────────────────

class TestLabSampleCollection:
    def test_collect_sample_changes_status(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")
        lab_test = LabTest(
            facility_id="facility-A",
            code=f"LAB-{uuid4().hex[:6]}",
            name="NFS",
            sample_type="BLOOD",
        )
        db.add(lab_test)
        db.commit()
        db.refresh(lab_test)

        order = LabOrder(
            facility_id="facility-A",
            patient_id=patient.id,
            test_id=lab_test.id,
            status="ORDERED",
            priority="NORMAL",
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        resp = client.post(
            f"/api/v1/laboratory/orders/{order.id}/collect",
            json={"sample_id": "SAM-2026-001"},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["status"] == "SAMPLE_COLLECTED"
        assert body["data"]["sample_id"] == "SAM-2026-001"

    def test_collect_already_collected_returns_409(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")
        lab_test = LabTest(
            facility_id="facility-A",
            code=f"LAB-{uuid4().hex[:6]}",
            name="CRP",
            sample_type="BLOOD",
        )
        db.add(lab_test)
        db.commit()
        db.refresh(lab_test)

        order = LabOrder(
            facility_id="facility-A",
            patient_id=patient.id,
            test_id=lab_test.id,
            status="SAMPLE_COLLECTED",
            priority="NORMAL",
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        resp = client.post(
            f"/api/v1/laboratory/orders/{order.id}/collect",
            json={},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 409


# ── GET /emergency/indicators ──────────────────────────────────────────────

class TestEmergencyIndicators:
    def test_indicators_returns_kpis(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        # Créer 3 visites aujourd'hui
        for status in ("WAITING", "TRIAGED", "DISCHARGED"):
            visit = EmergencyVisit(
                facility_id="facility-A",
                patient_id=patient.id,
                priority_level="NORMAL",
                status=status,
                arrived_at=utcnow(),
            )
            if status == "DISCHARGED":
                visit.seen_at = utcnow()
                visit.discharged_at = utcnow()
            db.add(visit)
        db.commit()

        resp = client.get(
            "/api/v1/emergency/indicators",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total_today"] >= 3
        assert "count_by_status" in body["data"]
        assert "avg_time_to_care_min" in body["data"]


# ── POST /emergency/visits/{id}/hospitalize ────────────────────────────────

class TestEmergencyHospitalize:
    def test_hospitalize_creates_admission(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        visit = EmergencyVisit(
            facility_id="facility-A",
            patient_id=patient.id,
            priority_level="URGENT",
            status="IN_CARE",
            arrived_at=utcnow(),
            seen_at=utcnow(),
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)

        resp = client.post(
            f"/api/v1/emergency/visits/{visit.id}/hospitalize",
            json={"reason": "Surveillance post-urgences"},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["data"]["visit_status"] == "DISCHARGED"
        assert body["data"]["admission_id"] is not None
        assert body["data"]["admission_type"] == "HOSPITALIZATION"

        # Vérifier que l'admission a été créée
        adm = db.query(Admission).filter(
            Admission.id == body["data"]["admission_id"]
        ).first()
        assert adm is not None
        assert adm.admission_type == "HOSPITALIZATION"
        assert adm.status == "ACTIVE"

    def test_hospitalize_wrong_status_returns_409(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        visit = EmergencyVisit(
            facility_id="facility-A",
            patient_id=patient.id,
            priority_level="NORMAL",
            status="WAITING",  # pas encore IN_CARE
            arrived_at=utcnow(),
        )
        db.add(visit)
        db.commit()
        db.refresh(visit)

        resp = client.post(
            f"/api/v1/emergency/visits/{visit.id}/hospitalize",
            json={"reason": "Test"},
            headers=_headers_for(admin),
        )
        assert resp.status_code == 409


# ── GET /documents/payments/{id}/pdf ───────────────────────────────────────

class TestPaymentReceiptPDF:
    def test_pdf_receipt_generated(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        patient = _make_patient(db, facility_id="facility-A")

        inv = Invoice(
            facility_id="facility-A",
            patient_id=patient.id,
            invoice_number=f"INV-{uuid4().hex[:8]}",
            net_amount=50000,
            paid_amount=50000,
            balance_due=0,
            status="PAID",
        )
        db.add(inv)
        db.commit()
        db.refresh(inv)

        pay = Payment(
            facility_id="facility-A",
            invoice_id=inv.id,
            amount=50000,
            payment_method="CASH",
            status="COMPLETED",
            received_at=utcnow(),
        )
        db.add(pay)
        db.commit()
        db.refresh(pay)

        resp = client.get(
            f"/api/v1/documents/payments/{pay.id}/pdf",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        # Le PDF doit commencer par %PDF
        assert resp.content[:4] == b"%PDF"
        # Le header Content-Disposition doit mentionner le reçu
        assert "REC-" in resp.headers.get("content-disposition", "")
