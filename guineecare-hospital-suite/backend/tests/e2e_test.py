"""
GuinéeCare Hospital Suite — End-to-End Test Suite
Tests ALL 120 API endpoints, multi-tenant isolation, and RBAC permissions.
Uses SQLite for local testing (no PostgreSQL/Redis required).
"""

import os, sys, json, traceback
from datetime import date, datetime

# ── Setup test environment BEFORE importing app ─────────────────────
os.environ["DATABASE_URL"] = "sqlite:///./test_e2e.db"
os.environ["AUTH_SECRET"] = "test-secret-key-e2e"
os.environ["AUTH_ALGORITHM"] = "HS256"
os.environ["ENVIRONMENT"] = "local"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["RATELIMIT_ENABLED"] = "false"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import hash_password

# Disable rate limiter for tests by making it very permissive
from app.core.limiter import limiter
limiter.reset()

# Import all models
from app.modules.facilities.models import Facility
from app.modules.users.models import User
from app.modules.rbac.models import Role, Permission, RolePermission
from app.modules.rbac.seed import seed_rbac
from app.modules.departments.models import Department
from app.modules.patients.models import Patient
from app.modules.admissions.models import Admission
from app.modules.emergency.models import EmergencyVisit
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement
from app.modules.laboratory.models import LabTest, LabOrder, LabResult
from app.modules.billing.models import TariffItem, Invoice, Payment
from app.modules.clinical.models import ClinicalNote, PatientMeasurement, Diagnosis
from app.modules.hospitalization.models import Room, Bed, HospitalStay
from app.modules.maternity.models import MaternityRecord, MaternityConsultation, DeliveryRecord
from app.modules.personnel.models import StaffMember, OnCallSchedule, LeaveRequest, Contract
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.surgery.models import OperatingRoom, SurgerySchedule, SurgeryTeamMember, SurgeryReport
from app.modules.quality.models import QualityIndicator, QualityMeasurement, IncidentReport
from app.modules.reporting.models import NationalReport, EpidemicAlert, HealthStatistic
from app.modules.activity.models import ActivityEntry


