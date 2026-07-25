def create_facility(client, headers):
    response = client.post(
        "/api/v1/facilities",
        headers=headers,
        json={"code": "PHARM-HOSP", "name": "Hopital Pharmacie", "category": "HOPITAL"},
    )
    assert response.status_code == 200
    return response.json()["data"]["id"]


def test_pharmacy_stock_in_and_out(client, admin_headers):
    facility_id = create_facility(client, admin_headers)

    product_response = client.post(
        "/api/v1/pharmacy/products",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "code": "PARA-500",
            "name": "Paracetamol 500mg",
            "category": "MEDICINE",
            "form": "Tablet",
            "dosage": "500mg",
        },
    )
    assert product_response.status_code == 200
    product_id = product_response.json()["data"]["id"]

    stock_in = client.post(
        "/api/v1/pharmacy/stock/movements",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "product_id": product_id,
            "movement_type": "IN",
            "quantity": 100,
            "reason": "Initial stock",
        },
    )
    assert stock_in.status_code == 200

    stock_out = client.post(
        "/api/v1/pharmacy/stock/movements",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "product_id": product_id,
            "movement_type": "OUT",
            "quantity": 25,
            "reason": "Dispensation",
        },
    )
    assert stock_out.status_code == 200

    stock_response = client.get("/api/v1/pharmacy/stock", headers=admin_headers)
    assert stock_response.status_code == 200
    stock_rows = stock_response.json()["data"]
    assert len(stock_rows) == 1
    assert stock_rows[0]["quantity_available"] == 75
