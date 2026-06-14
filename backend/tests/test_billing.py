"""Tests for billing endpoints (tariffs, invoices, payments)."""

TARIFF_PAYLOAD = {
    "facility_id": "facility-001",
    "code": "CONSULT-01",
    "name": "General Consultation",
    "category": "CONSULTATION",
    "unit_price": 25000.0,
}

PATIENT_PAYLOAD = {
    "facility_id": "facility-001",
    "patient_number": "P-BIL-001",
    "first_name": "Kadiatou",
    "last_name": "Sylla",
    "gender": "F",
}


def _create_patient(client, auth_headers):
    """Helper: create a patient and return its id."""
    resp = client.post("/api/v1/patients", json=PATIENT_PAYLOAD, headers=auth_headers)
    return resp.json()["data"]["id"]


def test_create_tariff(auth_headers, client):
    """POST /billing/tariffs should create a tariff item."""
    response = client.post(
        "/api/v1/billing/tariffs", json=TARIFF_PAYLOAD, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["code"] == "CONSULT-01"
    assert data["data"]["unit_price"] == 25000.0


def test_create_invoice(auth_headers, client):
    """POST /billing/invoices should create an invoice."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-001",
        "patient_id": patient_id,
        "invoice_number": "INV-2025-001",
        "description": "Consultation and lab tests",
        "net_amount": 50000.0,
    }

    response = client.post(
        "/api/v1/billing/invoices", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["invoice_number"] == "INV-2025-001"
    assert data["data"]["status"] == "ISSUED"
    assert data["data"]["balance_due"] == 50000.0


def test_create_payment(auth_headers, client):
    """POST /billing/invoices/{id}/payments should record a payment."""
    patient_id = _create_patient(client, auth_headers)

    # Create invoice
    inv_resp = client.post(
        "/api/v1/billing/invoices",
        json={
            "facility_id": "facility-001",
            "patient_id": patient_id,
            "invoice_number": "INV-2025-002",
            "net_amount": 75000.0,
        },
        headers=auth_headers,
    )
    invoice_id = inv_resp.json()["data"]["id"]

    # Make a partial payment
    response = client.post(
        f"/api/v1/billing/invoices/{invoice_id}/payments",
        json={
            "facility_id": "facility-001",
            "amount": 30000.0,
            "payment_method": "CASH",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["payment"]["amount"] == 30000.0
    assert data["data"]["invoice"]["paid_amount"] == 30000.0


def test_invoice_status_auto_update(auth_headers, client):
    """Invoice status should auto-update to PAID when balance is zero."""
    patient_id = _create_patient(client, auth_headers)

    # Create invoice
    inv_resp = client.post(
        "/api/v1/billing/invoices",
        json={
            "facility_id": "facility-001",
            "patient_id": patient_id,
            "invoice_number": "INV-2025-003",
            "net_amount": 50000.0,
        },
        headers=auth_headers,
    )
    invoice_id = inv_resp.json()["data"]["id"]

    # Pay the full amount
    response = client.post(
        f"/api/v1/billing/invoices/{invoice_id}/payments",
        json={
            "facility_id": "facility-001",
            "amount": 50000.0,
            "payment_method": "MOBILE_MONEY",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["invoice"]["status"] == "PAID"
    assert data["data"]["invoice"]["balance_due"] == 0
