"""Tests for clinical DPI endpoints (notes, measurements, diagnoses)."""

PATIENT_PAYLOAD = {
    "facility_id": "facility-001",
    "patient_number": "P-CLN-001",
    "first_name": "Mariama",
    "last_name": "Conte",
    "gender": "F",
}


def _create_patient(client, auth_headers):
    """Helper: create a patient and return its id."""
    resp = client.post("/api/v1/patients", json=PATIENT_PAYLOAD, headers=auth_headers)
    return resp.json()["data"]["id"]


# ── Clinical Notes ─────────────────────────────────────────────


def test_create_clinical_note(auth_headers, client):
    """POST /clinical/patients/{id}/notes should create a note."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-001",
        "note_type": "OBSERVATION",
        "content": "Patient presents with mild fever.",
    }

    response = client.post(
        f"/api/v1/clinical/patients/{patient_id}/notes",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["note_type"] == "OBSERVATION"
    assert data["data"]["content"] == "Patient presents with mild fever."


def test_list_clinical_notes(auth_headers, client):
    """GET /clinical/patients/{id}/notes should return notes for a patient."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-001",
        "note_type": "CONSULTATION",
        "content": "Follow-up consultation note.",
    }
    client.post(
        f"/api/v1/clinical/patients/{patient_id}/notes",
        json=payload,
        headers=auth_headers,
    )

    response = client.get(
        f"/api/v1/clinical/patients/{patient_id}/notes",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


# ── Measurements ───────────────────────────────────────────────


def test_create_measurement(auth_headers, client):
    """POST /clinical/patients/{id}/measurements should record a measurement."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-001",
        "measurement_type": "TEMPERATURE",
        "value": "38.5",
        "unit": "°C",
    }

    response = client.post(
        f"/api/v1/clinical/patients/{patient_id}/measurements",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["measurement_type"] == "TEMPERATURE"
    assert data["data"]["value"] == "38.5"


def test_list_measurements(auth_headers, client):
    """GET /clinical/patients/{id}/measurements should return measurements."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-001",
        "measurement_type": "BLOOD_PRESSURE",
        "value": "120/80",
        "unit": "mmHg",
    }
    client.post(
        f"/api/v1/clinical/patients/{patient_id}/measurements",
        json=payload,
        headers=auth_headers,
    )

    response = client.get(
        f"/api/v1/clinical/patients/{patient_id}/measurements",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


# ── Diagnoses ─────────────────────────────────────────────────


def test_create_diagnosis(auth_headers, client):
    """POST /clinical/patients/{id}/diagnoses should create a diagnosis."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-001",
        "diagnosis_code": "J18.9",
        "diagnosis_label": "Pneumonia, unspecified",
        "diagnosis_type": "PRINCIPAL",
        "status": "ACTIVE",
    }

    response = client.post(
        f"/api/v1/clinical/patients/{patient_id}/diagnoses",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["diagnosis_code"] == "J18.9"
    assert data["data"]["diagnosis_type"] == "PRINCIPAL"


def test_list_diagnoses(auth_headers, client):
    """GET /clinical/patients/{id}/diagnoses should return diagnoses."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-001",
        "diagnosis_label": "Hypertension",
        "diagnosis_type": "SECONDARY",
    }
    client.post(
        f"/api/v1/clinical/patients/{patient_id}/diagnoses",
        json=payload,
        headers=auth_headers,
    )

    response = client.get(
        f"/api/v1/clinical/patients/{patient_id}/diagnoses",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
