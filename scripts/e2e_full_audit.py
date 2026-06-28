#!/usr/bin/env python3
"""Audit E2E complet — tous les modules, tous les rôles, CRUD operations."""
import requests, json, sys

BASE = "https://guineecare.onrender.com/api/v1"
results = []

def login(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password}, timeout=30)
    if r.status_code == 200:
        d = r.json()
        if d.get("requires_2fa"):
            return None, "2FA required"
        return d["access_token"], d["user"]["role"]
    return None, f"HTTP {r.status_code}"

def api(token, method, path, data=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{BASE}{path}"
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=30)
        elif method == "POST":
            r = requests.post(url, headers=headers, json=data, timeout=30)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers, timeout=30)
        return r.status_code, r.text
    except Exception as e:
        return 0, str(e)[:150]

def test(role, action, status, detail=""):
    ok = status in (200, 201, 204)
    icon = "✅" if ok else "❌"
    results.append(f"{icon} [{role}] {action} → {status} {detail}")
    return ok

USERS = [
    ("SUPER_ADMIN", "admin@guineecare.com", "admin123"),
    ("ADMIN", "admin.donka@chu-donka.gn", "admin123"),
    ("DOCTOR", "dr.diallo@chu-donka.gn", "doctor123"),
    ("NURSE", "inf.konde@chu-donka.gn", "nurse123"),
    ("PHARMACIST", "pharma.dubois@chu-donka.gn", "pharma123"),
    ("LAB_TECH", "lab.sakouv@chu-donka.gn", "labtech123"),
    ("MIDWIFE", "sf.bangoura@chu-donka.gn", "sagefemme123"),
    ("CASHIER", "caisse.tamba@chu-ignace.gn", "caisse123"),
]

# LOGIN ALL
tokens = {}
for role, email, pwd in USERS:
    tok, info = login(email, pwd)
    if tok:
        tokens[role] = tok
        test(role, f"LOGIN", 200, f"({email})")
    else:
        test(role, f"LOGIN", 0, f"({email}) {info}")

T = tokens.get("SUPER_ADMIN")
if not T:
    print("FATAL: Cannot login as SUPER_ADMIN"); sys.exit(1)

# GET FACILITY
s, body = api(T, "GET", "/facilities")
try:
    FAC_ID = json.loads(body).get("data", [{}])[0].get("id", "unknown")
except:
    FAC_ID = "3782cbcc-1e27-4d45-93c9-4b1d43f9ca8c"  # fallback known ID

# PATIENTS CRUD
print("\n=== PATIENTS ===")
s, body = api(T, "POST", "/patients", {"facility_id": FAC_ID, "first_name": "E2E", "last_name": "Audit", "gender": "M", "blood_type": "O+"})
test("SUPER_ADMIN", "POST /patients (create)", s)
pid = json.loads(body)["data"]["id"] if s == 200 else None

s, _ = api(T, "GET", f"/patients/{pid}" if pid else "/patients/nonexistent")
test("SUPER_ADMIN", "GET /patients/{id}", s)
s, _ = api(T, "GET", "/patients?page=1&page_size=5")
test("SUPER_ADMIN", "GET /patients (list)", s)
s, _ = api(T, "GET", "/patients?search=E2E")
test("SUPER_ADMIN", "GET /patients?search=", s)

# ADMISSIONS
print("\n=== ADMISSIONS ===")
if pid:
    s, _ = api(T, "POST", "/admissions", {"patient_id": pid, "admission_type": "ROUTINE"})
    test("SUPER_ADMIN", "POST /admissions", s)
s, _ = api(T, "GET", "/admissions?page=1&page_size=5")
test("SUPER_ADMIN", "GET /admissions", s)

# CLINICAL
print("\n=== CLINICAL ===")
s, _ = api(T, "GET", "/clinical/notes"); test("SUPER_ADMIN", "GET /clinical/notes", s)
s, _ = api(T, "GET", "/clinical/measurements"); test("SUPER_ADMIN", "GET /clinical/measurements", s)
if pid:
    s, _ = api(T, "POST", f"/clinical/patients/{pid}/notes", {"note_type": "OBSERVATION", "content": "Test"})
    test("SUPER_ADMIN", "POST /clinical/notes", s)
    s, _ = api(T, "POST", f"/clinical/patients/{pid}/measurements", {"measurement_type": "HEART_RATE", "value": "72", "unit": "bpm"})
    test("SUPER_ADMIN", "POST /clinical/measurements", s)
    s, _ = api(T, "GET", f"/clinical/patients/{pid}/notes"); test("SUPER_ADMIN", "GET /clinical/patients/{id}/notes", s)
    s, _ = api(T, "GET", f"/clinical/patients/{pid}/measurements"); test("SUPER_ADMIN", "GET /clinical/patients/{id}/measurements", s)

