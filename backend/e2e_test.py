"""
GuinéeCare Hospital Suite — End-to-End Test Suite
Tests all modules, multi-tenant RLS, RBAC, and personnel management.
Uses SQLite database for testing.
"""
import os
import sys
import time
from datetime import date, datetime, timedelta

# Force SQLite for testing
os.environ["DATABASE_URL"] = "sqlite:////tmp/guineecare_test.db"
os.environ["AUTH_SECRET"] = "test-secret-key-e2e"
os.environ["ENVIRONMENT"] = "local"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["CORS_ORIGINS"] = '["http://localhost"]'

from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.core.security import hash_password
from app.modules.facilities.models import Facility
from app.modules.departments.models import Department
from app.modules.patients.models import Patient
from app.modules.users.models import User
from app.modules.rbac.models import Role, Permission, RolePermission
from app.modules.rbac.seed import seed_rbac
from app.modules.emergency.models import EmergencyVisit
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock
from app.modules.laboratory.models import LabTest
from app.modules.billing.models import TariffItem
from app.modules.hospitalization.models import Room, Bed
from app.modules.personnel.models import StaffMember, OnCallSchedule, LeaveRequest, Contract
from app.modules.quality.models import QualityIndicator
from app.modules.surgery.models import OperatingRoom
from app.modules.clinical.models import ClinicalNote, PatientMeasurement

from app.main import app

# Disable rate limiting for tests
app.state.limiter.enabled = False

client = TestClient(app)

results = {"passed": 0, "failed": 0, "errors": []}

def test(name, condition, detail=""):
    if condition:
        results["passed"] += 1
        print(f"  PASS {name}")
    else:
        results["failed"] += 1
        results["errors"].append(f"{name}: {detail}")
        print(f"  FAIL {name} -- {detail}")

