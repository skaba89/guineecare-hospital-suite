"""Tests for pharmacy endpoints (products, stock movements)."""

PRODUCT_PAYLOAD = {
    "facility_id": "facility-001",
    "code": "PARA-500",
    "name": "Paracetamol 500mg",
    "category": "ANALGESIC",
    "form": "TABLET",
    "dosage": "500mg",
}


def _create_product(client, auth_headers):
    """Helper: create a pharmacy product and return its id."""
    resp = client.post(
        "/api/v1/pharmacy/products", json=PRODUCT_PAYLOAD, headers=auth_headers
    )
    return resp.json()["data"]["id"]


def test_create_product(auth_headers, client):
    """POST /pharmacy/products should create a new product."""
    response = client.post(
        "/api/v1/pharmacy/products", json=PRODUCT_PAYLOAD, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["code"] == "PARA-500"
    assert data["data"]["name"] == "Paracetamol 500mg"


def test_stock_movement_in(auth_headers, client):
    """POST /pharmacy/stock/movements with type IN should increase stock."""
    product_id = _create_product(client, auth_headers)
    payload = {
        "facility_id": "facility-001",
        "product_id": product_id,
        "movement_type": "IN",
        "quantity": 100,
        "reason": "Initial stock",
    }

    response = client.post(
        "/api/v1/pharmacy/stock/movements", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["stock"]["quantity_available"] == 100


def test_stock_movement_out(auth_headers, client):
    """POST /pharmacy/stock/movements with type OUT should decrease stock."""
    product_id = _create_product(client, auth_headers)

    # First, add stock
    client.post(
        "/api/v1/pharmacy/stock/movements",
        json={
            "facility_id": "facility-001",
            "product_id": product_id,
            "movement_type": "IN",
            "quantity": 100,
            "reason": "Initial stock",
        },
        headers=auth_headers,
    )

    # Then, dispense some
    response = client.post(
        "/api/v1/pharmacy/stock/movements",
        json={
            "facility_id": "facility-001",
            "product_id": product_id,
            "movement_type": "OUT",
            "quantity": 30,
            "reason": "Dispensed to patient",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["stock"]["quantity_available"] == 70


def test_stock_movement_insufficient(auth_headers, client):
    """POST /pharmacy/stock/movements with OUT exceeding stock should fail."""
    product_id = _create_product(client, auth_headers)

    # Add a small amount
    client.post(
        "/api/v1/pharmacy/stock/movements",
        json={
            "facility_id": "facility-001",
            "product_id": product_id,
            "movement_type": "IN",
            "quantity": 10,
            "reason": "Small stock",
        },
        headers=auth_headers,
    )

    # Try to dispense more than available
    response = client.post(
        "/api/v1/pharmacy/stock/movements",
        json={
            "facility_id": "facility-001",
            "product_id": product_id,
            "movement_type": "OUT",
            "quantity": 50,
            "reason": "Too much",
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