# ALL MODULES GET
print("\n=== ALL MODULES ===")
modules = [
    ("/billing/tariffs", "billing/tariffs"), ("/billing/invoices?page=1&page_size=5", "billing/invoices"),
    ("/billing/payments?page=1&page_size=5", "billing/payments"), ("/laboratory/tests", "lab/tests"),
    ("/laboratory/orders?page=1&page_size=5", "lab/orders"), ("/laboratory/results?page=1&page_size=5", "lab/results"),
    ("/pharmacy/products", "pharmacy/products"), ("/pharmacy/stock", "pharmacy/stock"),
    ("/pharmacy/stock/movements?page=1&page_size=5", "pharmacy/movements"), ("/emergency/queue", "emergency/queue"),
    ("/hospitalization/beds", "hosp/beds"), ("/hospitalization/stays", "hosp/stays"),
    ("/imaging/orders", "imaging/orders"), ("/imaging/results", "imaging/results"),
    ("/surgery/rooms", "surgery/rooms"), ("/surgery/schedules", "surgery/schedules"),
    ("/maternity/records", "maternity/records"), ("/personnel/staff?page=1&page_size=5", "personnel/staff"),
    ("/personnel/shifts", "personnel/shifts"), ("/quality/dashboard?days=30", "quality/dashboard"),
    ("/quality/indicators", "quality/indicators"), ("/quality/alerts", "quality/alerts"),
    ("/quality/thresholds", "quality/thresholds"), ("/notifications?page=1&page_size=5", "notifications"),
    ("/notifications/unread-count", "notifications/unread-count"),
    ("/notifications/sms/providers", "sms/providers"), ("/notifications/sms/rules", "sms/rules"),
    ("/notifications/sms/messages?page=1&page_size=5", "sms/messages"), ("/notifications/sms/stats?days=30", "sms/stats"),
    ("/users?page=1&page_size=5", "users"), ("/rbac/roles", "rbac/roles"), ("/rbac/permissions", "rbac/permissions"),
    ("/facilities", "facilities"), ("/departments", "departments"),
    ("/audit/logs?page=1&page_size=5", "audit/logs"), ("/activity?page=1&page_size=5", "activity"),
    ("/reporting/statistics", "reporting/stats"), ("/search?q=Test", "search"),
]
for path, name in modules:
    s, _ = api(T, "GET", path)
    test("SUPER_ADMIN", f"GET /{name}", s)

# FHIR
print("\n=== FHIR ===")
for path, name in [("/fhir/metadata", "metadata"), ("/fhir/Patient?_count=3", "Patient"),
                    ("/fhir/Encounter?_count=3", "Encounter"), ("/fhir/Observation?_count=3", "Observation"),
                    ("/fhir/MedicationRequest?_count=3", "MedicationRequest"),
                    ("/fhir/DiagnosticReport?_count=3", "DiagnosticReport")]:
    s, _ = api(T, "GET", path)
    test("SUPER_ADMIN", f"GET /fhir/{name}", s)

# 2FA
print("\n=== 2FA ===")
s, _ = api(T, "POST", "/auth/2fa/setup"); test("SUPER_ADMIN", "POST /2fa/setup", s)

# ROLE-BASED ACCESS
print("\n=== ROLE ACCESS ===")
role_tests = [
    ("DOCTOR", "GET", "/patients?page=1&page_size=5", 200, "Doctor read patients"),
    ("DOCTOR", "GET", "/clinical/notes", 200, "Doctor read clinical"),
    ("DOCTOR", "GET", "/billing/invoices", 403, "Doctor CANNOT billing"),
    ("NURSE", "GET", "/patients", 200, "Nurse read patients"),
    ("NURSE", "GET", "/clinical/notes", 200, "Nurse read clinical"),
    ("NURSE", "GET", "/billing/invoices", 403, "Nurse CANNOT billing"),
    ("PHARMACIST", "GET", "/pharmacy/products", 200, "Pharmacist read pharmacy"),
    ("PHARMACIST", "GET", "/billing/invoices", 403, "Pharmacist CANNOT billing"),
    ("LAB_TECH", "GET", "/laboratory/orders", 200, "LabTech read lab"),
    ("LAB_TECH", "GET", "/billing/invoices", 403, "LabTech CANNOT billing"),
    ("CASHIER", "GET", "/billing/invoices", 200, "Cashier read billing"),
    ("CASHIER", "GET", "/billing/payments", 200, "Cashier read payments"),
    ("MIDWIFE", "GET", "/maternity/records", 200, "Midwife read maternity"),
    ("ADMIN", "GET", "/users", 200, "Admin read users"),
    ("ADMIN", "GET", "/audit/logs", 200, "Admin read audit"),
]
for role, method, path, expected, desc in role_tests:
    tok = tokens.get(role)
    if not tok:
        test(role, desc, 0, "no token"); continue
    s, _ = api(tok, method, path)
    ok = s == expected
    icon = "✅" if ok else "❌"
    extra = f" (expected {expected}, got {s})" if not ok else ""
    results.append(f"{icon} [{role}] {desc} → {s}{extra}")

# SUMMARY
passed = sum(1 for r in results if r.startswith("✅"))
failed = sum(1 for r in results if r.startswith("❌"))
total = len(results)
print(f"\n{'='*60}")
print(f"AUDIT E2E COMPLET: {passed} passed, {failed} failed, {total} total")
print(f"{'='*60}")
for r in results:
    print(r)
if failed > 0:
    print(f"\n{'='*60}")
    print("ÉCHECS:")
    for r in results:
        if r.startswith("❌"):
            print(f"  {r}")
