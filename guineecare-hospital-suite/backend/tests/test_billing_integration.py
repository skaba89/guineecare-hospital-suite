def create_facility_and_patient(client, headers):
    facility_response = client.post(
        "/api/v1/facilities",
        headers=headers,
        json={"code": "BILL-HOSP", "name": "Hopital Facturation", "category": "HOPITAL"},
    )
    assert facility_response.status_code == 200
    facility_id = facility_response.json()["data"]["id"]

    patient_response = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "facility_id": facility_id,
            "patient_number": "BILL-PAT-001",
            "first_name": "Ibrahima",
            "last_name": "Bah",
        },
    )
    assert patient_response.status_code == 200
    patient_id = patient_response.json()["data"]["id"]
    return facility_id, patient_id


def test_billing_invoice_payment_receipt(client, admin_headers):
    facility_id, patient_id = create_facility_and_patient(client, admin_headers)

    tariff_response = client.post(
        "/api/v1/billing/tariffs",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "code": "CONS-001",
            "name": "Consultation",
            "category": "CONSULTATION",
            "unit_price": 50000,
        },
    )
    assert tariff_response.status_code == 200

    invoice_response = client.post(
        "/api/v1/billing/invoices",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "patient_id": patient_id,
            "invoice_number": "INV-TEST-001",
            "description": "Test invoice",
            "net_amount": 50000,
        },
    )
    assert invoice_response.status_code == 200
    invoice_id = invoice_response.json()["data"]["id"]
    assert invoice_response.json()["data"]["balance_due"] == 50000

    payment_response = client.post(
        f"/api/v1/billing/invoices/{invoice_id}/payments",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "amount": 50000,
            "payment_method": "CASH",
        },
    )
    assert payment_response.status_code == 200
    payment_id = payment_response.json()["data"]["payment"]["id"]
    assert payment_response.json()["data"]["invoice"]["status"] == "PAID"

    receipt_response = client.get(
        f"/api/v1/billing/payments/{payment_id}/receipt",
        headers=admin_headers,
    )
    assert receipt_response.status_code == 200
    assert receipt_response.json()["data"]["payment_id"] == payment_id
