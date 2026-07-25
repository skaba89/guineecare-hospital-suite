"""Tests for quality endpoints (indicators, measurements, incidents)."""


def test_create_quality_indicator(auth_headers, client):
    """POST /quality/indicators should create a quality indicator."""
    payload = {
        "facility_id": "facility-qual-001",
        "code": "IPS",
        "name": "Indice de Performance",
        "category": "CLINICAL_OUTCOME",
        "unit": "score",
        "target_value": "80",
    }
    response = client.post(
        "/api/v1/quality/indicators", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["code"] == "IPS"
    assert data["data"]["name"] == "Indice de Performance"


def test_list_quality_indicators(auth_headers, client):
    """GET /quality/indicators should return a list of indicators."""
    client.post(
        "/api/v1/quality/indicators",
        json={
            "facility_id": "facility-qual-001",
            "code": "TMR24",
            "name": "Taux de Mortalité 24h",
        },
        headers=auth_headers,
    )

    response = client.get("/api/v1/quality/indicators", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


def test_create_quality_measurement(auth_headers, client):
    """POST /quality/measurements should create a quality measurement."""
    # Create indicator first
    indicator_resp = client.post(
        "/api/v1/quality/indicators",
        json={
            "facility_id": "facility-qual-001",
            "code": "SAT_PATIENT",
            "name": "Satisfaction Patient",
        },
        headers=auth_headers,
    )
    indicator_id = indicator_resp.json()["data"]["id"]

    # Create measurement
    payload = {
        "facility_id": "facility-qual-001",
        "indicator_id": indicator_id,
        "period_start": "2026-01-01T00:00:00",
        "period_end": "2026-01-31T00:00:00",
        "value": "85",
    }
    response = client.post(
        "/api/v1/quality/measurements", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["value"] == "85"
    assert data["data"]["indicator_id"] == indicator_id


def test_create_incident_report(auth_headers, client):
    """POST /quality/incidents should create an incident report."""
    payload = {
        "facility_id": "facility-qual-001",
        "incident_date": "2026-01-15T10:30:00",
        "incident_type": "FALL",
        "description": "Chute du patient",
    }
    response = client.post(
        "/api/v1/quality/incidents", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["incident_type"] == "FALL"
    assert data["data"]["description"] == "Chute du patient"
    assert data["data"]["status"] == "REPORTED"


def test_investigate_incident(auth_headers, client):
    """POST /quality/incidents/{id}/investigate should transition REPORTED → UNDER_INVESTIGATION."""
    # Create incident
    create_resp = client.post(
        "/api/v1/quality/incidents",
        json={
            "facility_id": "facility-qual-001",
            "incident_date": "2026-02-01T08:00:00",
            "incident_type": "MEDICATION_ERROR",
            "description": "Erreur de médication",
        },
        headers=auth_headers,
    )
    incident_id = create_resp.json()["data"]["id"]

    # Investigate
    response = client.post(
        f"/api/v1/quality/incidents/{incident_id}/investigate", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "UNDER_INVESTIGATION"


def test_resolve_incident(auth_headers, client):
    """POST /quality/incidents/{id}/resolve should transition UNDER_INVESTIGATION → RESOLVED."""
    # Create and investigate incident
    create_resp = client.post(
        "/api/v1/quality/incidents",
        json={
            "facility_id": "facility-qual-001",
            "incident_date": "2026-02-10T14:00:00",
            "incident_type": "EQUIPMENT_FAILURE",
            "description": "Défaillance d'équipement",
        },
        headers=auth_headers,
    )
    incident_id = create_resp.json()["data"]["id"]

    client.post(
        f"/api/v1/quality/incidents/{incident_id}/investigate", headers=auth_headers
    )

    # Resolve
    response = client.post(
        f"/api/v1/quality/incidents/{incident_id}/resolve", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "RESOLVED"
