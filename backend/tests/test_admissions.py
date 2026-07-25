"""Tests for admission endpoints."""

PATIENT_PAYLOAD = {
    "facility_id": "facility-001",
    "patient_number": "P-ADM-001",
    "first_name": "Fatou",
    "last_name": "Bah",
    "gender": "F",
}

ADMISSION_PAYLOAD = {
    "facility_id": "facility-001",
    "patient_id": "will-be-set",
    "admission_type": "URGENT",
}


def _create_patient(client, auth_headers):
    """Helper: create a patient and return its id."""
    resp = client.post("/api/v1/patients", json=PATIENT_PAYLOAD, headers=auth_headers)
    return resp.json()["data"]["id"]


def test_create_admission(auth_headers, client):
    """POST /admissions should create a new admission."""
    patient_id = _create_patient(client, auth_headers)
    payload = {**ADMISSION_PAYLOAD, "patient_id": patient_id}

    response = client.post(
        "/api/v1/admissions", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["patient_id"] == patient_id
    assert data["data"]["admission_type"] == "URGENT"
    assert data["data"]["status"] == "OPEN"


def test_list_admissions(auth_headers, client):
    """GET /admissions should return a paginated list."""
    patient_id = _create_patient(client, auth_headers)
    payload = {**ADMISSION_PAYLOAD, "patient_id": patient_id}
    client.post("/api/v1/admissions", json=payload, headers=auth_headers)

    response = client.get("/api/v1/admissions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


def test_close_admission(auth_headers, client):
    """POST /admissions/{id}/close should set status to CLOSED."""
    patient_id = _create_patient(client, auth_headers)
    payload = {**ADMISSION_PAYLOAD, "patient_id": patient_id}
    create_resp = client.post(
        "/api/v1/admissions", json=payload, headers=auth_headers
    )
    admission_id = create_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/admissions/{admission_id}/close", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "CLOSED"
    assert data["data"]["closed_at"] is not None
