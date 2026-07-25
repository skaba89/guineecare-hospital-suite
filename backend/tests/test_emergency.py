"""Tests for emergency endpoints."""

PATIENT_PAYLOAD = {
    "facility_id": "facility-001",
    "patient_number": "P-EMG-001",
    "first_name": "Ibrahima",
    "last_name": "Sow",
    "gender": "M",
}

VISIT_PAYLOAD = {
    "facility_id": "facility-001",
    "patient_id": "will-be-set",
    "priority_level": "NORMAL",
    "chief_complaint": "Chest pain",
}


def _create_patient(client, auth_headers):
    """Helper: create a patient and return its id."""
    resp = client.post("/api/v1/patients", json=PATIENT_PAYLOAD, headers=auth_headers)
    return resp.json()["data"]["id"]


def test_create_emergency_visit(auth_headers, client):
    """POST /emergency/visits should create a new emergency visit."""
    patient_id = _create_patient(client, auth_headers)
    payload = {**VISIT_PAYLOAD, "patient_id": patient_id}

    response = client.post(
        "/api/v1/emergency/visits", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["patient_id"] == patient_id
    assert data["data"]["chief_complaint"] == "Chest pain"
    assert data["data"]["status"] == "WAITING"


def test_get_emergency_queue(auth_headers, client):
    """GET /emergency/queue should return non-closed visits."""
    patient_id = _create_patient(client, auth_headers)
    payload = {**VISIT_PAYLOAD, "patient_id": patient_id}
    client.post("/api/v1/emergency/visits", json=payload, headers=auth_headers)

    response = client.get("/api/v1/emergency/queue", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_triage_visit(auth_headers, client):
    """POST /emergency/visits/{id}/triage should update priority and status."""
    patient_id = _create_patient(client, auth_headers)
    payload = {**VISIT_PAYLOAD, "patient_id": patient_id}
    create_resp = client.post(
        "/api/v1/emergency/visits", json=payload, headers=auth_headers
    )
    visit_id = create_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/emergency/visits/{visit_id}/triage",
        json={"priority_level": "URGENT"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["priority_level"] == "URGENT"
    assert data["data"]["status"] == "TRIAGED"


def test_orient_visit(auth_headers, client):
    """POST /emergency/visits/{id}/orientation should set orientation and orient."""
    patient_id = _create_patient(client, auth_headers)
    payload = {**VISIT_PAYLOAD, "patient_id": patient_id}
    create_resp = client.post(
        "/api/v1/emergency/visits", json=payload, headers=auth_headers
    )
    visit_id = create_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/emergency/visits/{visit_id}/orientation",
        json={"orientation": "HOSPITALIZATION"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["orientation"] == "HOSPITALIZATION"
    assert data["data"]["status"] == "ORIENTED"