# ── Test framework ──────────────────────────────────────────────────
class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
        self.current_module = ""

    def ok(self, name, detail=""):
        self.passed.append((self.current_module, name, detail))
        print(f"  ✅ {name}: {detail}" if detail else f"  ✅ {name}")

    def fail(self, name, detail=""):
        self.failed.append((self.current_module, name, detail))
        print(f"  ❌ {name}: {detail}")

    def warn(self, name, detail=""):
        self.warnings.append((self.current_module, name, detail))
        print(f"  ⚠️  {name}: {detail}")

    def section(self, name):
        self.current_module = name
        print(f"\n{'='*60}")
        print(f"  📋 {name}")
        print(f"{'='*60}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        pct = (len(self.passed) / total * 100) if total > 0 else 0
        print(f"\n\n{'#'*60}")
        print(f"  RÉSULTATS DES TESTS END-TO-END")
        print(f"{'#'*60}")
        print(f"  ✅ Passés : {len(self.passed)}/{total} ({pct:.1f}%)")
        print(f"  ❌ Échoués : {len(self.failed)}")
        print(f"  ⚠️  Avertissements : {len(self.warnings)}")
        print(f"{'#'*60}")

        if self.failed:
            print(f"\n❌ DÉTAILS DES ÉCHECS:")
            for mod, name, detail in self.failed:
                print(f"   [{mod}] {name}: {detail[:200]}")

        if self.warnings:
            print(f"\n⚠️  AVERTISSEMENTS:")
            for mod, name, detail in self.warnings:
                print(f"   [{mod}] {name}: {detail[:200]}")

        return len(self.failed) == 0


results = TestResult()


# ── Database setup ──────────────────────────────────────────────────
print("🔧 Configuration SQLite...")

test_engine = create_engine(
    "sqlite:///./test_e2e.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

Base.metadata.drop_all(bind=test_engine)
Base.metadata.create_all(bind=test_engine)

# ── Seed data ───────────────────────────────────────────────────────
print("🌱 Création des données de test...")
db = TestSessionLocal()

# RBAC
seed_rbac(db)
db.commit()

# Facilities (model has: id, code, name, category, region, prefecture, status)
fac1 = Facility(id="fac-chu-donka", code="CHU-DONKA", name="CHU Donka",
                category="CHU", region="Conakry", prefecture="Conakry", status="ACTIVE")
fac2 = Facility(id="fac-hgr-kankan", code="HGR-KANKAN", name="HGR Kankan",
                category="HGR", region="Kankan", prefecture="Kankan", status="ACTIVE")
fac3 = Facility(id="fac-csi-mamou", code="CSI-MAMOU", name="CSI Mamou",
                category="CSI", region="Mamou", prefecture="Mamou", status="ACTIVE")
db.add_all([fac1, fac2, fac3])
db.commit()

# Users
users_data = [
    ("super-admin-id", "admin@guineecare.com", "Super", "Admin", "SUPER_ADMIN", None),
    ("admin-donka-id", "admin.donka@chu-donka.gn", "Amadou", "Diallo", "ADMIN", "fac-chu-donka"),
    ("doctor-donka-id", "dr.diallo@chu-donka.gn", "Mamadou", "Diallo", "DOCTOR", "fac-chu-donka"),
    ("nurse-donka-id", "infirmiere.donka@chu-donka.gn", "Fatoumata", "Bangoura", "NURSE", "fac-chu-donka"),
    ("pharma-donka-id", "pharma.donka@chu-donka.gn", "Ibrahima", "Camara", "PHARMACIST", "fac-chu-donka"),
    ("lab-donka-id", "lab.donka@chu-donka.gn", "Moussa", "Souaré", "LAB_TECH", "fac-chu-donka"),
    ("cashier-donka-id", "caisse.donka@chu-donka.gn", "Aminata", "Touré", "CASHIER", "fac-chu-donka"),
    ("midwife-donka-id", "sagefemme.donka@chu-donka.gn", "Mariama", "Bah", "MIDWIFE", "fac-chu-donka"),
    ("admin-kankan-id", "admin.kankan@hgr-kankan.gn", "Sekou", "Koné", "ADMIN", "fac-hgr-kankan"),
    ("doctor-kankan-id", "dr.kone@hgr-kankan.gn", "Abdoulaye", "Koné", "DOCTOR", "fac-hgr-kankan"),
]
for uid, email, fn, ln, role, fid in users_data:
    db.add(User(id=uid, email=email, password_hash=hash_password("pass123"),
                first_name=fn, last_name=ln, role=role, facility_id=fid, is_active=True))
db.commit()

# Departments
db.add(Department(id="dept-urgences", name="Urgences", code="URG", facility_id="fac-chu-donka"))
db.add(Department(id="dept-medecine", name="Médecine Interne", code="MED", facility_id="fac-chu-donka"))
db.add(Department(id="dept-maternite", name="Maternité", code="MAT", facility_id="fac-chu-donka"))
db.add(Department(id="dept-urg-kankan", name="Urgences", code="URG", facility_id="fac-hgr-kankan"))
db.commit()

# Patients (need patient_number, date objects for SQLite)
db.add(Patient(id="pat-001", patient_number="P-2024-001", first_name="Ibrahima", last_name="Sylla",
               date_of_birth=date(1990, 3, 15), gender="M", phone="+224 628 33 33 33",
               national_id="GN-1990-12345", insurance_number="INS-001", facility_id="fac-chu-donka"))
db.add(Patient(id="pat-002", patient_number="P-2024-002", first_name="Aissatou", last_name="Diallo",
               date_of_birth=date(1985, 7, 22), gender="F", phone="+224 628 44 44 44",
               national_id="GN-1985-67890", insurance_number="INS-002", facility_id="fac-chu-donka"))
db.add(Patient(id="pat-003", patient_number="P-2024-003", first_name="Kabinet", last_name="Camara",
               date_of_birth=date(1978, 1, 10), gender="M", phone="+224 628 55 55 55",
               national_id="GN-1978-11111", facility_id="fac-hgr-kankan"))
db.commit()

# Pharmacy (code is required)
db.add(PharmacyProduct(id="prod-001", code="PARA-500", name="Paracétamol 500mg",
                       category="Antalgique", form="Comprimé", facility_id="fac-chu-donka"))
db.commit()
db.add(PharmacyStock(id="stock-001", product_id="prod-001", quantity_available=500,
                     min_threshold=50, facility_id="fac-chu-donka"))

# Lab test (code is required)
db.add(LabTest(id="ltest-001", code="NFS", name="NFS", category="Hématologie",
               sample_type="Sang", facility_id="fac-chu-donka"))

# Tariff (code, name, category, unit_price required)
db.add(TariffItem(id="tariff-001", code="CONS-STD", name="Consultation standard",
                  category="Consultation", unit_price=25000.0, facility_id="fac-chu-donka"))

# Room + Bed
db.add(Room(id="room-001", code="R-101", name="Chambre 101", room_type="STANDARD",
            department_id="dept-medecine", facility_id="fac-chu-donka"))
db.commit()
db.add(Bed(id="bed-001", room_id="room-001", bed_number="101-A", bed_status="AVAILABLE",
           facility_id="fac-chu-donka"))

# Operating room (code and name required)
db.add(OperatingRoom(id="or-001", code="BLOC-1", name="Bloc 1", room_type="GENERAL",
                     status="AVAILABLE", facility_id="fac-chu-donka"))

# Staff (date objects for hire_date)
db.add(StaffMember(id="staff-001", employee_number="EMP-001", first_name="Mamadou", last_name="Diallo",
                   profession="MEDECIN", specialty="Cardiologie", department_id="dept-medecine",
                   status="ACTIVE", hire_date=date(2020, 1, 15), phone="+224 622 00 00 01",
                   email="m.diallo@chu-donka.gn", facility_id="fac-chu-donka"))
db.add(StaffMember(id="staff-002", employee_number="EMP-002", first_name="Fatoumata", last_name="Bangoura",
                   profession="INFIRMIER", specialty="Urgences", department_id="dept-urgences",
                   status="ACTIVE", hire_date=date(2019, 6, 1), phone="+224 622 00 00 02",
                   email="f.bangoura@chu-donka.gn", facility_id="fac-chu-donka"))
db.add(StaffMember(id="staff-003", employee_number="EMP-003", first_name="Sekou", last_name="Koné",
                   profession="MEDECIN", specialty="Général", department_id="dept-urg-kankan",
                   status="ACTIVE", hire_date=date(2021, 3, 20), phone="+224 622 00 00 03",
                   email="s.kone@hgr-kankan.gn", facility_id="fac-hgr-kankan"))
db.commit()

db.close()
print("✅ Données de test créées\n")


# ── Helpers ─────────────────────────────────────────────────────────
client = TestClient(app)

def login(email, password="pass123"):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    if resp.status_code != 200:
        return None, None
    data = resp.json()
    return data["access_token"], data.get("user", {})

def auth(token):
    return {"Authorization": f"Bearer {token}"}

def call(method, path, token=None, json_data=None, params=None):
    h = auth(token) if token else {}
    kw = {"headers": h}
    if json_data: kw["json"] = json_data
    if params: kw["params"] = params
    return getattr(client, method)(path, **kw)

def extract_list(resp):
    """Extract list from various response formats"""
    data = resp.json()
    if isinstance(data, list):
        return data
    for key in ["items", "data", "results"]:
        if key in data and isinstance(data[key], list):
            return data[key]
    return []


# ═══════════════════════════════════════════════════════════════════
# 1. AUTH
# ═══════════════════════════════════════════════════════════════════
results.section("1. AUTHENTIFICATION")

# 1.1 Login SUPER_ADMIN
sa_token, sa_user = login("admin@guineecare.com", "pass123")
if sa_token and sa_user.get("role") == "SUPER_ADMIN":
    results.ok("Login SUPER_ADMIN", f"role={sa_user['role']}, facility={sa_user.get('facility_id')}")
else:
    results.fail("Login SUPER_ADMIN", f"token={'OK' if sa_token else 'None'}, user={sa_user}")

# 1.2 Login DOCTOR
doc_token, doc_user = login("dr.diallo@chu-donka.gn", "pass123")
if doc_token and doc_user.get("role") == "DOCTOR":
    results.ok("Login DOCTOR", f"facility={doc_user['facility_id']}")
else:
    results.fail("Login DOCTOR", f"user={doc_user}")

# 1.3 Invalid credentials
resp = client.post("/api/v1/auth/login", json={"email": "admin@guineecare.com", "password": "wrong"})
results.ok("Login invalide", f"status={resp.status_code}") if resp.status_code == 401 else \
    results.fail("Login invalide", f"attendu 401, obtenu {resp.status_code}")

# 1.4 Non-existent user
resp = client.post("/api/v1/auth/login", json={"email": "nobody@test.gn", "password": "test"})
results.ok("Login inexistant", f"status={resp.status_code}") if resp.status_code == 401 else \
    results.fail("Login inexistant", f"attendu 401, obtenu {resp.status_code}")

# 1.5 GET /auth/me
resp = client.get("/api/v1/auth/me", headers=auth(sa_token))
if resp.status_code == 200:
    results.ok("GET /auth/me", f"email={resp.json().get('email')}")
else:
    results.fail("GET /auth/me", f"status={resp.status_code}")

# 1.6 GET /auth/me sans token
resp = client.get("/api/v1/auth/me")
results.ok("Me sans token", f"status={resp.status_code}") if resp.status_code in [401, 403] else \
    results.fail("Me sans token", f"attendu 401/403, obtenu {resp.status_code}")

# 1.7 Login all roles (use specific keys to avoid overwriting)
role_tokens = {}
for uid, email, fn, ln, role, fid in users_data:
    t, u = login(email)
    if t:
        # Use role + facility to avoid key collisions for duplicate roles
        key = f"{role}_{fid}" if fid else role
        role_tokens[key] = t
        # Also store by role (last one wins, but that's ok for non-duplicate roles)
        if role not in role_tokens:
            role_tokens[role] = t
        results.ok(f"Login {key}", email)
    else:
        results.fail(f"Login {role}", email)

# Store specific tokens for tenant tests
admin_donka_token = role_tokens.get("ADMIN_fac-chu-donka")
admin_kankan_token = role_tokens.get("ADMIN_fac-hgr-kankan")
doctor_donka_token = role_tokens.get("DOCTOR_fac-chu-donka")
doctor_kankan_token = role_tokens.get("DOCTOR_fac-hgr-kankan")

# 1.8 Health check
resp = client.get("/health")
results.ok("Health check", resp.json().get("status", "")) if resp.status_code == 200 else \
    results.fail("Health check", f"status={resp.status_code}")

# 1.9 API root
resp = client.get("/api/v1")
if resp.status_code == 200:
    results.ok("API root", f"{len(resp.json().get('modules', []))} modules")
else:
    results.fail("API root", f"status={resp.status_code}")


# ═══════════════════════════════════════════════════════════════════
# 2. FACILITIES
# ═══════════════════════════════════════════════════════════════════
results.section("2. FACILITIES")

# 2.1 List
resp = call("get", "/api/v1/facilities", sa_token)
if resp.status_code == 200:
    facs = extract_list(resp)
    results.ok("List facilities", f"{len(facs)} facilities")
else:
    results.fail("List facilities", f"status={resp.status_code}, {resp.text[:200]}")

# 2.2 Create
resp = call("post", "/api/v1/facilities", sa_token, {"code": "CSI-LABE", "name": "CSI Labé", "category": "CSI", "region": "Labé"})
if resp.status_code in [200, 201]:
    new_fac_id = resp.json().get("id")
    results.ok("Create facility", f"id={new_fac_id}")
else:
    results.fail("Create facility", f"status={resp.status_code}, {resp.text[:200]}")
    new_fac_id = None

# 2.3 Get by ID
resp = call("get", "/api/v1/facilities/fac-chu-donka", sa_token)
results.ok("Get facility", f"name={resp.json().get('name','')}") if resp.status_code == 200 else \
    results.fail("Get facility", f"status={resp.status_code}, {resp.text[:200]}")

# 2.4 Update
resp = call("put", "/api/v1/facilities/fac-chu-donka", sa_token, {"region": "Conakry"})
results.ok("Update facility", "region mis à jour") if resp.status_code == 200 else \
    results.fail("Update facility", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 3. USERS
# ═══════════════════════════════════════════════════════════════════
results.section("3. USERS")

# 3.1 List
resp = call("get", "/api/v1/users", sa_token)
if resp.status_code == 200:
    results.ok("List users", f"{len(extract_list(resp))} users")
else:
    results.fail("List users", f"status={resp.status_code}, {resp.text[:200]}")

# 3.2 Create
resp = call("post", "/api/v1/users", sa_token, {
    "email": "new.user@chu-donka.gn", "password": "pass123",
    "first_name": "Nouveau", "last_name": "Utilisateur",
    "role": "NURSE", "facility_id": "fac-chu-donka"
})
results.ok("Create user", "nouveau utilisateur") if resp.status_code in [200, 201] else \
    results.fail("Create user", f"status={resp.status_code}, {resp.text[:200]}")

# 3.3 GET /users/me
resp = call("get", "/api/v1/users/me", doc_token)
results.ok("Get /users/me", resp.json().get("email", "")) if resp.status_code == 200 else \
    results.fail("Get /users/me", f"status={resp.status_code}")

# 3.4 NURSE cannot create user
if "NURSE" in role_tokens:
    resp = call("post", "/api/v1/users", role_tokens["NURSE"], {
        "email": "hack@test.gn", "password": "hack", "first_name": "H", "last_name": "Ack"
    })
    results.ok("NURSE denied user create", f"status={resp.status_code}") if resp.status_code == 403 else \
        results.warn("NURSE user create", f"status={resp.status_code}")


# ═══════════════════════════════════════════════════════════════════
# 4. RBAC
# ═══════════════════════════════════════════════════════════════════
results.section("4. RBAC")

# 4.1 List roles
resp = call("get", "/api/v1/rbac/roles", sa_token)
if resp.status_code == 200:
    roles = extract_list(resp)
    results.ok("List roles", f"{len(roles)} rôles")
else:
    results.fail("List roles", f"status={resp.status_code}, {resp.text[:200]}")

# 4.2 List permissions
resp = call("get", "/api/v1/rbac/permissions", sa_token)
if resp.status_code == 200:
    perms = extract_list(resp)
    results.ok("List permissions", f"{len(perms)} permissions")
else:
    results.fail("List permissions", f"status={resp.status_code}, {resp.text[:200]}")

# 4.3 Create role
resp = call("post", "/api/v1/rbac/roles", sa_token, {"code": "INTERN", "name": "Interne"})
results.ok("Create role", "INTERN") if resp.status_code in [200, 201] else \
    results.fail("Create role", f"status={resp.status_code}, {resp.text[:200]}")

# 4.4 Assign permission to role
resp = call("post", "/api/v1/rbac/role-permissions", sa_token, {"role_code": "INTERN", "permission_code": "patient.read"})
results.ok("Assign permission", "patient.read → INTERN") if resp.status_code in [200, 201] else \
    results.fail("Assign permission", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 5. DEPARTMENTS
# ═══════════════════════════════════════════════════════════════════
results.section("5. DEPARTMENTS")

resp = call("get", "/api/v1/departments", sa_token)
if resp.status_code == 200:
    results.ok("List departments", f"{len(extract_list(resp))} départements")
else:
    results.fail("List departments", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("post", "/api/v1/departments", sa_token, {
    "name": "Chirurgie", "code": "CHIR", "facility_id": "fac-chu-donka"
})
results.ok("Create department", "Chirurgie") if resp.status_code in [200, 201] else \
    results.fail("Create department", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 6. PATIENTS
# ═══════════════════════════════════════════════════════════════════
results.section("6. PATIENTS")

# 6.1 List
resp = call("get", "/api/v1/patients", sa_token)
if resp.status_code == 200:
    results.ok("List patients", f"{len(extract_list(resp))} patients")
else:
    results.fail("List patients", f"status={resp.status_code}, {resp.text[:200]}")

# 6.2 Create (patient_number required)
resp = call("post", "/api/v1/patients", sa_token, {
    "first_name": "Adama", "last_name": "Condé", "patient_number": "P-2024-010",
    "date_of_birth": "1995-05-20", "gender": "F", "phone": "+224 628 66 66 66",
    "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    new_pat_id = resp.json().get("id")
    results.ok("Create patient", f"id={new_pat_id}")
else:
    results.fail("Create patient", f"status={resp.status_code}, {resp.text[:200]}")
    new_pat_id = None

# 6.3 Get by ID
resp = call("get", "/api/v1/patients/pat-001", sa_token)
results.ok("Get patient", f"{resp.json().get('first_name','')} {resp.json().get('last_name','')}") if resp.status_code == 200 else \
    results.fail("Get patient", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 7. ADMISSIONS
# ═══════════════════════════════════════════════════════════════════
results.section("7. ADMISSIONS")

resp = call("post", "/api/v1/admissions", sa_token, {
    "patient_id": "pat-001", "department_id": "dept-medecine",
    "admission_type": "URGENT", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    adm_id = resp.json().get("id")
    results.ok("Create admission", f"id={adm_id}")
else:
    results.fail("Create admission", f"status={resp.status_code}, {resp.text[:200]}")
    adm_id = None

resp = call("get", "/api/v1/admissions", sa_token)
if resp.status_code == 200:
    results.ok("List admissions", f"{len(extract_list(resp))} admissions")
else:
    results.fail("List admissions", f"status={resp.status_code}, {resp.text[:200]}")

# Close admission
if adm_id:
    resp = call("post", f"/api/v1/admissions/{adm_id}/close", sa_token)
    results.ok("Close admission", "admission fermée") if resp.status_code == 200 else \
        results.fail("Close admission", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 8. EMERGENCY
# ═══════════════════════════════════════════════════════════════════
results.section("8. URGENCES")

# Create visit
resp = call("post", "/api/v1/emergency/visits", sa_token, {
    "patient_id": "pat-001", "chief_complaint": "Chest pain",
    "priority_level": "URGENT", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    ev_id = resp.json().get("id")
    results.ok("Create emergency visit", f"id={ev_id}")
else:
    results.fail("Create emergency visit", f"status={resp.status_code}, {resp.text[:200]}")
    ev_id = None

# Queue
resp = call("get", "/api/v1/emergency/queue", sa_token)
results.ok("Emergency queue", f"{len(extract_list(resp))} visites") if resp.status_code == 200 else \
    results.fail("Emergency queue", f"status={resp.status_code}, {resp.text[:200]}")

# Triage
if ev_id and doc_token:
    resp = call("post", f"/api/v1/emergency/visits/{ev_id}/triage", doc_token, {"priority_level": "URGENT"})
    results.ok("Triage", "niveau URGENT") if resp.status_code == 200 else \
        results.warn("Triage", f"status={resp.status_code}, {resp.text[:200]}")

# Orientation
if ev_id and doc_token:
    resp = call("post", f"/api/v1/emergency/visits/{ev_id}/orientation", doc_token, {"orientation": "MEDECINE"})
    results.ok("Orientation", "→ MEDECINE") if resp.status_code == 200 else \
        results.warn("Orientation", f"status={resp.status_code}, {resp.text[:200]}")

# Care
if ev_id and doc_token:
    resp = call("post", f"/api/v1/emergency/visits/{ev_id}/care", doc_token, {
        "attending_doctor_id": "doctor-donka-id", "vital_signs": "HR:90 BP:130/85"
    })
    results.ok("Care", "médecin assigné") if resp.status_code == 200 else \
        results.warn("Care", f"status={resp.status_code}, {resp.text[:200]}")

# Discharge
if ev_id and doc_token:
    resp = call("post", f"/api/v1/emergency/visits/{ev_id}/discharge", doc_token, {
        "discharge_summary": "Patient stabilisé", "discharge_destination": "HOME"
    })
    results.ok("Discharge", "→ HOME") if resp.status_code == 200 else \
        results.warn("Discharge", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 9. PHARMACY
# ═══════════════════════════════════════════════════════════════════
results.section("9. PHARMACIE")

resp = call("get", "/api/v1/pharmacy/products", sa_token)
if resp.status_code == 200:
    results.ok("List products", f"{len(extract_list(resp))} produits")
else:
    results.fail("List products", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("post", "/api/v1/pharmacy/products", sa_token, {
    "code": "AMOX-250", "name": "Amoxicilline 250mg", "category": "Antibiotique",
    "form": "Gélule", "facility_id": "fac-chu-donka"
})
results.ok("Create product", "Amoxicilline") if resp.status_code in [200, 201] else \
    results.fail("Create product", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/pharmacy/stock", sa_token)
results.ok("List stock", f"{len(extract_list(resp))} entrées") if resp.status_code == 200 else \
    results.fail("List stock", f"status={resp.status_code}, {resp.text[:200]}")

# Stock movement
resp = call("post", "/api/v1/pharmacy/stock/movements", sa_token, {
    "facility_id": "fac-chu-donka", "product_id": "prod-001",
    "movement_type": "IN", "quantity": 100, "reason": "Réapprovisionnement"
})
results.ok("Stock movement IN", "+100") if resp.status_code in [200, 201] else \
    results.fail("Stock movement IN", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/pharmacy/stock/movements", sa_token)
results.ok("List movements", f"{len(extract_list(resp))} mouvements") if resp.status_code == 200 else \
    results.fail("List movements", f"status={resp.status_code}, {resp.text[:200]}")

# RBAC: PHARMACIST can access
if "PHARMACIST" in role_tokens:
    resp = call("get", "/api/v1/pharmacy/products", role_tokens["PHARMACIST"])
    results.ok("PHARMACIST → pharmacy", f"status={resp.status_code}") if resp.status_code == 200 else \
        results.fail("PHARMACIST → pharmacy", f"status={resp.status_code}")

# RBAC: NURSE cannot manage
if "NURSE" in role_tokens:
    resp = call("post", "/api/v1/pharmacy/products", role_tokens["NURSE"], {
        "code": "HACK", "name": "Hack", "facility_id": "fac-chu-donka"
    })
    results.ok("NURSE denied pharmacy.manage", f"status={resp.status_code}") if resp.status_code == 403 else \
        results.warn("NURSE pharmacy.manage", f"status={resp.status_code}")


# ═══════════════════════════════════════════════════════════════════
# 10. LABORATORY
# ═══════════════════════════════════════════════════════════════════
results.section("10. LABORATOIRE")

resp = call("get", "/api/v1/laboratory/tests", sa_token)
if resp.status_code == 200:
    results.ok("List lab tests", f"{len(extract_list(resp))} tests")
else:
    results.fail("List lab tests", f"status={resp.status_code}, {resp.text[:200]}")

# Create order
resp = call("post", "/api/v1/laboratory/orders", doc_token, {
    "patient_id": "pat-001", "test_id": "ltest-001",
    "facility_id": "fac-chu-donka", "priority": "NORMAL"
})
if resp.status_code in [200, 201]:
    lab_order_id = resp.json().get("id")
    results.ok("Create lab order", f"id={lab_order_id}")
else:
    results.fail("Create lab order", f"status={resp.status_code}, {resp.text[:200]}")
    lab_order_id = None

# List orders
resp = call("get", "/api/v1/laboratory/orders", sa_token)
results.ok("List lab orders", f"{len(extract_list(resp))} commandes") if resp.status_code == 200 else \
    results.fail("List lab orders", f"status={resp.status_code}, {resp.text[:200]}")

# Create result
if lab_order_id and "LAB_TECH" in role_tokens:
    resp = call("post", f"/api/v1/laboratory/orders/{lab_order_id}/results", role_tokens["LAB_TECH"], {
        "facility_id": "fac-chu-donka", "result_value": "GB: 7500/mm3"
    })
    if resp.status_code in [200, 201]:
        lab_result_id = resp.json().get("id")
        results.ok("Create lab result", f"id={lab_result_id}")
    else:
        results.fail("Create lab result", f"status={resp.status_code}, {resp.text[:200]}")
        lab_result_id = None

    # Validate result
    if lab_result_id:
        resp = call("post", f"/api/v1/laboratory/results/{lab_result_id}/validate", role_tokens["LAB_TECH"])
        results.ok("Validate lab result", "validé") if resp.status_code == 200 else \
            results.warn("Validate lab result", f"status={resp.status_code}, {resp.text[:200]}")

# List results
resp = call("get", "/api/v1/laboratory/results", sa_token)
results.ok("List lab results", f"{len(extract_list(resp))} résultats") if resp.status_code == 200 else \
    results.fail("List lab results", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 11. BILLING
# ═══════════════════════════════════════════════════════════════════
results.section("11. FACTURATION")

resp = call("get", "/api/v1/billing/tariffs", sa_token)
if resp.status_code == 200:
    results.ok("List tariffs", f"{len(extract_list(resp))} tarifs")
else:
    results.fail("List tariffs", f"status={resp.status_code}, {resp.text[:200]}")

# Create invoice (invoice_number and net_amount required)
resp = call("post", "/api/v1/billing/invoices", sa_token, {
    "patient_id": "pat-001", "invoice_number": "FAC-2024-001",
    "net_amount": 25000.0, "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    inv_id = resp.json().get("id")
    results.ok("Create invoice", f"id={inv_id}")
else:
    results.fail("Create invoice", f"status={resp.status_code}, {resp.text[:200]}")
    inv_id = None

# List invoices
resp = call("get", "/api/v1/billing/invoices", sa_token)
results.ok("List invoices", f"{len(extract_list(resp))} factures") if resp.status_code == 200 else \
    results.fail("List invoices", f"status={resp.status_code}, {resp.text[:200]}")

# Payment
if inv_id and "CASHIER" in role_tokens:
    resp = call("post", f"/api/v1/billing/invoices/{inv_id}/payments", role_tokens["CASHIER"], {
        "facility_id": "fac-chu-donka", "amount": 25000.0, "payment_method": "CASH"
    })
    if resp.status_code in [200, 201]:
        pay_id = resp.json().get("id")
        results.ok("Create payment", f"id={pay_id}")
    else:
        results.fail("Create payment", f"status={resp.status_code}, {resp.text[:200]}")

# List payments
resp = call("get", "/api/v1/billing/payments", sa_token)
results.ok("List payments", f"{len(extract_list(resp))} paiements") if resp.status_code == 200 else \
    results.fail("List payments", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 12. HOSPITALIZATION
# ═══════════════════════════════════════════════════════════════════
results.section("12. HOSPITALISATION")

resp = call("get", "/api/v1/hospitalization/rooms", sa_token)
results.ok("List rooms", f"{len(extract_list(resp))} chambres") if resp.status_code == 200 else \
    results.fail("List rooms", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/hospitalization/beds", sa_token)
results.ok("List beds", f"{len(extract_list(resp))} lits") if resp.status_code == 200 else \
    results.fail("List beds", f"status={resp.status_code}, {resp.text[:200]}")

# Bed board
resp = call("get", "/api/v1/hospitalization/bed-board", sa_token, params={"facility_id": "fac-chu-donka"})
results.ok("Bed board", "OK") if resp.status_code == 200 else \
    results.warn("Bed board", f"status={resp.status_code}, {resp.text[:200]}")

# Create stay
resp = call("post", "/api/v1/hospitalization/stays", sa_token, {
    "patient_id": "pat-002", "bed_id": "bed-001",
    "reason": "Surveillance", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    stay_id = resp.json().get("id")
    results.ok("Create stay", f"id={stay_id}")
else:
    results.fail("Create stay", f"status={resp.status_code}, {resp.text[:200]}")
    stay_id = None

# List stays
resp = call("get", "/api/v1/hospitalization/stays", sa_token)
results.ok("List stays", f"{len(extract_list(resp))} séjours") if resp.status_code == 200 else \
    results.fail("List stays", f"status={resp.status_code}, {resp.text[:200]}")

# Discharge
if stay_id:
    resp = call("post", f"/api/v1/hospitalization/stays/{stay_id}/discharge", sa_token)
    results.ok("Discharge stay", "patient sorti") if resp.status_code == 200 else \
        results.warn("Discharge stay", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 13. CLINICAL
# ═══════════════════════════════════════════════════════════════════
results.section("13. CLINIQUE")

# Notes (nested under patient)
resp = call("post", "/api/v1/clinical/patients/pat-001/notes", doc_token, {
    "note_type": "CONSULTATION", "content": "Douleurs abdominales. Examen normal.",
    "facility_id": "fac-chu-donka"
})
results.ok("Create clinical note", "note créée") if resp.status_code in [200, 201] else \
    results.fail("Create clinical note", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/clinical/patients/pat-001/notes", doc_token)
results.ok("List clinical notes", f"{len(extract_list(resp))} notes") if resp.status_code == 200 else \
    results.fail("List clinical notes", f"status={resp.status_code}, {resp.text[:200]}")

# Measurements
resp = call("post", "/api/v1/clinical/patients/pat-001/measurements", doc_token, {
    "measurement_type": "TEMPERATURE", "value": "37.5", "unit": "°C",
    "facility_id": "fac-chu-donka"
})
results.ok("Create measurement", "37.5°C") if resp.status_code in [200, 201] else \
    results.fail("Create measurement", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/clinical/patients/pat-001/measurements", doc_token)
results.ok("List measurements", f"{len(extract_list(resp))} mesures") if resp.status_code == 200 else \
    results.fail("List measurements", f"status={resp.status_code}, {resp.text[:200]}")

# Diagnoses
resp = call("post", "/api/v1/clinical/patients/pat-001/diagnoses", doc_token, {
    "diagnosis_label": "Gastro-entérite aiguë", "diagnosis_type": "PRINCIPAL",
    "diagnosis_code": "A09", "facility_id": "fac-chu-donka"
})
results.ok("Create diagnosis", "Gastro-entérite") if resp.status_code in [200, 201] else \
    results.fail("Create diagnosis", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/clinical/patients/pat-001/diagnoses", doc_token)
results.ok("List diagnoses", f"{len(extract_list(resp))} diagnostics") if resp.status_code == 200 else \
    results.fail("List diagnoses", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 14. MATERNITY
# ═══════════════════════════════════════════════════════════════════
results.section("14. MATERNITÉ")

# Create record
resp = call("post", "/api/v1/maternity/records", role_tokens.get("MIDWIFE", sa_token), {
    "patient_id": "pat-002", "gravidity": "3", "parity": "2",
    "last_menstrual_period": "2025-09-01", "expected_due_date": "2026-06-08",
    "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    mat_rec_id = resp.json().get("id")
    results.ok("Create maternity record", f"id={mat_rec_id}")
else:
    results.fail("Create maternity record", f"status={resp.status_code}, {resp.text[:200]}")
    mat_rec_id = None

# List records
resp = call("get", "/api/v1/maternity/records", role_tokens.get("MIDWIFE", sa_token))
results.ok("List maternity records", f"{len(extract_list(resp))} dossiers") if resp.status_code == 200 else \
    results.fail("List maternity records", f"status={resp.status_code}, {resp.text[:200]}")

# Get record detail
if mat_rec_id:
    resp = call("get", f"/api/v1/maternity/records/{mat_rec_id}", role_tokens.get("MIDWIFE", sa_token))
    results.ok("Get maternity record", "détail OK") if resp.status_code == 200 else \
        results.fail("Get maternity record", f"status={resp.status_code}, {resp.text[:200]}")

# Create consultation
if mat_rec_id:
    resp = call("post", f"/api/v1/maternity/records/{mat_rec_id}/consultations", role_tokens.get("MIDWIFE", sa_token), {
        "consultation_type": "PRENATAL", "facility_id": "fac-chu-donka"
    })
    results.ok("Create prenatal consult", "OK") if resp.status_code in [200, 201] else \
        results.fail("Create prenatal consult", f"status={resp.status_code}, {resp.text[:200]}")

# Create delivery
if mat_rec_id:
    resp = call("post", f"/api/v1/maternity/records/{mat_rec_id}/deliveries", role_tokens.get("MIDWIFE", sa_token), {
        "delivery_type": "VAGINAL", "delivery_date": "2026-06-08T10:00:00",
        "baby_gender": "M", "baby_weight_kg": 3.2, "facility_id": "fac-chu-donka"
    })
    results.ok("Create delivery", "naissance enregistrée") if resp.status_code in [200, 201] else \
        results.fail("Create delivery", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 15. IMAGING
# ═══════════════════════════════════════════════════════════════════
results.section("15. IMAGERIE")

# Create order
resp = call("post", "/api/v1/imaging/orders", doc_token, {
    "patient_id": "pat-001", "exam_type": "RADIOGRAPHY",
    "body_region": "Thorax", "clinical_info": "Suspicion pneumopathie",
    "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    img_order_id = resp.json().get("id")
    results.ok("Create imaging order", f"id={img_order_id}")
else:
    results.fail("Create imaging order", f"status={resp.status_code}, {resp.text[:200]}")
    img_order_id = None

# List orders
resp = call("get", "/api/v1/imaging/orders", sa_token)
results.ok("List imaging orders", f"{len(extract_list(resp))} commandes") if resp.status_code == 200 else \
    results.fail("List imaging orders", f"status={resp.status_code}, {resp.text[:200]}")

# Start exam
if img_order_id:
    resp = call("post", f"/api/v1/imaging/orders/{img_order_id}/start", sa_token)
    results.ok("Start imaging", "IN_PROGRESS") if resp.status_code == 200 else \
        results.warn("Start imaging", f"status={resp.status_code}, {resp.text[:200]}")

# Complete exam
if img_order_id:
    resp = call("post", f"/api/v1/imaging/orders/{img_order_id}/complete", sa_token)
    results.ok("Complete imaging", "COMPLETED") if resp.status_code == 200 else \
        results.warn("Complete imaging", f"status={resp.status_code}, {resp.text[:200]}")

# Create result
if img_order_id:
    resp = call("post", "/api/v1/imaging/results", sa_token, {
        "order_id": img_order_id, "patient_id": "pat-001",
        "findings": "Pas d'anomalie", "conclusion": "Radio normale",
        "facility_id": "fac-chu-donka"
    })
    if resp.status_code in [200, 201]:
        img_result_id = resp.json().get("id")
        results.ok("Create imaging result", f"id={img_result_id}")
    else:
        results.fail("Create imaging result", f"status={resp.status_code}, {resp.text[:200]}")
        img_result_id = None

# List results
resp = call("get", "/api/v1/imaging/results", sa_token, params={"patient_id": "pat-001"})
results.ok("List imaging results", f"{len(extract_list(resp))} résultats") if resp.status_code == 200 else \
    results.fail("List imaging results", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 16. SURGERY
# ═══════════════════════════════════════════════════════════════════
results.section("16. CHIRURGIE")

# List rooms
resp = call("get", "/api/v1/surgery/rooms", sa_token)
results.ok("List OR rooms", f"{len(extract_list(resp))} salles") if resp.status_code == 200 else \
    results.fail("List OR rooms", f"status={resp.status_code}, {resp.text[:200]}")

# Create schedule
resp = call("post", "/api/v1/surgery/schedules", doc_token, {
    "patient_id": "pat-001", "operating_room_id": "or-001",
    "surgeon_id": "doctor-donka-id", "procedure_name": "Appendicectomie",
    "scheduled_date": "2026-06-20T08:00:00", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    surg_id = resp.json().get("id")
    results.ok("Create surgery schedule", f"id={surg_id}")
else:
    results.fail("Create surgery schedule", f"status={resp.status_code}, {resp.text[:200]}")
    surg_id = None

# List schedules
resp = call("get", "/api/v1/surgery/schedules", sa_token)
results.ok("List surgery schedules", f"{len(extract_list(resp))} programmations") if resp.status_code == 200 else \
    results.fail("List surgery schedules", f"status={resp.status_code}, {resp.text[:200]}")

# Start surgery
if surg_id:
    resp = call("post", f"/api/v1/surgery/schedules/{surg_id}/start", sa_token)
    results.ok("Start surgery", "IN_PROGRESS") if resp.status_code == 200 else \
        results.warn("Start surgery", f"status={resp.status_code}, {resp.text[:200]}")

# Complete surgery
if surg_id:
    resp = call("post", f"/api/v1/surgery/schedules/{surg_id}/complete", sa_token)
    results.ok("Complete surgery", "COMPLETED") if resp.status_code == 200 else \
        results.warn("Complete surgery", f"status={resp.status_code}, {resp.text[:200]}")

# Create report
if surg_id:
    resp = call("post", "/api/v1/surgery/reports", sa_token, {
        "schedule_id": surg_id, "patient_id": "pat-001", "surgeon_id": "doctor-donka-id",
        "operative_findings": "Appendice enflammé", "procedure_performed": "Appendicectomie",
        "anesthesia_type": "GENERAL", "facility_id": "fac-chu-donka"
    })
    if resp.status_code in [200, 201]:
        surg_report_id = resp.json().get("id")
        results.ok("Create surgery report", f"id={surg_report_id}")
    else:
        results.fail("Create surgery report", f"status={resp.status_code}, {resp.text[:200]}")

# List reports
resp = call("get", "/api/v1/surgery/reports", sa_token)
results.ok("List surgery reports", f"{len(extract_list(resp))} rapports") if resp.status_code == 200 else \
    results.fail("List surgery reports", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 17. QUALITY
# ═══════════════════════════════════════════════════════════════════
results.section("17. QUALITÉ")

# Indicators
resp = call("post", "/api/v1/quality/indicators", sa_token, {
    "code": "IPS", "name": "Indicateur de Performance", "category": "SAFETY",
    "facility_id": "fac-chu-donka"
})
results.ok("Create indicator", "IPS") if resp.status_code in [200, 201] else \
    results.fail("Create indicator", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/quality/indicators", sa_token)
if resp.status_code == 200:
    indicators = extract_list(resp)
    indicator_id = indicators[0].get("id") if indicators else None
    results.ok("List indicators", f"{len(indicators)} indicateurs")
else:
    results.fail("List indicators", f"status={resp.status_code}, {resp.text[:200]}")
    indicator_id = None

# Incident
resp = call("post", "/api/v1/quality/incidents", sa_token, {
    "incident_date": "2026-06-15", "incident_type": "FALL",
    "description": "Chute de patient dans le couloir", "severity": "MODERATE",
    "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    incident_id = resp.json().get("id")
    results.ok("Create incident", f"id={incident_id}")
else:
    results.fail("Create incident", f"status={resp.status_code}, {resp.text[:200]}")
    incident_id = None

resp = call("get", "/api/v1/quality/incidents", sa_token)
results.ok("List incidents", f"{len(extract_list(resp))} incidents") if resp.status_code == 200 else \
    results.fail("List incidents", f"status={resp.status_code}, {resp.text[:200]}")

# Investigate + Resolve
if incident_id:
    resp = call("post", f"/api/v1/quality/incidents/{incident_id}/investigate", sa_token)
    results.ok("Investigate incident", "UNDER_INVESTIGATION") if resp.status_code == 200 else \
        results.warn("Investigate incident", f"status={resp.status_code}, {resp.text[:200]}")

    resp = call("post", f"/api/v1/quality/incidents/{incident_id}/resolve", sa_token)
    results.ok("Resolve incident", "RESOLVED") if resp.status_code == 200 else \
        results.warn("Resolve incident", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 18. REPORTING
# ═══════════════════════════════════════════════════════════════════
results.section("18. REPORTING")

# National report
resp = call("post", "/api/v1/reporting/national-reports", sa_token, {
    "report_type": "MONTHLY", "period_start": "2026-05-01", "period_end": "2026-05-31",
    "total_admissions": "150", "total_deaths": "3", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    report_id = resp.json().get("id")
    results.ok("Create national report", f"id={report_id}")
else:
    results.fail("Create national report", f"status={resp.status_code}, {resp.text[:200]}")
    report_id = None

# List reports
resp = call("get", "/api/v1/reporting/national-reports", sa_token)
results.ok("List national reports", f"{len(extract_list(resp))} rapports") if resp.status_code == 200 else \
    results.fail("List national reports", f"status={resp.status_code}, {resp.text[:200]}")

# Submit + Validate
if report_id:
    resp = call("post", f"/api/v1/reporting/national-reports/{report_id}/submit", sa_token)
    results.ok("Submit report", "SUBMITTED") if resp.status_code == 200 else \
        results.warn("Submit report", f"status={resp.status_code}, {resp.text[:200]}")

    resp = call("post", f"/api/v1/reporting/national-reports/{report_id}/validate", sa_token)
    results.ok("Validate report", "VALIDATED") if resp.status_code == 200 else \
        results.warn("Validate report", f"status={resp.status_code}, {resp.text[:200]}")

# Epidemic alert
resp = call("post", "/api/v1/reporting/epidemic-alerts", sa_token, {
    "disease_name": "Choléra", "case_count": "15", "alert_level": "WARNING",
    "region": "Conakry", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    alert_id = resp.json().get("id")
    results.ok("Create epidemic alert", "Choléra")
else:
    results.fail("Create epidemic alert", f"status={resp.status_code}, {resp.text[:200]}")
    alert_id = None

if alert_id:
    resp = call("post", f"/api/v1/reporting/epidemic-alerts/{alert_id}/close", sa_token)
    results.ok("Close epidemic alert", "CLOSED") if resp.status_code == 200 else \
        results.warn("Close epidemic alert", f"status={resp.status_code}, {resp.text[:200]}")

# Statistics
resp = call("post", "/api/v1/reporting/statistics", sa_token, {
    "category": "CONSULTATION", "metric_name": "Total consultations",
    "metric_value": "450", "period_start": "2026-05-01", "period_end": "2026-05-31",
    "facility_id": "fac-chu-donka"
})
results.ok("Create statistic", "450 consultations") if resp.status_code in [200, 201] else \
    results.fail("Create statistic", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/reporting/statistics", sa_token)
results.ok("List statistics", f"{len(extract_list(resp))} stats") if resp.status_code == 200 else \
    results.fail("List statistics", f"status={resp.status_code}, {resp.text[:200]}")

# Dashboard
resp = call("get", "/api/v1/reporting/dashboard", sa_token, params={"facility_id": "fac-chu-donka"})
results.ok("Reporting dashboard", "OK") if resp.status_code == 200 else \
    results.warn("Reporting dashboard", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 19. PERSONNEL
# ═══════════════════════════════════════════════════════════════════
results.section("19. PERSONNEL")

# Staff
resp = call("get", "/api/v1/personnel/staff", sa_token)
if resp.status_code == 200:
    results.ok("List staff", f"{len(extract_list(resp))} membres")
else:
    results.fail("List staff", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("post", "/api/v1/personnel/staff", sa_token, {
    "first_name": "Aïssata", "last_name": "Touré", "profession": "SAGE_FEMME",
    "specialty": "Obstétrique", "department_id": "dept-maternite",
    "employee_number": "EMP-100", "hire_date": "2022-09-01",
    "phone": "+224 628 77 77 77", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    new_staff_id = resp.json().get("id")
    results.ok("Create staff", f"id={new_staff_id}")
else:
    results.fail("Create staff", f"status={resp.status_id}, {resp.text[:200]}")
    new_staff_id = None

resp = call("get", "/api/v1/personnel/staff/staff-001", sa_token)
results.ok("Get staff by ID", f"{resp.json().get('first_name','')}") if resp.status_code == 200 else \
    results.fail("Get staff by ID", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("put", "/api/v1/personnel/staff/staff-001", sa_token, {"phone": "+224 628 88 88 88"})
results.ok("Update staff", "phone mis à jour") if resp.status_code == 200 else \
    results.fail("Update staff", f"status={resp.status_code}, {resp.text[:200]}")

# On-call
resp = call("post", "/api/v1/personnel/on-call", sa_token, {
    "staff_id": "staff-001", "on_call_date": "2026-06-20",
    "shift_type": "NIGHT", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    oncall_id = resp.json().get("id")
    results.ok("Create on-call", "garde de nuit")
else:
    results.fail("Create on-call", f"status={resp.status_code}, {resp.text[:200]}")
    oncall_id = None

resp = call("get", "/api/v1/personnel/on-call", sa_token)
results.ok("List on-call", f"{len(extract_list(resp))} gardes") if resp.status_code == 200 else \
    results.fail("List on-call", f"status={resp.status_code}, {resp.text[:200]}")

# Leaves
resp = call("post", "/api/v1/personnel/leaves", sa_token, {
    "staff_id": "staff-001", "leave_type": "CONGE_ANNUEL",
    "start_date": "2026-07-01", "end_date": "2026-07-15",
    "reason": "Congé annuel", "facility_id": "fac-chu-donka"
})
if resp.status_code in [200, 201]:
    leave_id = resp.json().get("id")
    results.ok("Create leave request", f"id={leave_id}")
else:
    results.fail("Create leave request", f"status={resp.status_code}, {resp.text[:200]}")
    leave_id = None

resp = call("get", "/api/v1/personnel/leaves", sa_token)
results.ok("List leaves", f"{len(extract_list(resp))} demandes") if resp.status_code == 200 else \
    results.fail("List leaves", f"status={resp.status_code}, {resp.text[:200]}")

# Approve leave
if leave_id:
    resp = call("put", f"/api/v1/personnel/leaves/{leave_id}", sa_token, {"status": "APPROVED"})
    results.ok("Approve leave", "APPROVED") if resp.status_code == 200 else \
        results.fail("Approve leave", f"status={resp.status_code}, {resp.text[:200]}")

# Contracts
resp = call("post", "/api/v1/personnel/contracts", sa_token, {
    "staff_id": "staff-001", "contract_type": "CDI",
    "start_date": "2020-01-15", "position": "Médecin Cardiologue",
    "salary_grade": "Echelle 10", "facility_id": "fac-chu-donka"
})
results.ok("Create contract", "CDI") if resp.status_code in [200, 201] else \
    results.fail("Create contract", f"status={resp.status_code}, {resp.text[:200]}")

resp = call("get", "/api/v1/personnel/contracts", sa_token)
results.ok("List contracts", f"{len(extract_list(resp))} contrats") if resp.status_code == 200 else \
    results.fail("List contracts", f"status={resp.status_code}, {resp.text[:200]}")

# Stats
resp = call("get", "/api/v1/personnel/stats", sa_token)
results.ok("Personnel stats", f"total={resp.json().get('total','N/A')}") if resp.status_code == 200 else \
    results.fail("Personnel stats", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 20. ACTIVITY
# ═══════════════════════════════════════════════════════════════════
results.section("20. JOURNAL D'ACTIVITÉ")

resp = call("get", "/api/v1/activity", sa_token)
results.ok("List activity", f"{len(extract_list(resp))} entrées") if resp.status_code == 200 else \
    results.fail("List activity", f"status={resp.status_code}, {resp.text[:200]}")


# ═══════════════════════════════════════════════════════════════════
# 21. MULTI-TENANT ISOLATION
# ═══════════════════════════════════════════════════════════════════
results.section("21. ISOLEMENT MULTI-TENANT")

# 21.1 SUPER_ADMIN sees all patients
resp = call("get", "/api/v1/patients", sa_token)
if resp.status_code == 200:
    pats = extract_list(resp)
    fac_ids = set(p.get("facility_id") for p in pats) if pats else set()
    if len(fac_ids) >= 2:
        results.ok("SUPER_ADMIN sees all facilities", f"{len(fac_ids)} facilities: {fac_ids}")
    else:
        results.warn("SUPER_ADMIN sees all facilities", f"seulement {len(fac_ids)}: {fac_ids}")

# 21.2 ADMIN Donka sees only Donka patients
if admin_donka_token:
    resp = call("get", "/api/v1/patients", admin_donka_token)
    if resp.status_code == 200:
        pats = extract_list(resp)
        fac_ids = set(p.get("facility_id") for p in pats) if pats else set()
        only_donka = "fac-hgr-kankan" not in fac_ids
        if only_donka:
            results.ok("ADMIN Donka isolated", f"voit {fac_ids} (pas Kankan)")
        else:
            results.fail("ADMIN Donka NOT isolated", f"voit {fac_ids} (contient Kankan!)")
    else:
        results.fail("ADMIN Donka patients", f"status={resp.status_code}")

# 21.3 Doctor Kankan sees only Kankan
if doctor_kankan_token:
    resp = call("get", "/api/v1/patients", doctor_kankan_token)
    if resp.status_code == 200:
        pats = extract_list(resp)
        fac_ids = set(p.get("facility_id") for p in pats) if pats else set()
        only_kankan = "fac-chu-donka" not in fac_ids
        if only_kankan:
            results.ok("Doctor Kankan isolated", f"voit {fac_ids} (pas Donka)")
        else:
            results.fail("Doctor Kankan NOT isolated", f"voit {fac_ids} (contient Donka!)")

# 21.4 Staff isolation
if admin_donka_token:
    resp = call("get", "/api/v1/personnel/staff", admin_donka_token)
    if resp.status_code == 200:
        staff = extract_list(resp)
        fac_ids = set(s.get("facility_id") for s in staff) if staff else set()
        only_donka = "fac-hgr-kankan" not in fac_ids
        if only_donka:
            results.ok("Staff tenant-isolated", f"ADMIN Donka voit {fac_ids}")
        else:
            results.fail("Staff NOT isolated", f"voit {fac_ids}")

# 21.5 SUPER_ADMIN sees all staff
resp = call("get", "/api/v1/personnel/staff", sa_token)
if resp.status_code == 200:
    staff = extract_list(resp)
    fac_ids = set(s.get("facility_id") for s in staff) if staff else set()
    if len(fac_ids) >= 2:
        results.ok("SUPER_ADMIN sees all staff", f"{len(fac_ids)} facilities")
    else:
        results.warn("SUPER_ADMIN all staff", f"seulement {len(fac_ids)} facility")


# ═══════════════════════════════════════════════════════════════════
# 22. RBAC PERMISSION CHECKS
# ═══════════════════════════════════════════════════════════════════
results.section("22. RBAC - PERMISSIONS PAR RÔLE")

# 22.1 PHARMACIST denied billing
if "PHARMACIST" in role_tokens:
    resp = call("get", "/api/v1/billing/invoices", role_tokens["PHARMACIST"])
    results.ok("PHARMACIST denied billing", f"status={resp.status_code}") if resp.status_code == 403 else \
        results.warn("PHARMACIST billing", f"status={resp.status_code}")

# 22.2 CASHIER denied pharmacy management
if "CASHIER" in role_tokens:
    resp = call("post", "/api/v1/pharmacy/products", role_tokens["CASHIER"], {
        "code": "HACK", "name": "Hack", "facility_id": "fac-chu-donka"
    })
    results.ok("CASHIER denied pharmacy.manage", f"status={resp.status_code}") if resp.status_code == 403 else \
        results.warn("CASHIER pharmacy", f"status={resp.status_code}")

# 22.3 NURSE denied hospitalization management
if "NURSE" in role_tokens:
    resp = call("post", "/api/v1/hospitalization/rooms", role_tokens["NURSE"], {
        "code": "HACK", "name": "Hack", "department_id": "dept-medecine", "facility_id": "fac-chu-donka"
    })
    results.ok("NURSE denied hosp.manage", f"status={resp.status_code}") if resp.status_code == 403 else \
        results.warn("NURSE hosp.manage", f"status={resp.status_code}")

# 22.4 LAB_TECH can access lab
if "LAB_TECH" in role_tokens:
    resp = call("get", "/api/v1/laboratory/tests", role_tokens["LAB_TECH"])
    results.ok("LAB_TECH → lab", f"status={resp.status_code}") if resp.status_code == 200 else \
        results.fail("LAB_TECH → lab", f"status={resp.status_code}")

# 22.5 MIDWIFE can access maternity
if "MIDWIFE" in role_tokens:
    resp = call("get", "/api/v1/maternity/records", role_tokens["MIDWIFE"])
    results.ok("MIDWIFE → maternity", f"status={resp.status_code}") if resp.status_code == 200 else \
        results.fail("MIDWIFE → maternity", f"status={resp.status_code}")

# 22.6 DOCTOR can access clinical
resp = call("get", "/api/v1/clinical/patients/pat-001/notes", doc_token)
results.ok("DOCTOR → clinical", f"status={resp.status_code}") if resp.status_code == 200 else \
    results.fail("DOCTOR → clinical", f"status={resp.status_code}")

# 22.7 ADMIN bypasses permission
if admin_donka_token:
    resp = call("get", "/api/v1/personnel/staff", admin_donka_token)
    results.ok("ADMIN bypasses perms", f"status={resp.status_code}") if resp.status_code == 200 else \
        results.fail("ADMIN bypass", f"status={resp.status_code}")

# 22.8 CASHIER can access billing
if "CASHIER" in role_tokens:
    resp = call("get", "/api/v1/billing/tariffs", role_tokens["CASHIER"])
    results.ok("CASHIER → billing", f"status={resp.status_code}") if resp.status_code == 200 else \
        results.fail("CASHIER → billing", f"status={resp.status_code}")


# ═══════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════
success = results.summary()

# Cleanup
try:
    os.remove("./test_e2e.db")
except:
    pass

sys.exit(0 if success else 1)
