"""Tests for v1.2.0 search module — global multi-resource search.

Covers:
- Patient search by name, by patient_number, by phone.
- Invoice search by invoice_number, by description.
- Lab order search by test name/code.
- Imaging order search by exam_type, body_region.
- Clinical note search by content.
- Prefix-based search (PAT-xxx, INV-xxx).
- Tenant filtering (facility A cannot see facility B results).
- Empty query (too short) → 422.
- Capping (limit_per_category + max_total).
- Categories filter.
- Invalid category → 422.
"""
import pytest

from app.core.security import create_access_token, hash_password
from app.modules.billing.models import Invoice
from app.modules.clinical.models import ClinicalNote
from app.modules.facilities.models import Facility
from app.modules.imaging.models import ImagingOrder
from app.modules.laboratory.models import LabOrder, LabTest
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
    fac = Facility(name="CHU Other", code="CHU-OTHER", category="CHU", region="Kankan")
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac


@pytest.fixture
def super_admin_headers(db):
    user = User(
        email="sa@search.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Super",
        last_name="Admin",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.id, facility_id=user.facility_id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def doctor_headers(db, facility):
    user = User(
        email="doc@search.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Doc",
        last_name="Search",
        role="DOCTOR",
        facility_id=facility.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.id, facility_id=user.facility_id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def other_doctor_headers(db, other_facility):
    user = User(
        email="doc.other@search.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="DocOther",
        last_name="Search",
        role="DOCTOR",
        facility_id=other_facility.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(subject=user.id, facility_id=user.facility_id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def patients(db, facility):
    p1 = Patient(
        facility_id=facility.id,
        patient_number="PAT-0001",
        first_name="Aissatou",
        last_name="Camara",
        gender="F",
        phone="+224 622 111 111",
    )
    p2 = Patient(
        facility_id=facility.id,
        patient_number="PAT-0002",
        first_name="Mamadou",
        last_name="Diallo",
        gender="M",
        phone="+224 622 222 222",
    )
    p3 = Patient(
        facility_id=facility.id,
        patient_number="PAT-0003",
        first_name="Fatou",
        last_name="Camara",
        gender="F",
        phone="+224 622 333 333",
    )
    db.add_all([p1, p2, p3])
    db.commit()
    return [p1, p2, p3]


@pytest.fixture
def other_patient(db, other_facility):
    p = Patient(
        facility_id=other_facility.id,
        patient_number="PAT-9999",
        first_name="Hidden",
        last_name="Camara",
        gender="F",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@pytest.fixture
def invoice(db, facility, patients):
    inv = Invoice(
        facility_id=facility.id,
        patient_id=patients[0].id,
        invoice_number="INV-2026-0001",
        description="Consultation cardiologie",
        net_amount=200000,
        paid_amount=200000,
        balance_due=0,
        status="PAID",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return inv


@pytest.fixture
def lab_test(db, facility):
    t = LabTest(
        facility_id=facility.id,
        code="NFS",
        name="Numération Formule Sanguine",
        category="HEMATOLOGIE",
        sample_type="Sang",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@pytest.fixture
def lab_order(db, facility, patients, lab_test):
    o = LabOrder(
        facility_id=facility.id,
        patient_id=patients[0].id,
        test_id=lab_test.id,
        priority="NORMAL",
        status="ORDERED",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@pytest.fixture
def imaging_order(db, facility, patients):
    o = ImagingOrder(
        facility_id=facility.id,
        patient_id=patients[0].id,
        exam_type="ULTRASOUND",
        body_region="Abdomen",
        clinical_info="Douleur abdominale",
        urgency="URGENT",
        status="PENDING",
    )
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@pytest.fixture
def clinical_note(db, facility, patients):
    n = ClinicalNote(
        facility_id=facility.id,
        patient_id=patients[0].id,
        note_type="CONSULTATION",
        content="Patient vu pour fièvre et toux. Prescription antibiotique.",
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


# ============================================================================
# Tests — basic search
# ============================================================================

class TestSearchBasics:
    def test_search_too_short_query(self, client, doctor_headers):
        """Query < 2 chars → 422."""
        resp = client.get("/api/v1/search?q=a", headers=doctor_headers)
        assert resp.status_code == 422

    def test_search_no_results(self, client, doctor_headers):
        resp = client.get("/api/v1/search?q=zzzzzzz", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] == 0
        assert data["categories"] == {}

    def test_search_unauthenticated(self, client):
        resp = client.get("/api/v1/search?q=test")
        assert resp.status_code == 401


# ============================================================================
# Tests — patient search
# ============================================================================

class TestPatientSearch:
    def test_search_by_last_name(self, client, doctor_headers, patients):
        """'Camara' returns both Aissatou and Fatou."""
        resp = client.get("/api/v1/search?q=camara", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "patient" in data["categories"]
        patient_results = data["categories"]["patient"]
        assert len(patient_results) == 2
        labels = [r["label"] for r in patient_results]
        assert any("Aissatou" in l for l in labels)
        assert any("Fatou" in l for l in labels)

    def test_search_by_first_name(self, client, doctor_headers, patients):
        resp = client.get("/api/v1/search?q=mamadou", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "patient" in data["categories"]
        assert len(data["categories"]["patient"]) == 1
        assert "Mamadou" in data["categories"]["patient"][0]["label"]

    def test_search_by_patient_number(self, client, doctor_headers, patients):
        resp = client.get("/api/v1/search?q=PAT-0002", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "patient" in data["categories"]
        assert len(data["categories"]["patient"]) == 1
        assert "Diallo" in data["categories"]["patient"][0]["label"]

    def test_search_by_phone(self, client, doctor_headers, patients):
        resp = client.get("/api/v1/search?q=622 222", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "patient" in data["categories"]
        assert len(data["categories"]["patient"]) == 1


# ============================================================================
# Tests — invoice search
# ============================================================================

class TestInvoiceSearch:
    def test_search_by_invoice_number(self, client, doctor_headers, invoice):
        resp = client.get("/api/v1/search?q=INV-2026", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "invoice" in data["categories"]
        assert len(data["categories"]["invoice"]) >= 1

    def test_search_by_description(self, client, doctor_headers, invoice):
        resp = client.get("/api/v1/search?q=cardiologie", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "invoice" in data["categories"]


# ============================================================================
# Tests — lab / imaging / clinical note search
# ============================================================================

class TestResourceSearch:
    def test_search_lab_order_by_test_name(self, client, doctor_headers, lab_order):
        resp = client.get("/api/v1/search?q=numération", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "lab_order" in data["categories"]
        assert len(data["categories"]["lab_order"]) >= 1

    def test_search_lab_order_by_test_code(self, client, doctor_headers, lab_order):
        resp = client.get("/api/v1/search?q=NFS", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "lab_order" in data["categories"]

    def test_search_imaging_by_body_region(self, client, doctor_headers, imaging_order):
        resp = client.get("/api/v1/search?q=abdomen", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "imaging_order" in data["categories"]

    def test_search_clinical_note_by_content(self, client, doctor_headers, clinical_note):
        resp = client.get("/api/v1/search?q=fièvre", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "clinical_note" in data["categories"]


# ============================================================================
# Tests — prefix-based search
# ============================================================================

class TestPrefixSearch:
    def test_pat_prefix_restricts_to_patients(
        self, client, doctor_headers, patients, invoice, lab_order, imaging_order
    ):
        """PAT-xxx → only patient category, prefix stripped."""
        resp = client.get("/api/v1/search?q=PAT-0001", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "patient" in data["categories"]
        # Should NOT return other categories even if they match
        assert "invoice" not in data["categories"]
        assert "lab_order" not in data["categories"]
        assert "imaging_order" not in data["categories"]

    def test_inv_prefix_restricts_to_invoices(self, client, doctor_headers, invoice):
        resp = client.get("/api/v1/search?q=INV-2026", headers=doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "invoice" in data["categories"]
        assert "patient" not in data["categories"]


# ============================================================================
# Tests — tenant isolation
# ============================================================================

class TestTenantIsolation:
    def test_doctor_in_facility_a_cannot_see_facility_b_patients(
        self, client, other_doctor_headers, patients, other_patient
    ):
        """Doctor from facility B searches 'Camara' — should not see facility A's Camara patients."""
        resp = client.get("/api/v1/search?q=camara", headers=other_doctor_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        # other_patient is in other_facility with last_name Camara — should match
        if "patient" in data["categories"]:
            # All returned patients must be in other_facility
            for p in data["categories"]["patient"]:
                assert p["id"] == other_patient.id
        # And no patients from facility A should leak
        patient_ids = [p["id"] for p in data["categories"].get("patient", [])]
        for original_p in patients:
            assert original_p.id not in patient_ids

    def test_super_admin_sees_all_facilities(
        self, client, super_admin_headers, patients, other_patient
    ):
        """SUPER_ADMIN searching 'Camara' should see all Camara patients across facilities."""
        resp = client.get("/api/v1/search?q=camara", headers=super_admin_headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "patient" in data["categories"]
        all_ids = {p["id"] for p in data["categories"]["patient"]}
        # At least the 2 Camara in facility A + 1 in other_facility
        assert other_patient.id in all_ids


# ============================================================================
# Tests — categories filter + capping
# ============================================================================

class TestCategoriesAndCapping:
    def test_categories_filter_restricts_search(
        self, client, doctor_headers, patients, invoice
    ):
        """?categories=patient only returns patient results."""
        # 'a' is broad — matches Camara, Aissatou, plus invoice description
        resp = client.get(
            "/api/v1/search?q=camara&categories=patient",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "patient" in data["categories"]
        # Only patient category should be returned
        assert set(data["categories"].keys()) == {"patient"}

    def test_invalid_category_returns_422(self, client, doctor_headers):
        resp = client.get(
            "/api/v1/search?q=test&categories=invalid",
            headers=doctor_headers,
        )
        assert resp.status_code == 422

    def test_limit_per_category_caps_results(self, client, doctor_headers, db, facility):
        """Create 15 patients matching 'aaa' and verify limit=5 caps the result."""
        for i in range(15):
            p = Patient(
                facility_id=facility.id,
                patient_number=f"PAT-AAA-{i:03d}",
                first_name=f"AAA{i}",
                last_name="AAAPatient",
            )
            db.add(p)
        db.commit()
        resp = client.get(
            "/api/v1/search?q=AAAPatient&limit=5",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data["categories"].get("patient", [])) <= 5

    def test_max_total_caps_all_results(self, client, doctor_headers, db, facility):
        # Use 'aa' (2 chars) to satisfy min_length=2 validation.
        for i in range(5):
            p = Patient(
                facility_id=facility.id,
                patient_number=f"PAT-AATOT-{i:03d}",
                first_name="AABatch",
                last_name="AATotal",
            )
            db.add(p)
        db.commit()
        resp = client.get(
            "/api/v1/search?q=AATotal&max_total=3",
            headers=doctor_headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["total"] <= 3
