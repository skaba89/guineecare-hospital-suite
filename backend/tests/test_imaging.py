"""Tests for imaging endpoints (orders, results)."""

PATIENT_PAYLOAD = {
    "facility_id": "facility-img-001",
    "patient_number": "P-IMG-001",
    "first_name": "Mamadou",
    "last_name": "Diallo",
    "gender": "M",
}


def _create_patient(client, auth_headers):
    """Helper: create a patient and return its id."""
    resp = client.post("/api/v1/patients", json=PATIENT_PAYLOAD, headers=auth_headers)
    return resp.json()["data"]["id"]


def test_create_imaging_order(auth_headers, client):
    """POST /imaging/orders should create an imaging order."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-img-001",
        "patient_id": patient_id,
        "exam_type": "RADIOGRAPHY",
        "body_region": "Thorax",
    }
    response = client.post(
        "/api/v1/imaging/orders", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["exam_type"] == "RADIOGRAPHY"
    assert data["data"]["body_region"] == "Thorax"
    assert data["data"]["status"] == "PENDING"


def test_list_imaging_orders(auth_headers, client):
    """GET /imaging/orders should return a list of imaging orders."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-img-001",
        "patient_id": patient_id,
        "exam_type": "ULTRASOUND",
        "body_region": "Abdomen",
    }
    client.post("/api/v1/imaging/orders", json=payload, headers=auth_headers)

    response = client.get("/api/v1/imaging/orders", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


def test_start_imaging_order(auth_headers, client):
    """POST /imaging/orders/{id}/start should transition PENDING → IN_PROGRESS."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-img-001",
        "patient_id": patient_id,
        "exam_type": "RADIOGRAPHY",
        "body_region": "Thorax",
    }
    create_resp = client.post(
        "/api/v1/imaging/orders", json=payload, headers=auth_headers
    )
    order_id = create_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/imaging/orders/{order_id}/start", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "IN_PROGRESS"


def test_complete_imaging_order(auth_headers, client):
    """POST /imaging/orders/{id}/complete should transition IN_PROGRESS → COMPLETED."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-img-001",
        "patient_id": patient_id,
        "exam_type": "RADIOGRAPHY",
        "body_region": "Thorax",
    }
    create_resp = client.post(
        "/api/v1/imaging/orders", json=payload, headers=auth_headers
    )
    order_id = create_resp.json()["data"]["id"]

    # Start the order first
    client.post(f"/api/v1/imaging/orders/{order_id}/start", headers=auth_headers)

    # Complete the order
    response = client.post(
        f"/api/v1/imaging/orders/{order_id}/complete", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "COMPLETED"


def test_create_imaging_result(auth_headers, client):
    """POST /imaging/results should create an imaging result."""
    patient_id = _create_patient(client, auth_headers)

    # Create an imaging order first
    order_resp = client.post(
        "/api/v1/imaging/orders",
        json={
            "facility_id": "facility-img-001",
            "patient_id": patient_id,
            "exam_type": "CT_SCAN",
            "body_region": "Crâne",
        },
        headers=auth_headers,
    )
    order_id = order_resp.json()["data"]["id"]

    # Create an imaging result
    result_payload = {
        "facility_id": "facility-img-001",
        "order_id": order_id,
        "patient_id": patient_id,
        "findings": "Pas d'anomalie",
    }
    response = client.post(
        "/api/v1/imaging/results", json=result_payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["findings"] == "Pas d'anomalie"
    assert data["data"]["status"] == "DRAFT"


def test_validate_imaging_result(auth_headers, client):
    """POST /imaging/results/{id}/validate should transition DRAFT → VALIDATED."""
    patient_id = _create_patient(client, auth_headers)

    # Create an imaging order
    order_resp = client.post(
        "/api/v1/imaging/orders",
        json={
            "facility_id": "facility-img-001",
            "patient_id": patient_id,
            "exam_type": "MRI",
            "body_region": "Rachis",
        },
        headers=auth_headers,
    )
    order_id = order_resp.json()["data"]["id"]

    # Create an imaging result
    result_resp = client.post(
        "/api/v1/imaging/results",
        json={
            "facility_id": "facility-img-001",
            "order_id": order_id,
            "patient_id": patient_id,
            "findings": "Disque L4-L5 protrus",
        },
        headers=auth_headers,
    )
    result_id = result_resp.json()["data"]["id"]

    # Validate the result
    response = client.post(
        f"/api/v1/imaging/results/{result_id}/validate", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "VALIDATED"
