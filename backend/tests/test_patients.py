"""Tests for patient CRUD endpoints."""

PATIENT_PAYLOAD = {
    "facility_id": "facility-001",
    "patient_number": "P-10001",
    "first_name": "Amadou",
    "last_name": "Diallo",
    "date_of_birth": "1990-05-15",
    "gender": "M",
    "phone": "+224 620 00 00 01",
}


def test_create_patient(auth_headers, client):
    """POST /patients should create a new patient."""
    response = client.post(
        "/api/v1/patients",
        json=PATIENT_PAYLOAD,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["first_name"] == "Amadou"
    assert data["data"]["last_name"] == "Diallo"
    assert data["data"]["patient_number"] == "P-10001"


def test_list_patients(auth_headers, client):
    """GET /patients should return a paginated list."""
    # Create a patient first
    client.post("/api/v1/patients", json=PATIENT_PAYLOAD, headers=auth_headers)

    response = client.get("/api/v1/patients", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["data"]) >= 1


def test_get_patient_by_id(auth_headers, client):
    """GET /patients/{id} should return a single patient."""
    create_resp = client.post(
        "/api/v1/patients", json=PATIENT_PAYLOAD, headers=auth_headers
    )
    patient_id = create_resp.json()["data"]["id"]

    response = client.get(
        f"/api/v1/patients/{patient_id}", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == patient_id
    assert data["data"]["first_name"] == "Amadou"


def test_patient_pagination(auth_headers, client):
    """GET /patients with page/page_size params should paginate."""
    # Create several patients
    for i in range(5):
        payload = {**PATIENT_PAYLOAD, "patient_number": f"P-2000{i}"}
        client.post("/api/v1/patients", json=payload, headers=auth_headers)

    response = client.get(
        "/api/v1/patients?page=1&page_size=2", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2


def test_patient_search(auth_headers, client):
    """GET /patients?search= should filter by name or patient number."""
    payload = {**PATIENT_PAYLOAD, "patient_number": "P-SEARCH-01", "first_name": "Searchable"}
    client.post("/api/v1/patients", json=payload, headers=auth_headers)

    response = client.get(
        "/api/v1/patients?search=Searchable", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    found = any(p["first_name"] == "Searchable" for p in data["data"])
    assert found


def test_create_patient_without_auth(client):
    """POST /patients without authentication should return 401."""
    response = client.post("/api/v1/patients", json=PATIENT_PAYLOAD)
    assert response.status_code in (401, 403)
