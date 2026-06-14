"""Tests for reporting endpoints (national reports, epidemic alerts, health statistics, dashboard)."""


def test_create_national_report(auth_headers, client):
    """POST /reporting/national-reports should create a national report."""
    payload = {
        "facility_id": "facility-rpt-001",
        "report_type": "MONTHLY",
        "period_start": "2026-01-01T00:00:00",
        "period_end": "2026-01-31T00:00:00",
    }
    response = client.post(
        "/api/v1/reporting/national-reports", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["report_type"] == "MONTHLY"
    assert data["data"]["status"] == "DRAFT"


def test_submit_national_report(auth_headers, client):
    """POST /reporting/national-reports/{id}/submit should transition DRAFT → SUBMITTED."""
    # Create report
    create_resp = client.post(
        "/api/v1/reporting/national-reports",
        json={
            "facility_id": "facility-rpt-001",
            "report_type": "MONTHLY",
            "period_start": "2026-02-01T00:00:00",
            "period_end": "2026-02-28T00:00:00",
        },
        headers=auth_headers,
    )
    report_id = create_resp.json()["data"]["id"]

    # Submit
    response = client.post(
        f"/api/v1/reporting/national-reports/{report_id}/submit", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "SUBMITTED"


def test_validate_national_report(auth_headers, client):
    """POST /reporting/national-reports/{id}/validate should transition SUBMITTED → VALIDATED."""
    # Create and submit report
    create_resp = client.post(
        "/api/v1/reporting/national-reports",
        json={
            "facility_id": "facility-rpt-001",
            "report_type": "QUARTERLY",
            "period_start": "2026-01-01T00:00:00",
            "period_end": "2026-03-31T00:00:00",
        },
        headers=auth_headers,
    )
    report_id = create_resp.json()["data"]["id"]

    client.post(
        f"/api/v1/reporting/national-reports/{report_id}/submit", headers=auth_headers
    )

    # Validate
    response = client.post(
        f"/api/v1/reporting/national-reports/{report_id}/validate",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "VALIDATED"


def test_create_epidemic_alert(auth_headers, client):
    """POST /reporting/epidemic-alerts should create an epidemic alert."""
    payload = {
        "facility_id": "facility-rpt-001",
        "disease_name": "Paludisme",
        "case_count": "12",
    }
    response = client.post(
        "/api/v1/reporting/epidemic-alerts", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["disease_name"] == "Paludisme"
    assert data["data"]["case_count"] == "12"
    assert data["data"]["status"] == "ACTIVE"


def test_close_epidemic_alert(auth_headers, client):
    """POST /reporting/epidemic-alerts/{id}/close should transition ACTIVE → CLOSED."""
    # Create alert
    create_resp = client.post(
        "/api/v1/reporting/epidemic-alerts",
        json={
            "facility_id": "facility-rpt-001",
            "disease_name": "Choléra",
            "case_count": "5",
        },
        headers=auth_headers,
    )
    alert_id = create_resp.json()["data"]["id"]

    # Close the alert
    response = client.post(
        f"/api/v1/reporting/epidemic-alerts/{alert_id}/close", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "CLOSED"


def test_create_health_statistic(auth_headers, client):
    """POST /reporting/statistics should create a health statistic."""
    payload = {
        "facility_id": "facility-rpt-001",
        "category": "CONSULTATION",
        "metric_name": "total_consultations",
        "metric_value": "1250",
        "period_start": "2026-01-01T00:00:00",
        "period_end": "2026-01-31T00:00:00",
    }
    response = client.post(
        "/api/v1/reporting/statistics", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["metric_name"] == "total_consultations"
    assert data["data"]["metric_value"] == "1250"


def test_reporting_dashboard(auth_headers, client):
    """GET /reporting/dashboard should return dashboard summary."""
    response = client.get("/api/v1/reporting/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data["data"]
    assert "alerts" in data["data"]
    assert "statistics" in data["data"]
