"""Tests du module Dashboard Qualité v1.4.0 — seuils, alertes, dashboard, check_thresholds."""
from datetime import datetime, timedelta

import pytest

from app.modules.quality.dashboard_models import (
    QualityAlert,
    QualityThreshold,
    evaluate_threshold,
)
from app.modules.quality.models import (
    IncidentReport,
    QualityIndicator,
    QualityMeasurement,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _create_indicator(db, facility_id="facility-qual-001", code="INOSO_RATE"):
    """Crée un indicateur qualité de test."""
    ind = QualityIndicator(
        facility_id=facility_id,
        code=code,
        name=f"Indicator {code}",
        category="SAFETY",
        unit="%",
        target_value="5",
        frequency="MONTHLY",
    )
    db.add(ind)
    db.commit()
    db.refresh(ind)
    return ind


def _create_measurement(db, indicator_id, value="7", facility_id="facility-qual-001"):
    """Crée une mesure qualité de test."""
    now = datetime.utcnow()
    m = QualityMeasurement(
        facility_id=facility_id,
        indicator_id=indicator_id,
        period_start=now - timedelta(days=30),
        period_end=now,
        value=value,
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


# ── Thresholds CRUD ─────────────────────────────────────────────────────────

def test_list_thresholds_empty(auth_headers, client):
    """GET /quality/thresholds — liste vide au début."""
    response = client.get("/api/v1/quality/thresholds", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_create_threshold(auth_headers, client, db):
    """POST /quality/thresholds — crée un seuil d'alerte."""
    ind = _create_indicator(db)
    payload = {
        "facility_id": "facility-qual-001",
        "indicator_id": ind.id,
        "comparator": "GT",
        "threshold_value": "5",
        "severity": "CRITICAL",
        "alert_message": "Taux > {{threshold}}% : {{value}}%",
        "notify_roles": ["ADMIN", "DOCTOR"],
        "channels": ["in_app", "sms"],
        "cooldown_hours": 24,
    }
    response = client.post(
        "/api/v1/quality/thresholds", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["comparator"] == "GT"
    assert data["threshold_value"] == "5"
    assert data["severity"] == "CRITICAL"
    assert "sms" in data["channels"]
    assert "ADMIN" in data["notify_roles"]
    assert data["enabled"] is True


def test_update_threshold(auth_headers, client, db):
    """PATCH /quality/thresholds/{id} — met à jour le seuil."""
    ind = _create_indicator(db, code="SAT_PATIENT")
    create = client.post(
        "/api/v1/quality/thresholds",
        json={
            "facility_id": "facility-qual-001",
            "indicator_id": ind.id,
            "comparator": "LT",
            "threshold_value": "80",
            "severity": "HIGH",
        },
        headers=auth_headers,
    )
    threshold_id = create.json()["id"]

    response = client.patch(
        f"/api/v1/quality/thresholds/{threshold_id}",
        json={"severity": "MEDIUM", "threshold_value": "75"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "MEDIUM"
    assert data["threshold_value"] == "75"


def test_delete_threshold(auth_headers, client, db):
    """DELETE /quality/thresholds/{id} — supprime un seuil."""
    ind = _create_indicator(db, code="READMIT_30D")
    create = client.post(
        "/api/v1/quality/thresholds",
        json={
            "facility_id": "facility-qual-001",
            "indicator_id": ind.id,
            "comparator": "GT",
            "threshold_value": "10",
        },
        headers=auth_headers,
    )
    threshold_id = create.json()["id"]
    response = client.delete(
        f"/api/v1/quality/thresholds/{threshold_id}", headers=auth_headers
    )
    assert response.status_code == 204


# ── Dashboard agrégé ────────────────────────────────────────────────────────

def test_get_dashboard(auth_headers, client, db):
    """GET /quality/dashboard — retourne KPIs + incidents + alertes + trends."""
    # Créer un indicateur + une mesure
    ind = _create_indicator(db, code="INOSO_RATE")
    _create_measurement(db, ind.id, value="3.5")

    response = client.get(
        "/api/v1/quality/dashboard?days=30", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert "incidents" in data
    assert "alerts" in data
    assert "trends" in data
    assert "thresholds_count" in data
    # Au moins un KPI dans la liste
    assert len(data["kpis"]) >= 1


def test_get_dashboard_with_incidents(auth_headers, client, db):
    """GET /quality/dashboard — agrège correctement les incidents."""
    # Créer un incident
    inc = IncidentReport(
        facility_id="facility-qual-001",
        incident_date=datetime.utcnow(),
        incident_type="FALL",
        severity="MINOR",
        description="Chute test",
    )
    db.add(inc)
    db.commit()

    response = client.get(
        "/api/v1/quality/dashboard?days=30", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["incidents"]["total"] >= 1
    # Vérifier la structure des agrégats
    assert "by_type" in data["incidents"]
    assert "by_severity" in data["incidents"]
    assert "by_status" in data["incidents"]


def test_get_indicators_catalog(auth_headers, client):
    """GET /quality/indicators/catalog — catalogue statique OMS/HAS."""
    response = client.get(
        "/api/v1/quality/indicators/catalog", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "indicators" in data
    assert "thresholds" in data
    codes = [i["code"] for i in data["indicators"]]
    assert "INOSO_RATE" in codes
    assert "SAT_PATIENT" in codes
    assert "ED_WAIT_4H" in codes


# ── Seed defaults ───────────────────────────────────────────────────────────

def test_seed_defaults_no_facility(auth_headers, client, db):
    """POST /quality/seed-defaults — sans facility, ne crée rien (pas de facility)."""
    response = client.post(
        "/api/v1/quality/seed-defaults", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    # Sans facility dans la DB de test, rien n'est créé
    assert data["indicators_created"] == 0
    assert data["thresholds_created"] == 0


def test_seed_defaults_with_facility(auth_headers, client, db):
    """POST /quality/seed-defaults?facility_id=... — crée indicateurs + seuils."""
    from app.modules.facilities.models import Facility
    fac = Facility(name="Test Facility", code="TEST-FAC", category="CHU")
    db.add(fac)
    db.commit()
    db.refresh(fac)

    response = client.post(
        f"/api/v1/quality/seed-defaults?facility_id={fac.id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["indicators_created"] >= 8  # 10 indicateurs par défaut
    assert data["thresholds_created"] >= 8  # 10 seuils par défaut


# ── Alertes ─────────────────────────────────────────────────────────────────

def test_list_alerts_empty(auth_headers, client):
    """GET /quality/alerts — liste vide au début."""
    response = client.get("/api/v1/quality/alerts", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_check_thresholds_raises_alert(auth_headers, client, db):
    """POST /quality/alerts/check — lève une alerte si seuil franchi."""
    ind = _create_indicator(db, code="INOSO_RATE")
    # Mesure au-dessus du seuil
    _create_measurement(db, ind.id, value="8")  # > 5

    # Créer un threshold GT 5
    client.post(
        "/api/v1/quality/thresholds",
        json={
            "facility_id": "facility-qual-001",
            "indicator_id": ind.id,
            "comparator": "GT",
            "threshold_value": "5",
            "severity": "CRITICAL",
            "alert_message": "Taux > {{threshold}}% : {{value}}%",
            "notify_roles": [],  # pas de notification pour éviter les effets de bord
            "channels": ["in_app"],
        },
        headers=auth_headers,
    )

    # Déclencher le check
    response = client.post(
        "/api/v1/quality/alerts/check", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["raised"] >= 1
    assert len(data["alerts"]) >= 1
    alert = data["alerts"][0]
    assert alert["status"] == "OPEN"
    assert alert["severity"] == "CRITICAL"
    assert alert["observed_value"] == "8"
    assert alert["threshold_value"] == "5"


def test_check_thresholds_no_alert_when_below(auth_headers, client, db):
    """POST /quality/alerts/check — pas d'alerte si mesure sous le seuil."""
    ind = _create_indicator(db, code="SAT_PATIENT")
    _create_measurement(db, ind.id, value="85")  # > 80 (target)

    # Threshold LT 80 (alerte si < 80)
    client.post(
        "/api/v1/quality/thresholds",
        json={
            "facility_id": "facility-qual-001",
            "indicator_id": ind.id,
            "comparator": "LT",
            "threshold_value": "80",
            "severity": "HIGH",
        },
        headers=auth_headers,
    )

    response = client.post(
        "/api/v1/quality/alerts/check", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["raised"] == 0


def test_acknowledge_alert(auth_headers, client, db):
    """POST /quality/alerts/{id}/acknowledge — passe à ACKNOWLEDGED."""
    ind = _create_indicator(db, code="MORTALITY_24H")
    _create_measurement(db, ind.id, value="3")  # > 2

    client.post(
        "/api/v1/quality/thresholds",
        json={
            "facility_id": "facility-qual-001",
            "indicator_id": ind.id,
            "comparator": "GT",
            "threshold_value": "2",
            "severity": "CRITICAL",
            "channels": ["in_app"],
            "notify_roles": [],
        },
        headers=auth_headers,
    )

    check = client.post("/api/v1/quality/alerts/check", headers=auth_headers)
    alert_id = check.json()["alerts"][0]["id"]

    response = client.post(
        f"/api/v1/quality/alerts/{alert_id}/acknowledge",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ACKNOWLEDGED"
    assert data["acknowledged_at"] is not None


def test_resolve_alert(auth_headers, client, db):
    """POST /quality/alerts/{id}/resolve — passe à RESOLVED avec note."""
    ind = _create_indicator(db, code="FALL_RATE")
    _create_measurement(db, ind.id, value="5")  # > 3

    client.post(
        "/api/v1/quality/thresholds",
        json={
            "facility_id": "facility-qual-001",
            "indicator_id": ind.id,
            "comparator": "GT",
            "threshold_value": "3",
            "severity": "HIGH",
            "channels": ["in_app"],
            "notify_roles": [],
        },
        headers=auth_headers,
    )

    check = client.post("/api/v1/quality/alerts/check", headers=auth_headers)
    alert_id = check.json()["alerts"][0]["id"]

    response = client.post(
        f"/api/v1/quality/alerts/{alert_id}/resolve",
        json={"resolution_note": "Investigation done. Action corrective mise en place."},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RESOLVED"
    assert "Action corrective" in data["resolution_note"]


def test_close_alert(auth_headers, client, db):
    """POST /quality/alerts/{id}/close — clôture une alerte résolue."""
    ind = _create_indicator(db, code="MED_ERROR_RATE")
    _create_measurement(db, ind.id, value="2")

    client.post(
        "/api/v1/quality/thresholds",
        json={
            "facility_id": "facility-qual-001",
            "indicator_id": ind.id,
            "comparator": "GT",
            "threshold_value": "1",
            "channels": ["in_app"],
            "notify_roles": [],
        },
        headers=auth_headers,
    )

    check = client.post("/api/v1/quality/alerts/check", headers=auth_headers)
    alert_id = check.json()["alerts"][0]["id"]

    # D'abord résoudre
    client.post(
        f"/api/v1/quality/alerts/{alert_id}/resolve",
        json={"resolution_note": "Resolved"},
        headers=auth_headers,
    )

    # Puis clore
    response = client.post(
        f"/api/v1/quality/alerts/{alert_id}/close", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CLOSED"
    assert data["closed_at"] is not None


# ── Cooldown ────────────────────────────────────────────────────────────────

def test_check_thresholds_respects_cooldown(auth_headers, client, db):
    """POST /quality/alerts/check — cooldown évite le spam d'alertes."""
    ind = _create_indicator(db, code="BED_OCCUPANCY")
    _create_measurement(db, ind.id, value="95")  # > 85

    client.post(
        "/api/v1/quality/thresholds",
        json={
            "facility_id": "facility-qual-001",
            "indicator_id": ind.id,
            "comparator": "GT",
            "threshold_value": "85",
            "severity": "MEDIUM",
            "channels": ["in_app"],
            "notify_roles": [],
            "cooldown_hours": 24,
        },
        headers=auth_headers,
    )

    # Premier check : doit lever une alerte
    r1 = client.post("/api/v1/quality/alerts/check", headers=auth_headers)
    assert r1.json()["raised"] >= 1

    # Deuxième check immédiat : cooldown → pas de nouvelle alerte
    r2 = client.post("/api/v1/quality/alerts/check", headers=auth_headers)
    assert r2.json()["raised"] == 0


# ── Comparateurs ────────────────────────────────────────────────────────────

def test_evaluate_threshold_gt():
    """evaluate_threshold — comparateur GT."""
    assert evaluate_threshold("GT", "8", "5") is True
    assert evaluate_threshold("GT", "5", "5") is False
    assert evaluate_threshold("GT", "3", "5") is False


def test_evaluate_threshold_lt():
    """evaluate_threshold — comparateur LT."""
    assert evaluate_threshold("LT", "3", "5") is True
    assert evaluate_threshold("LT", "5", "5") is False
    assert evaluate_threshold("LT", "8", "5") is False


def test_evaluate_threshold_ge_le():
    """evaluate_threshold — comparateurs GE et LE."""
    assert evaluate_threshold("GE", "5", "5") is True
    assert evaluate_threshold("GE", "4", "5") is False
    assert evaluate_threshold("LE", "5", "5") is True
    assert evaluate_threshold("LE", "6", "5") is False


def test_evaluate_threshold_eq():
    """evaluate_threshold — comparateur EQ."""
    assert evaluate_threshold("EQ", "5", "5") is True
    assert evaluate_threshold("EQ", "5", "6") is False


def test_evaluate_threshold_with_percent():
    """evaluate_threshold — gère les valeurs avec %."""
    assert evaluate_threshold("GT", "8%", "5%") is True
    assert evaluate_threshold("GT", "3.5%", "5%") is False


def test_evaluate_threshold_non_numeric_eq():
    """evaluate_threshold — EQ fonctionne avec des chaînes non numériques."""
    assert evaluate_threshold("EQ", "CRITICAL", "CRITICAL") is True
    assert evaluate_threshold("EQ", "CRITICAL", "MAJOR") is False
    # Les autres comparateurs retournent False pour des non-numériques
    assert evaluate_threshold("GT", "CRITICAL", "MAJOR") is False
