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


def test_create_patient_with_medical_fields_defaults(auth_headers, client):
    """POST /patients sans champs médicaux → valeurs par défaut 'Non renseigné'."""
    payload = {
        "facility_id": "facility-test-001",
        "patient_number": "P-MED-DEFAULT-01",
        "first_name": "MedDefault",
        "last_name": "Patient",
        # Pas de blood_type, allergies, etc. fournis
    }
    response = client.post("/api/v1/patients", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["blood_type"] == "NON_RENSEIGNE"
    assert data["allergies"] == "Non renseigné"
    assert data["medical_history"] == "Non renseigné"
    assert data["current_medication"] == "Non renseigné"
    assert data["chronic_conditions"] == "Non renseigné"


def test_create_patient_with_explicit_medical_fields(auth_headers, client):
    """POST /patients avec champs médicaux explicites → valeurs conservées."""
    payload = {
        "facility_id": "facility-test-001",
        "patient_number": "P-MED-EXPLICIT-01",
        "first_name": "MedExplicit",
        "last_name": "Patient",
        "blood_type": "O+",
        "allergies": "Pénicilline, arachide",
        "medical_history": "Appendicectomie 2020",
        "current_medication": "Paracetamol 1g x3/j",
        "chronic_conditions": "Diabète type 2, HTA",
    }
    response = client.post("/api/v1/patients", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["blood_type"] == "O+"
    assert "Pénicilline" in data["allergies"]
    assert "Appendicectomie" in data["medical_history"]
    assert "Paracetamol" in data["current_medication"]
    assert "Diabète" in data["chronic_conditions"]


def test_get_patient_includes_medical_fields(auth_headers, client, db):
    """GET /patients/{id} retourne bien les champs médicaux."""
    # Créer un patient
    create = client.post(
        "/api/v1/patients",
        json={
            "facility_id": "facility-test-001",
            "patient_number": "P-MED-GET-01",
            "first_name": "MedGet",
            "last_name": "Patient",
            "blood_type": "A+",
            "allergies": "Iode",
        },
        headers=auth_headers,
    )
    patient_id = create.json()["data"]["id"]

    # GET
    response = client.get(f"/api/v1/patients/{patient_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["blood_type"] == "A+"
    assert data["allergies"] == "Iode"
    # Les champs non fournis ont la valeur par défaut
    assert data["medical_history"] == "Non renseigné"
    assert data["current_medication"] == "Non renseigné"
    assert data["chronic_conditions"] == "Non renseigné"
