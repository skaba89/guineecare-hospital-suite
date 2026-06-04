def create_facility_and_patient(client, headers):
    facility_response = client.post(
        "/api/v1/facilities",
        headers=headers,
        json={"code": "LAB-HOSP", "name": "Hopital Labo", "category": "HOPITAL"},
    )
    assert facility_response.status_code == 200
    facility_id = facility_response.json()["data"]["id"]

    patient_response = client.post(
        "/api/v1/patients",
        headers=headers,
        json={
            "facility_id": facility_id,
            "patient_number": "LAB-PAT-001",
            "first_name": "Aminata",
            "last_name": "Diallo",
        },
    )
    assert patient_response.status_code == 200
    patient_id = patient_response.json()["data"]["id"]
    return facility_id, patient_id


def test_laboratory_order_result_validation(client, admin_headers):
    facility_id, patient_id = create_facility_and_patient(client, admin_headers)

    test_response = client.post(
        "/api/v1/laboratory/tests",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "code": "TEST-001",
            "name": "Generic Lab Test",
            "category": "GENERAL",
            "sample_type": "Sample",
        },
    )
    assert test_response.status_code == 200
    test_id = test_response.json()["data"]["id"]

    order_response = client.post(
        "/api/v1/laboratory/orders",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "patient_id": patient_id,
            "test_id": test_id,
            "priority": "NORMAL",
        },
    )
    assert order_response.status_code == 200
    order_id = order_response.json()["data"]["id"]

    result_response = client.post(
        f"/api/v1/laboratory/orders/{order_id}/results",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "result_value": "OK",
            "interpretation": "Standard",
        },
    )
    assert result_response.status_code == 200
    result_id = result_response.json()["data"]["id"]

    validate_response = client.post(
        f"/api/v1/laboratory/results/{result_id}/validate",
        headers=admin_headers,
    )
    assert validate_response.status_code == 200
    assert validate_response.json()["data"]["status"] == "VALIDATED"
