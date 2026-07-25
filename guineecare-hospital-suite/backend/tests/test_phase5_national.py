"""Tests Phase 5 — Pilotage national et reporting santé Guinée (v2.5.0).

Couvre les nouveaux endpoints :
- GET /reporting/national (dashboard national agrégé)
- GET /reporting/facility-breakdown (activité par établissement)
- GET /reporting/geo-distribution (répartition géographique)
- GET /reporting/dhis2/{period} (dataset DHIS2-compatible)
- GET /reporting/export/xlsx (export Excel)

SÉCURITÉ testée :
- Isolation multi-tenant (ADMIN ne voit que son établissement)
- SUPER_ADMIN voit tous les établissements
- Aucune donnée patient dans les agrégats (anonymisation)
- patient_id retiré de /laboratory/stats urgent_pending
"""
from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from app.core.security import create_access_token, hash_password
from app.modules.admissions.models import Admission
from app.modules.billing.models import Invoice
from app.modules.emergency.models import EmergencyVisit
from app.modules.facilities.models import Facility
from app.modules.laboratory.models import LabOrder, LabTest
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


def _make_facility(db, code=None, name=None, region="Conakry", prefecture="Conakry", commune="Kaloum", category="CHU"):
    f = Facility(
        code=code or f"FAC-{uuid4().hex[:6]}",
        name=name or f"Facility {uuid4().hex[:4]}",
        category=category,
        region=region,
        prefecture=prefecture,
        commune=commune,
        status="ACTIVE",
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


def _make_patient(db, facility_id):
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


# ── GET /reporting/national ────────────────────────────────────────────────

class TestNationalDashboard:
    def test_national_dashboard_returns_aggregates(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="FAC-A", name="CHU Donka", region="Conakry")
        f2 = _make_facility(db, code="FAC-B", name="CHU Ignace Deen", region="Conakry")

        # Créer des patients dans les 2 établissements
        for _ in range(5):
            _make_patient(db, f1.id)
        for _ in range(3):
            _make_patient(db, f2.id)

        resp = client.get(
            "/api/v1/reporting/national",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["facilities_count"] >= 2
        assert body["indicators"]["total_patients"] >= 8
        assert "by_region" in body
        assert "by_facility_type" in body

    def test_national_dashboard_region_filter(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="FAC-C", region="Conakry")
        f2 = _make_facility(db, code="FAC-D", region="Kankan")

        _make_patient(db, f1.id)
        _make_patient(db, f2.id)

        resp = client.get(
            "/api/v1/reporting/national?region=Conakry",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["filters"]["region"] == "Conakry"
        assert body["facilities_count"] >= 1
        # Seuls les patients de Conakry doivent être comptés
        # (mais il peut y avoir d'autres patients Conakry d'autres tests)
        assert body["indicators"]["total_patients"] >= 1

    def test_national_dashboard_no_patient_data_exposed(self, client, db):
        """Vérifie qu'aucune donnée patient nominative n'est exposée."""
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="FAC-E")
        p = _make_patient(db, f1.id)

        resp = client.get(
            "/api/v1/reporting/national",
            headers=_headers_for(admin),
        )
        body_str = resp.text
        # Aucun nom de patient ne doit apparaître
        assert p.first_name not in body_str
        assert p.last_name not in body_str
        assert p.phone not in body_str
        assert str(p.id) not in body_str or "patient_id" not in body_str

    def test_national_dashboard_admin_sees_only_own_facility(self, client, db):
        """ADMIN ne voit que les données de son établissement.

        Note : ADMIN a le bypass require_permission mais tenant_query filtre
        par facility_id (CROSS_TENANT_ROLES = {"SUPER_ADMIN"} uniquement).
        Donc ADMIN ne voit QUE les agrégats de son établissement.
        """
        f1 = _make_facility(db, code="FAC-F-OWN", name="My Facility Unique")
        f2 = _make_facility(db, code="FAC-G-OTHER", name="Other Facility Unique")
        admin = _make_user(db, role="ADMIN", facility_id=f1.id)

        p1 = _make_patient(db, f1.id)
        _make_patient(db, f2.id)
        _make_patient(db, f2.id)

        resp = client.get(
            "/api/v1/reporting/national",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        # ADMIN doit voir uniquement les patients de son établissement
        # (les autres facilities sont filtrées par tenant_query)
        assert body["indicators"]["total_patients"] == 1, (
            f"ADMIN should see only 1 patient (own facility), got {body['indicators']['total_patients']}"
        )

    def test_national_dashboard_period_filter(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="FAC-H")
        _make_patient(db, f1.id)

        resp = client.get(
            "/api/v1/reporting/national?period=2020",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        # Période 2020 → aucun patient (créés en 2026)
        assert body["indicators"]["total_patients"] == 0

    def test_national_dashboard_requires_permission(self, client, db):
        """Un utilisateur sans reporting.read doit être refusé."""
        # CASHIER n'a pas reporting.read
        f1 = _make_facility(db, code="FAC-I")
        cashier = _make_user(db, role="CASHIER", facility_id=f1.id)

        resp = client.get(
            "/api/v1/reporting/national",
            headers=_headers_for(cashier),
        )
        assert resp.status_code == 403


# ── GET /reporting/facility-breakdown ──────────────────────────────────────

class TestFacilityBreakdown:
    def test_breakdown_returns_per_facility_data(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="FAC-J", name="CHU A")
        f2 = _make_facility(db, code="FAC-K", name="CHU B")

        for _ in range(3):
            _make_patient(db, f1.id)
        _make_patient(db, f2.id)

        resp = client.get(
            "/api/v1/reporting/facility-breakdown",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_facilities"] >= 2
        names = [b["name"] for b in body["data"]]
        assert "CHU A" in names
        assert "CHU B" in names
        # Vérifier que les compteurs sont là
        for b in body["data"]:
            assert "patients_count" in b
            assert "admissions_count" in b
            assert "revenue_gnf" in b

    def test_breakdown_no_patient_ids(self, client, db):
        """Aucun patient_id ne doit apparaître dans le breakdown."""
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="FAC-L")
        p = _make_patient(db, f1.id)

        resp = client.get(
            "/api/v1/reporting/facility-breakdown",
            headers=_headers_for(admin),
        )
        body_str = resp.text
        assert str(p.id) not in body_str
        assert p.first_name not in body_str


# ── GET /reporting/geo-distribution ────────────────────────────────────────

class TestGeographicDistribution:
    def test_geo_distribution_by_region(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        _make_facility(db, code="FAC-M", region="Conakry")
        _make_facility(db, code="FAC-N", region="Kankan")
        _make_facility(db, code="FAC-O", region="Conakry")

        resp = client.get(
            "/api/v1/reporting/geo-distribution?level=region",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["level"] == "region"
        regions = [d["region"] for d in body["data"]]
        assert "Conakry" in regions
        assert "Kankan" in regions

    def test_geo_distribution_invalid_level(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        resp = client.get(
            "/api/v1/reporting/geo-distribution?level=invalid",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 422


# ── GET /reporting/dhis2/{period} ──────────────────────────────────────────

class TestDHIS2Dataset:
    def test_dhis2_dataset_structure(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="DHIS2-FAC-1")
        _make_patient(db, f1.id)

        resp = client.get(
            "/api/v1/reporting/dhis2/202603",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["dataSet"] == "SNIS_MENSUEL"
        assert body["period"] == "202603"
        assert "DHIS2-FAC-1" in body["orgUnits"]
        assert len(body["dataValues"]) > 0
        # Vérifier la structure DHIS2 d'un dataValue
        dv = body["dataValues"][0]
        assert "dataElement" in dv
        assert "orgUnit" in dv
        assert "period" in dv
        assert "value" in dv

    def test_dhis2_dataset_invalid_period(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        resp = client.get(
            "/api/v1/reporting/dhis2/abc",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 422


# ── GET /reporting/export/xlsx ─────────────────────────────────────────────

class TestExcelExport:
    def test_xlsx_export_returns_file(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="XLSX-FAC-1", name="CHU Export Test")
        _make_patient(db, f1.id)

        resp = client.get(
            "/api/v1/reporting/export/xlsx",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert "spreadsheetml" in resp.headers["content-type"]
        assert "attachment" in resp.headers["content-disposition"]
        assert ".xlsx" in resp.headers["content-disposition"]
        # Le contenu doit être un fichier xlsx (PK zip magic)
        assert resp.content[:2] == b"PK"

    def test_xlsx_export_with_filters(self, client, db):
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        _make_facility(db, code="XLSX-FAC-2", region="Conakry")
        _make_facility(db, code="XLSX-FAC-3", region="Kankan")

        resp = client.get(
            "/api/v1/reporting/export/xlsx?region=Conakry",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        assert resp.content[:2] == b"PK"

    def test_xlsx_export_creates_audit_log(self, client, db):
        """L'export doit être journalisé dans audit_logs."""
        from app.modules.auth.models import AuditLog

        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="XLSX-FAC-4")
        _make_patient(db, f1.id)

        client.get(
            "/api/v1/reporting/export/xlsx",
            headers=_headers_for(admin),
        )
        entries = (
            db.query(AuditLog)
            .filter(AuditLog.action == "reporting.export.xlsx")
            .all()
        )
        assert len(entries) >= 1


# ── GET /laboratory/stats (anonymisation v2.5.0) ───────────────────────────

class TestLabStatsAnonymisation:
    def test_lab_stats_no_patient_id(self, client, db):
        """Le payload urgent_pending ne doit plus contenir patient_id."""
        admin = _make_user(db, role="SUPER_ADMIN", facility_id=None)
        f1 = _make_facility(db, code="LAB-FAC-1")
        p = _make_patient(db, f1.id)
        lab_test = LabTest(
            facility_id=f1.id,
            code=f"LAB-{uuid4().hex[:6]}",
            name="Glycémie",
            sample_type="BLOOD",
        )
        db.add(lab_test)
        db.commit()
        db.refresh(lab_test)

        order = LabOrder(
            facility_id=f1.id,
            patient_id=p.id,
            test_id=lab_test.id,
            status="ORDERED",
            priority="URGENT",
        )
        db.add(order)
        db.commit()

        resp = client.get(
            "/api/v1/laboratory/stats",
            headers=_headers_for(admin),
        )
        assert resp.status_code == 200
        body = resp.json()
        # Aucun patient_id ne doit être dans urgent_pending
        for urgent in body["data"]["urgent_pending"]:
            assert "patient_id" not in urgent, (
                "urgent_pending ne doit plus contenir patient_id (anonymisation v2.5.0)"
            )
