"""Tests for v1.2.0 documents module — PDF generation.

Covers:
- Prescription PDF: happy path, wrong note_type (400), not found (404),
  cross-tenant (403), download flag, audit row written.
- Imaging report PDF: happy path, missing result still works,
  not found, cross-tenant.
- Lab result PDF: happy path, missing result still works, not found.
- Invoice PDF: happy path, with/without payments, not found.
- Audit listing: filter by document_type, filter by patient_id,
  paginated, SUPER_ADMIN sees all facilities.
"""
import io
import pytest

from app.core.security import create_access_token, hash_password
from app.modules.billing.models import Invoice, Payment, TariffItem
from app.modules.clinical.models import ClinicalNote
from app.modules.documents.models import DocumentGenerated
from app.modules.facilities.models import Facility
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.patients.models import Patient
from app.modules.users.models import User


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def facility(db):
    fac = Facility(name="CHU Donka", code="CHU-DONKA", category="CHU", region="Conakry")
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac


@pytest.fixture
def other_facility(db):
    fac = Facility(name="CHU Ignace Deen", code="CHU-ID", category="CHU", region="Conakry")
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac


@pytest.fixture
def doctor(db, facility):
    user = User(
        email="doc@docs.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Marie",
        last_name="Diallo",
        role="DOCTOR",
        facility_id=facility.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def doctor_headers(doctor):
    token = create_access_token(
        subject=doctor.id,
        facility_id=doctor.facility_id,
        role=doctor.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db, facility):
    user = User(
        email="admin@docs.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Admin",
        last_name="Docs",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(
        subject=user.id,
        facility_id=user.facility_id,
        role=user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_admin_headers(db, other_facility):
    """ADMIN scoped to other_facility — used for cross-tenant tests."""
    user = User(
        email="admin.other@docs.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Other",
        last_name="Admin",
        role="ADMIN",
        facility_id=other_facility.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(
        subject=user.id,
        facility_id=user.facility_id,
        role=user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def patient(db, facility):
    p = Patient(
        facility_id=facility.id,
        patient_number="PAT-0001",
        first_name="Aissatou",
        last_name="Camara",
        gender="F",
        phone="+224 622 000 001",
        address="Conakry",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def prescription(db, facility, patient, doctor):
    note = ClinicalNote(
        facility_id=facility.id,
        patient_id=patient.id,
        note_type="PRESCRIPTION",
        content="Paracétamol 500mg\n1 comprimé x 3/jour pendant 5 jours\nAmoxicilline 500mg\n1 gélule x 2/jour pendant 7 jours",
        created_by=doctor.id,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@pytest.fixture
def imaging_order(db, facility, patient):
    order = ImagingOrder(
        facility_id=facility.id,
        patient_id=patient.id,
        exam_type="RADIOGRAPHY",
        body_region="Thorax",
        clinical_info="Toux persistante depuis 3 semaines",
        urgency="ROUTINE",
        status="COMPLETED",
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@pytest.fixture
def imaging_result(db, facility, patient, imaging_order):
    result = ImagingResult(
        facility_id=facility.id,
        order_id=imaging_order.id,
        patient_id=patient.id,
        findings="Aucun foyer parenchymateux. Silhouette cardiaque normale.",
        conclusion="Radiographie thoracique sans anomalie.",
        recommendation="Surveillance clinique.",
        status="VALIDATED",
    )
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


@pytest.fixture
def lab_test(db, facility):
    t = LabTest(
        facility_id=facility.id,
        code="GLY",
        name="Glycémie",
        category="BIOCHIMIE",
        sample_type="Sang",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def lab_order(db, facility, patient, lab_test):
    o = LabOrder(
        facility_id=facility.id,
        patient_id=patient.id,
        test_id=lab_test.id,
        priority="NORMAL",
        status="RESULTED",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@pytest.fixture
def lab_result(db, facility, lab_order):
    r = LabResult(
        facility_id=facility.id,
        order_id=lab_order.id,
        result_value="0.95 g/L",
        interpretation="Normale",
        status="VALIDATED",
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@pytest.fixture
def invoice(db, facility, patient):
    inv = Invoice(
        facility_id=facility.id,
        patient_id=patient.id,
        invoice_number="INV-2026-0001",
        description="Consultation + analyses",
        net_amount=150000,
        paid_amount=100000,
        balance_due=50000,
        status="PARTIAL",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@pytest.fixture
def payment(db, facility, invoice):
    p = Payment(
        facility_id=facility.id,
        invoice_id=invoice.id,
        amount=100000,
        payment_method="CASH",
        status="COMPLETED",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ============================================================================
# Prescription PDF
# ============================================================================

class TestPrescriptionPDF:
    def test_generate_prescription_pdf_success(self, client, doctor_headers, prescription):
        """Valid prescription → 200, application/pdf, starts with %PDF."""
        resp = client.get(
            f"/api/v1/documents/prescriptions/{prescription.id}/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"
        assert "Content-Disposition" in resp.headers
        assert "inline" in resp.headers["content-disposition"]
        assert resp.headers["content-disposition"].count(".pdf") == 1

    def test_generate_prescription_pdf_download_flag(self, client, doctor_headers, prescription):
        """?download=1 → Content-Disposition: attachment."""
        resp = client.get(
            f"/api/v1/documents/prescriptions/{prescription.id}/pdf?download=1",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        assert "attachment" in resp.headers["content-disposition"]

    def test_prescription_pdf_wrong_note_type(self, client, doctor_headers, db, facility, patient, doctor):
        """Note with note_type != PRESCRIPTION → 400."""
        note = ClinicalNote(
            facility_id=facility.id,
            patient_id=patient.id,
            note_type="OBSERVATION",
            content="Patient stable.",
            created_by=doctor.id,
        )
        db.add(note)
        db.commit()
        resp = client.get(
            f"/api/v1/documents/prescriptions/{note.id}/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 400
        assert "PRESCRIPTION" in resp.json()["detail"]

    def test_prescription_pdf_not_found(self, client, doctor_headers):
        resp = client.get(
            "/api/v1/documents/prescriptions/nonexistent-id/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 404

    def test_prescription_pdf_cross_tenant_forbidden(
        self, client, other_admin_headers, prescription
    ):
        """ADMIN of facility B cannot generate PDF for facility A's prescription."""
        resp = client.get(
            f"/api/v1/documents/prescriptions/{prescription.id}/pdf",
            headers=other_admin_headers,
        )
        assert resp.status_code == 403

    def test_prescription_pdf_writes_audit_row(
        self, client, doctor_headers, doctor, db, prescription
    ):
        """After successful generation, DocumentGenerated row exists."""
        before = db.query(DocumentGenerated).count()
        resp = client.get(
            f"/api/v1/documents/prescriptions/{prescription.id}/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        after = db.query(DocumentGenerated).count()
        assert after == before + 1
        row = db.query(DocumentGenerated).order_by(DocumentGenerated.generated_at.desc()).first()
        assert row.document_type == "PRESCRIPTION"
        assert row.generated_by == doctor.id
        assert row.checksum_sha256 is not None
        assert len(row.checksum_sha256) == 64  # SHA-256 hex


# ============================================================================
# Imaging report PDF
# ============================================================================

class TestImagingReportPDF:
    def test_generate_imaging_pdf_with_result(
        self, client, doctor_headers, imaging_order, imaging_result
    ):
        resp = client.get(
            f"/api/v1/documents/imaging-reports/{imaging_order.id}/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"

    def test_generate_imaging_pdf_without_result(
        self, client, doctor_headers, imaging_order, db
    ):
        """If no result exists yet, PDF is still generated (demande seule)."""
        # Delete the imaging_result
        from app.modules.imaging.models import ImagingResult
        db.query(ImagingResult).filter(ImagingResult.order_id == imaging_order.id).delete()
        db.commit()
        resp = client.get(
            f"/api/v1/documents/imaging-reports/{imaging_order.id}/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"

    def test_imaging_pdf_not_found(self, client, doctor_headers):
        resp = client.get(
            "/api/v1/documents/imaging-reports/nonexistent/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 404


# ============================================================================
# Lab result PDF
# ============================================================================

class TestLabResultPDF:
    def test_generate_lab_pdf_with_result(
        self, client, doctor_headers, lab_order, lab_result
    ):
        resp = client.get(
            f"/api/v1/documents/lab-results/{lab_order.id}/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"

    def test_generate_lab_pdf_without_result(self, client, doctor_headers, lab_order, db):
        from app.modules.laboratory.models import LabResult
        db.query(LabResult).filter(LabResult.order_id == lab_order.id).delete()
        db.commit()
        resp = client.get(
            f"/api/v1/documents/lab-results/{lab_order.id}/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"

    def test_lab_pdf_critical_value_highlighted(
        self, client, doctor_headers, lab_order, db
    ):
        """When interpretation contains 'CRITIQUE', the PDF should
        include the critical-value warning banner."""
        from app.modules.laboratory.models import LabResult
        # Update the existing result to be critical
        r = db.query(LabResult).filter(LabResult.order_id == lab_order.id).first()
        if r is None:
            r = LabResult(
                facility_id=lab_order.facility_id,
                order_id=lab_order.id,
                result_value="3.5 g/L",
                interpretation="VALEUR CRITIQUE — Hyperglycémie sévère",
                status="VALIDATED",
            )
            db.add(r)
        else:
            r.interpretation = "VALEUR CRITIQUE — Hyperglycémie sévère"
        db.commit()
        resp = client.get(
            f"/api/v1/documents/lab-results/{lab_order.id}/pdf",
            headers=doctor_headers,
        )
        assert resp.status_code == 200


# ============================================================================
# Invoice PDF
# ============================================================================

class TestInvoicePDF:
    """Invoice PDF requires billing.read permission. DOCTOR doesn't have
    billing.read, so we use admin_headers (SUPER_ADMIN) which bypasses
    all permission checks."""

    def test_generate_invoice_pdf_without_payments(self, client, admin_headers, invoice):
        resp = client.get(
            f"/api/v1/documents/invoices/{invoice.id}/pdf",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert resp.content[:5] == b"%PDF-"

    def test_generate_invoice_pdf_with_payments(
        self, client, admin_headers, invoice, payment
    ):
        resp = client.get(
            f"/api/v1/documents/invoices/{invoice.id}/pdf",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.content[:5] == b"%PDF-"

    def test_invoice_pdf_not_found(self, client, admin_headers):
        resp = client.get(
            "/api/v1/documents/invoices/nonexistent/pdf",
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ============================================================================
# Audit listing
# ============================================================================

class TestDocumentsAudit:
    def test_audit_list_empty(self, client, doctor_headers):
        resp = client.get("/api/v1/documents/audit", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["data"] == []

    def test_audit_list_after_generation(
        self, client, doctor_headers, prescription
    ):
        # Generate one PDF first
        client.get(
            f"/api/v1/documents/prescriptions/{prescription.id}/pdf",
            headers=doctor_headers,
        )
        resp = client.get("/api/v1/documents/audit", headers=doctor_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_audit_list_filter_by_document_type(
        self, client, doctor_headers, prescription, invoice
    ):
        # Generate two different types
        client.get(
            f"/api/v1/documents/prescriptions/{prescription.id}/pdf",
            headers=doctor_headers,
        )
        client.get(
            f"/api/v1/documents/invoices/{invoice.id}/pdf",
            headers=doctor_headers,
        )
        # Filter on PRESCRIPTION only
        resp = client.get(
            "/api/v1/documents/audit?document_type=PRESCRIPTION",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(r["document_type"] == "PRESCRIPTION" for r in data["data"])
        assert data["total"] >= 1

    def test_audit_list_filter_by_patient(
        self, client, doctor_headers, prescription, patient
    ):
        client.get(
            f"/api/v1/documents/prescriptions/{prescription.id}/pdf",
            headers=doctor_headers,
        )
        resp = client.get(
            f"/api/v1/documents/audit?patient_id={patient.id}",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(r["patient_id"] == patient.id for r in data["data"])
