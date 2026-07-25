def test_patient_admission_lifecycle(client, admin_headers):
    facility_response = client.post(
        "/api/v1/facilities",
        headers=admin_headers,
        json={
            "code": "TEST-HOSP",
            "name": "Hopital Test",
            "category": "HOPITAL",
            "region": "Conakry",
            "prefecture": "Conakry",
        },
    )
    assert facility_response.status_code == 200
    facility_id = facility_response.json()["data"]["id"]

    department_response = client.post(
        "/api/v1/departments",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "code": "MED",
            "name": "Medecine generale",
            "category": "CLINICAL",
        },
    )
    assert department_response.status_code == 200
    department_id = department_response.json()["data"]["id"]

    patient_response = client.post(
        "/api/v1/patients",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "patient_number": "PAT-TEST-001",
            "first_name": "Mamadou",
            "last_name": "Camara",
        },
    )
    assert patient_response.status_code == 200
    patient_id = patient_response.json()["data"]["id"]

    admission_response = client.post(
        "/api/v1/admissions",
        headers=admin_headers,
        json={
            "facility_id": facility_id,
            "patient_id": patient_id,
            "department_id": department_id,
            "admission_type": "CONSULTATION",
        },
    )
    assert admission_response.status_code == 200
    admission_id = admission_response.json()["data"]["id"]
    assert admission_response.json()["data"]["status"] == "OPEN"

    close_response = client.post(
        f"/api/v1/admissions/{admission_id}/close",
        headers=admin_headers,
    )
    assert close_response.status_code == 200
    assert close_response.json()["data"]["status"] == "CLOSED"