def seed_test_data():
    db = SessionLocal()
    try:
        seed_rbac(db)

        # 2 facilities
        f1 = Facility(id="fac-donka", code="CHU-DONKA", name="CHU Donka", category="CHU", region="Conakry", status="ACTIVE")
        f2 = Facility(id="fac-kankan", code="HGR-KANKAN", name="HGR Kankan", category="HGR", region="Kankan", status="ACTIVE")
        db.add_all([f1, f2]); db.flush()

        # Departments
        d1 = Department(id="dept-chir", code="CHIRURGIE", name="Chirurgie", facility_id="fac-donka")
        d2 = Department(id="dept-med", code="MEDECINE", name="Médecine", facility_id="fac-donka")
        d3 = Department(id="dept-chir-k", code="CHIRURGIE", name="Chirurgie", facility_id="fac-kankan")
        db.add_all([d1, d2, d3]); db.flush()

        # Users
        users = [
            User(id="u-superadmin", email="admin@guineecare.com", password_hash=hash_password("admin123"), first_name="Super", last_name="Admin", role="SUPER_ADMIN", facility_id="fac-donka", is_active=True),
            User(id="u-admin-donka", email="admin.donka@chu-donka.gn", password_hash=hash_password("admin123"), first_name="Amadou", last_name="Diallo", role="ADMIN", facility_id="fac-donka", is_active=True),
            User(id="u-doctor-donka", email="dr.diallo@chu-donka.gn", password_hash=hash_password("doctor123"), first_name="Mamadou", last_name="Diallo", role="DOCTOR", facility_id="fac-donka", is_active=True),
            User(id="u-nurse-donka", email="inf.bah@chu-donka.gn", password_hash=hash_password("nurse123"), first_name="Fatoumata", last_name="Bah", role="NURSE", facility_id="fac-donka", is_active=True),
            User(id="u-pharma-donka", email="pharm.sow@chu-donka.gn", password_hash=hash_password("pharma123"), first_name="Ibrahima", last_name="Sow", role="PHARMACIST", facility_id="fac-donka", is_active=True),
            User(id="u-lab-donka", email="lab.toure@chu-donka.gn", password_hash=hash_password("lab123"), first_name="Kadiatou", last_name="Touré", role="LAB_TECH", facility_id="fac-donka", is_active=True),
            User(id="u-cashier-donka", email="caisse.conde@chu-donka.gn", password_hash=hash_password("cashier123"), first_name="Mariama", last_name="Condé", role="CASHIER", facility_id="fac-donka", is_active=True),
            User(id="u-midwife-donka", email="sf.keita@chu-donka.gn", password_hash=hash_password("midwife123"), first_name="Aissatou", last_name="Keita", role="MIDWIFE", facility_id="fac-donka", is_active=True),
            User(id="u-doctor-kankan", email="dr.cisse@hgr-kankan.gn", password_hash=hash_password("doctor123"), first_name="Oumar", last_name="Cissé", role="DOCTOR", facility_id="fac-kankan", is_active=True),
            User(id="u-admin-kankan", email="admin.kankan@hgr-kankan.gn", password_hash=hash_password("admin123"), first_name="Lansana", last_name="Camara", role="ADMIN", facility_id="fac-kankan", is_active=True),
            User(id="u-inactive", email="inactive@test.gn", password_hash=hash_password("test123"), first_name="Inactive", last_name="User", role="NURSE", facility_id="fac-donka", is_active=False),
        ]
        db.add_all(users); db.flush()

        # Staff
        staff = [
            StaffMember(id="s-doc1", facility_id="fac-donka", user_id="u-doctor-donka", employee_number="EMP-0001", first_name="Mamadou", last_name="Diallo", profession="MEDECIN", specialty="Chirurgie", department_id="dept-chir", status="ACTIVE"),
            StaffMember(id="s-nurse1", facility_id="fac-donka", user_id="u-nurse-donka", employee_number="EMP-0002", first_name="Fatoumata", last_name="Bah", profession="INFIRMIER", department_id="dept-med", status="ACTIVE"),
            StaffMember(id="s-doc2", facility_id="fac-kankan", user_id="u-doctor-kankan", employee_number="EMP-0003", first_name="Oumar", last_name="Cissé", profession="MEDECIN", department_id="dept-chir-k", status="ACTIVE"),
        ]
        db.add_all(staff); db.flush()

        # Patients
        p1 = Patient(id="p-1", facility_id="fac-donka", patient_number="PAT-0001", first_name="Abdoulaye", last_name="Condé", date_of_birth=date(1985, 3, 15), gender="M", phone="+224622000001")
        p2 = Patient(id="p-2", facility_id="fac-donka", patient_number="PAT-0002", first_name="Mariame", last_name="Diallo", date_of_birth=date(1990, 7, 22), gender="F")
        p3 = Patient(id="p-3", facility_id="fac-kankan", patient_number="PAT-0003", first_name="Ibrahim", last_name="Touré", date_of_birth=date(1978, 1, 10), gender="M")
        db.add_all([p1, p2, p3]); db.flush()

        # Room & Bed (correct field names)
        room1 = Room(id="room-1", facility_id="fac-donka", department_id="dept-chir", code="CHIR-A", name="Chirurgie A", room_type="COLLECTIVE", status="ACTIVE")
        bed1 = Bed(id="bed-1", facility_id="fac-donka", room_id="room-1", bed_number="CHIR-A-01", bed_status="AVAILABLE")
        db.add_all([room1, bed1]); db.flush()

        # Pharmacy
        pp = PharmacyProduct(id="pp-1", facility_id="fac-donka", code="PARA500", name="Paracétamol 500mg", category="ANTALGIQUE", form="COMPRIME")
        ps = PharmacyStock(id="ps-1", product_id="pp-1", facility_id="fac-donka", quantity_available=500, min_threshold=50)
        db.add_all([pp, ps]); db.flush()

        # Lab
        lt = LabTest(id="lt-1", facility_id="fac-donka", code="NFS", name="NFS", category="HEMATOLOGIE", sample_type="SANG")
        db.add(lt); db.flush()

        # Tariff
        ti = TariffItem(id="ti-1", facility_id="fac-donka", code="CONS-STD", name="Consultation standard", category="CONSULTATION", unit_price=50000.0)
        db.add(ti); db.flush()

        # Quality
        qi = QualityIndicator(id="qi-1", facility_id="fac-donka", code="TAUX-OCCUPATION", name="Taux d'occupation", category="EFFICIENCY", unit="%", target_value="80")
        db.add(qi); db.flush()

        # OR
        or1 = OperatingRoom(id="or-1", facility_id="fac-donka", code="BLOC-01", name="Bloc 1", status="AVAILABLE")
        db.add(or1); db.flush()

        db.commit()
        print("  Seed: OK")
    except Exception as e:
        db.rollback()
        print(f"  Seed ERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


def do_login(email, password):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return resp

def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── RUN ────────────────────────────────────────────────────────
print("=" * 60)
print("GUINEECARE E2E TEST SUITE")
print("=" * 60)

# Phase 1: Startup
print("\n[1] Database & Startup")
Base.metadata.create_all(bind=engine)
seed_test_data()

resp = client.get("/health")
test("Health check", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 2: Auth
print("\n[2] Authentication")
resp = do_login("admin@guineecare.com", "admin123")
test("Login SUPER_ADMIN", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:300]}")
super_token = resp.json().get("access_token", "") if resp.status_code == 200 else ""
test("Token present", bool(super_token), "No token")

if resp.status_code == 200:
    ud = resp.json().get("user", {})
    test("User data in response", bool(ud.get("id")), f"User: {ud}")
    test("Role in user data", ud.get("role") == "SUPER_ADMIN", f"Role: {ud.get('role')}")
    test("Facility_id in user data", "facility_id" in ud, f"Keys: {list(ud.keys())}")

resp = do_login("admin@guineecare.com", "wrong")
test("Wrong password -> 401", resp.status_code == 401, f"Got {resp.status_code}")

resp = do_login("inactive@test.gn", "test123")
test("Inactive user -> 403", resp.status_code == 403, f"Got {resp.status_code}")

if super_token:
    resp = client.get("/api/v1/auth/me", headers=auth_header(super_token))
    test("GET /auth/me", resp.status_code == 200, f"Got {resp.status_code}")

resp = client.get("/api/v1/auth/me")
test("No token -> 401", resp.status_code == 401, f"Got {resp.status_code}")

# Phase 3: Multi-Tenant
print("\n[3] Multi-Tenant RLS")
resp = do_login("dr.diallo@chu-donka.gn", "doctor123")
donka_doc_token = resp.json().get("access_token", "") if resp.status_code == 200 else ""
test("Login Donka doctor", bool(donka_doc_token), f"Got {resp.status_code}")

resp = do_login("dr.cisse@hgr-kankan.gn", "doctor123")
kankan_doc_token = resp.json().get("access_token", "") if resp.status_code == 200 else ""
test("Login Kankan doctor", bool(kankan_doc_token), f"Got {resp.status_code}")

resp = do_login("admin.donka@chu-donka.gn", "admin123")
donka_admin_token = resp.json().get("access_token", "") if resp.status_code == 200 else ""
test("Login Donka admin", bool(donka_admin_token), f"Got {resp.status_code}")

if super_token:
    resp = client.get("/api/v1/patients", headers=auth_header(super_token))
    test("SUPER_ADMIN sees all patients", resp.status_code == 200, f"Got {resp.status_code}")
    if resp.status_code == 200:
        test("Total patients = 3", resp.json().get("total") == 3, f"Total: {resp.json().get('total')}")

if donka_doc_token:
    resp = client.get("/api/v1/patients", headers=auth_header(donka_doc_token))
    test("Donka doc sees Donka patients only", resp.status_code == 200, f"Got {resp.status_code}")
    if resp.status_code == 200:
        test("Donka patients = 2", resp.json().get("total") == 2, f"Total: {resp.json().get('total')}")

if kankan_doc_token:
    resp = client.get("/api/v1/patients", headers=auth_header(kankan_doc_token))
    test("Kankan doc sees Kankan patients only", resp.status_code == 200, f"Got {resp.status_code}")
    if resp.status_code == 200:
        test("Kankan patients = 1", resp.json().get("total") == 1, f"Total: {resp.json().get('total')}")

if donka_doc_token:
    resp = client.get("/api/v1/patients/p-3", headers=auth_header(donka_doc_token))
    test("Donka doc blocked from Kankan patient", resp.status_code == 403, f"Got {resp.status_code}")

if donka_admin_token:
    resp = client.post("/api/v1/patients", headers=auth_header(donka_admin_token), json={
        "first_name": "Cross", "last_name": "Tenant", "patient_number": "PAT-XX",
        "facility_id": "fac-kankan", "date_of_birth": "2000-01-01", "gender": "M"
    })
    test("Donka admin blocked creating patient in Kankan", resp.status_code == 403, f"Got {resp.status_code}: {resp.text[:200]}")

# Phase 4: RBAC
print("\n[4] RBAC Permissions")
pharma_token = ""
resp = do_login("pharm.sow@chu-donka.gn", "pharma123")
if resp.status_code == 200:
    pharma_token = resp.json().get("access_token", "")
if pharma_token:
    resp = client.get("/api/v1/pharmacy/products", headers=auth_header(pharma_token))
    test("Pharmacist reads pharmacy", resp.status_code == 200, f"Got {resp.status_code}")

cashier_token = ""
resp = do_login("caisse.conde@chu-donka.gn", "cashier123")
if resp.status_code == 200:
    cashier_token = resp.json().get("access_token", "")
if cashier_token:
    resp = client.get("/api/v1/billing/tariffs", headers=auth_header(cashier_token))
    test("Cashier reads billing", resp.status_code == 200, f"Got {resp.status_code}")

nurse_token = ""
resp = do_login("inf.bah@chu-donka.gn", "nurse123")
if resp.status_code == 200:
    nurse_token = resp.json().get("access_token", "")
if nurse_token:
    resp = client.get("/api/v1/pharmacy/products", headers=auth_header(nurse_token))
    test("Nurse blocked from pharmacy", resp.status_code == 403, f"Got {resp.status_code}")

    resp = client.get("/api/v1/patients", headers=auth_header(nurse_token))
    test("Nurse reads patients", resp.status_code == 200, f"Got {resp.status_code}")

    resp = client.get("/api/v1/billing/tariffs", headers=auth_header(nurse_token))
    test("Nurse blocked from billing", resp.status_code == 403, f"Got {resp.status_code}")

lab_token = ""
resp = do_login("lab.toure@chu-donka.gn", "lab123")
if resp.status_code == 200:
    lab_token = resp.json().get("access_token", "")
if lab_token:
    resp = client.get("/api/v1/laboratory/tests", headers=auth_header(lab_token))
    test("Lab tech reads lab", resp.status_code == 200, f"Got {resp.status_code}")

    resp = client.get("/api/v1/pharmacy/products", headers=auth_header(lab_token))
    test("Lab tech blocked from pharmacy", resp.status_code == 403, f"Got {resp.status_code}")

midwife_token = ""
resp = do_login("sf.keita@chu-donka.gn", "midwife123")
if resp.status_code == 200:
    midwife_token = resp.json().get("access_token", "")
if midwife_token:
    resp = client.get("/api/v1/maternity/records", headers=auth_header(midwife_token))
    test("Midwife reads maternity", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 5: Personnel
print("\n[5] Personnel Management")
if super_token:
    resp = client.get("/api/v1/personnel/staff", headers=auth_header(super_token))
    test("List staff (SUPER_ADMIN)", resp.status_code == 200, f"Got {resp.status_code}")
    if resp.status_code == 200:
        test("SUPER_ADMIN sees 3 staff", resp.json().get("total") == 3, f"Total: {resp.json().get('total')}")

if donka_doc_token:
    resp = client.get("/api/v1/personnel/staff", headers=auth_header(donka_doc_token))
    test("Donka doc sees Donka staff", resp.status_code == 200, f"Got {resp.status_code}")
    if resp.status_code == 200:
        test("Donka staff = 2", resp.json().get("total") == 2, f"Total: {resp.json().get('total')}")

new_staff_id = ""
if donka_admin_token:
    resp = client.post("/api/v1/personnel/staff", headers=auth_header(donka_admin_token), json={
        "first_name": "Aminata", "last_name": "Sylla", "profession": "SAGE_FEMME",
        "specialty": "Gynécologie", "contract_type": "CDI", "salary_grade": "A4",
        "hire_date": "2024-01-15"
    })
    test("Create staff member", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:300]}")
    if resp.status_code == 200:
        new_staff_id = resp.json().get("data", {}).get("id", "")

    if new_staff_id:
        resp = client.get(f"/api/v1/personnel/staff/{new_staff_id}", headers=auth_header(donka_admin_token))
        test("Get staff detail", resp.status_code == 200, f"Got {resp.status_code}")

        resp = client.put(f"/api/v1/personnel/staff/{new_staff_id}", headers=auth_header(donka_admin_token), json={
            "phone": "+224622009999", "specialty": "Gynécologie-Obstétrique"
        })
        test("Update staff", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

# On-call
if donka_admin_token:
    resp = client.post("/api/v1/personnel/on-call", headers=auth_header(donka_admin_token), json={
        "staff_id": "s-doc1", "on_call_date": "2026-06-20", "shift_type": "NIGHT"
    })
    test("Create on-call", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

    resp = client.get("/api/v1/personnel/on-call", headers=auth_header(donka_admin_token))
    test("List on-call", resp.status_code == 200, f"Got {resp.status_code}")

# Leaves
leave_id = ""
if donka_admin_token:
    resp = client.post("/api/v1/personnel/leaves", headers=auth_header(donka_admin_token), json={
        "staff_id": "s-doc1", "leave_type": "CONGE_ANNUEL",
        "start_date": "2026-07-01", "end_date": "2026-07-15", "reason": "Congé annuel"
    })
    test("Create leave request", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")
    if resp.status_code == 200:
        leave_id = resp.json().get("data", {}).get("id", "")

    if leave_id:
        resp = client.put(f"/api/v1/personnel/leaves/{leave_id}", headers=auth_header(donka_admin_token), json={"status": "APPROVED"})
        test("Approve leave", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

    resp = client.get("/api/v1/personnel/leaves", headers=auth_header(donka_admin_token))
    test("List leaves", resp.status_code == 200, f"Got {resp.status_code}")

# Contracts
if donka_admin_token:
    resp = client.post("/api/v1/personnel/contracts", headers=auth_header(donka_admin_token), json={
        "staff_id": "s-doc1", "contract_type": "CDI",
        "start_date": "2020-03-01", "position": "Médecin chef", "salary_grade": "A7"
    })
    test("Create contract", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

    resp = client.get("/api/v1/personnel/contracts", headers=auth_header(donka_admin_token))
    test("List contracts", resp.status_code == 200, f"Got {resp.status_code}")

# Stats
if donka_admin_token:
    resp = client.get("/api/v1/personnel/stats", headers=auth_header(donka_admin_token))
    test("Personnel stats", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")
    if resp.status_code == 200:
        stats = resp.json().get("data", {})
        test("Stats has total_staff", "total_staff" in stats, f"Keys: {list(stats.keys())}")

# Phase 6: Patients
print("\n[6] Patients")
if super_token:
    resp = client.post("/api/v1/patients", headers=auth_header(super_token), json={
        "first_name": "Test", "last_name": "Patient", "patient_number": "PAT-NEW",
        "date_of_birth": "1995-06-15", "gender": "F", "facility_id": "fac-donka"
    })
    test("Create patient", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

    resp = client.get("/api/v1/patients?search=Condé", headers=auth_header(super_token))
    test("Search patients", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 7: Facilities
print("\n[7] Facilities")
if super_token:
    resp = client.get("/api/v1/facilities", headers=auth_header(super_token))
    test("List facilities (SUPER_ADMIN)", resp.status_code == 200, f"Got {resp.status_code}")
    if resp.status_code == 200:
        test("2 facilities", resp.json().get("total") == 2, f"Total: {resp.json().get('total')}")

if donka_admin_token:
    resp = client.get("/api/v1/facilities", headers=auth_header(donka_admin_token))
    test("List facilities (ADMIN)", resp.status_code == 200, f"Got {resp.status_code}")
    if resp.status_code == 200:
        test("ADMIN sees own facility only", resp.json().get("total") == 1, f"Total: {resp.json().get('total')}")

# Phase 8: Departments
print("\n[8] Departments")
if super_token:
    resp = client.get("/api/v1/departments", headers=auth_header(super_token))
    test("List departments", resp.status_code == 200, f"Got {resp.status_code}")

if donka_admin_token:
    resp = client.post("/api/v1/departments", headers=auth_header(donka_admin_token), json={
        "code": "PEDIATRIE", "name": "Pédiatrie", "facility_id": "fac-donka"
    })
    test("Create department", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

# Phase 9: Emergency
print("\n[9] Emergency")
visit_id = ""
if donka_doc_token:
    resp = client.post("/api/v1/emergency/visits", headers=auth_header(donka_doc_token), json={
        "patient_id": "p-1", "chief_complaint": "Douleur abdominale", "facility_id": "fac-donka"
    })
    test("Create emergency visit", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:300]}")
    if resp.status_code == 200:
        visit_id = resp.json().get("data", {}).get("id", "")

    if visit_id:
        resp = client.post(f"/api/v1/emergency/visits/{visit_id}/triage", headers=auth_header(donka_doc_token), json={
            "priority_level": "URGENT"
        })
        test("Triage visit", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

        resp = client.post(f"/api/v1/emergency/visits/{visit_id}/orientation", headers=auth_header(donka_doc_token), json={
            "orientation": "CHIRURGIE"
        })
        test("Orient visit", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

    resp = client.get("/api/v1/emergency/queue", headers=auth_header(donka_doc_token))
    test("Get emergency queue", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 10: Pharmacy
print("\n[10] Pharmacy")
if pharma_token:
    resp = client.get("/api/v1/pharmacy/products", headers=auth_header(pharma_token))
    test("List products", resp.status_code == 200, f"Got {resp.status_code}")

    resp = client.get("/api/v1/pharmacy/stock", headers=auth_header(pharma_token))
    test("List stock", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 11: Lab
print("\n[11] Laboratory")
if lab_token:
    resp = client.get("/api/v1/laboratory/tests", headers=auth_header(lab_token))
    test("List lab tests", resp.status_code == 200, f"Got {resp.status_code}")

if donka_doc_token:
    resp = client.post("/api/v1/laboratory/orders", headers=auth_header(donka_doc_token), json={
        "patient_id": "p-1", "test_id": "lt-1", "facility_id": "fac-donka"
    })
    test("Create lab order", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

# Phase 12: Billing
print("\n[12] Billing")
if donka_admin_token:
    resp = client.get("/api/v1/billing/tariffs", headers=auth_header(donka_admin_token))
    test("List tariffs", resp.status_code == 200, f"Got {resp.status_code}")

    resp = client.post("/api/v1/billing/invoices", headers=auth_header(donka_admin_token), json={
        "patient_id": "p-1", "facility_id": "fac-donka",
        "invoice_number": "FAC-001", "net_amount": 50000.0, "description": "Consultation standard"
    })
    test("Create invoice", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:300]}")

# Phase 13: Hospitalization
print("\n[13] Hospitalization")
if donka_admin_token:
    resp = client.get("/api/v1/hospitalization/rooms", headers=auth_header(donka_admin_token))
    test("List rooms", resp.status_code == 200, f"Got {resp.status_code}")

    resp = client.get("/api/v1/hospitalization/beds", headers=auth_header(donka_admin_token))
    test("List beds", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 14: Clinical
print("\n[14] Clinical")
if donka_doc_token:
    resp = client.post("/api/v1/clinical/patients/p-1/notes", headers=auth_header(donka_doc_token), json={
        "facility_id": "fac-donka",
        "note_type": "CONSULTATION", "content": "Patient présente douleur abdominale."
    })
    test("Create clinical note", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:200]}")

    resp = client.post("/api/v1/clinical/patients/p-1/measurements", headers=auth_header(donka_doc_token), json={
        "facility_id": "fac-donka",
        "measurement_type": "WEIGHT", "value": "75", "unit": "kg"
    })
    test("Create measurement", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:300]}")

# Phase 15: Maternity
print("\n[15] Maternity")
if midwife_token:
    resp = client.get("/api/v1/maternity/records", headers=auth_header(midwife_token))
    test("List maternity records", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 16: Imaging
print("\n[16] Imaging")
if donka_doc_token:
    resp = client.post("/api/v1/imaging/orders", headers=auth_header(donka_doc_token), json={
        "patient_id": "p-1", "facility_id": "fac-donka",
        "exam_type": "RADIOGRAPHY", "body_region": "Abdomen", "urgency": "ROUTINE"
    })
    test("Create imaging order", resp.status_code == 200, f"Got {resp.status_code}: {resp.text[:300]}")

# Phase 17: Surgery
print("\n[17] Surgery")
if donka_admin_token:
    resp = client.get("/api/v1/surgery/rooms", headers=auth_header(donka_admin_token))
    test("List OR rooms", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 18: Quality
print("\n[18] Quality")
if donka_admin_token:
    resp = client.get("/api/v1/quality/indicators", headers=auth_header(donka_admin_token))
    test("List quality indicators", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 19: RBAC Admin
print("\n[19] RBAC Admin")
if super_token:
    resp = client.get("/api/v1/rbac/roles", headers=auth_header(super_token))
    test("List RBAC roles", resp.status_code == 200, f"Got {resp.status_code}")
    if resp.status_code == 200:
        test("8+ roles", resp.json().get("total", 0) >= 8, f"Total: {resp.json().get('total')}")

    resp = client.get("/api/v1/rbac/permissions", headers=auth_header(super_token))
    test("List RBAC permissions", resp.status_code == 200, f"Got {resp.status_code}")

# Phase 20: Users
print("\n[20] Users")
if super_token:
    resp = client.get("/api/v1/users", headers=auth_header(super_token))
    test("List users (SUPER_ADMIN)", resp.status_code == 200, f"Got {resp.status_code}")

if donka_admin_token:
    resp = client.get("/api/v1/users", headers=auth_header(donka_admin_token))
    test("List users (ADMIN)", resp.status_code == 200, f"Got {resp.status_code}")

if donka_doc_token:
    resp = client.get("/api/v1/users", headers=auth_header(donka_doc_token))
    test("Doctor blocked from users list", resp.status_code == 403, f"Got {resp.status_code}")


# ── Results ────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("TEST RESULTS")
print("=" * 60)
print(f"  Passed: {results['passed']}")
print(f"  Failed: {results['failed']}")
print(f"  Total:  {results['passed'] + results['failed']}")

if results["errors"]:
    print("\nFAILURES:")
    for err in results["errors"]:
        print(f"  - {err}")
else:
    print("\nAll tests passed!")

# Cleanup
try:
    os.unlink("/tmp/guineecare_test.db")
except:
    pass

sys.exit(0 if results["failed"] == 0 else 1)
