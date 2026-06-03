from tests.helpers import create_super_admin_and_login


def test_super_admin_can_create_and_list_facilities(client):
    headers = create_super_admin_and_login(client)
    payload = {
        "code": "TEST-HOSPITAL",
        "name": "Test Hospital",
        "category": "Hospital",
        "region": "Conakry",
        "prefecture": "Conakry",
    }

    create_response = client.post("/api/v1/facilities", json=payload, headers=headers)
    assert create_response.status_code == 200

    list_response = client.get("/api/v1/facilities", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1


def test_super_admin_can_create_patient_after_facility(client):
    headers = create_super_admin_and_login(client)
    facility_response = client.post(
        "/api/v1/facilities",
        json={"code": "FAC-1", "name": "Facility 1", "category": "Hospital"},
        headers=headers,
    )
    facility_id = facility_response.json()["data"]["id"]

    patient_response = client.post(
        "/api/v1/patients",
        json={
            "facility_id": facility_id,
            "patient_number": "PAT-1",
            "first_name": "Mamadou",
            "last_name": "Camara",
        },
        headers=headers,
    )

    assert patient_response.status_code == 200
    assert patient_response.json()["data"]["patient_number"] == "PAT-1"


def test_super_admin_can_create_and_close_admission(client):
    headers = create_super_admin_and_login(client)
    facility = client.post(
        "/api/v1/facilities",
        json={"code": "FAC-2", "name": "Facility 2", "category": "Hospital"},
        headers=headers,
    ).json()["data"]
    patient = client.post(
        "/api/v1/patients",
        json={
            "facility_id": facility["id"],
            "patient_number": "PAT-2",
            "first_name": "Aminata",
            "last_name": "Diallo",
        },
        headers=headers,
    ).json()["data"]

    admission_response = client.post(
        "/api/v1/admissions",
        json={
            "facility_id": facility["id"],
            "patient_id": patient["id"],
            "department_id": None,
            "admission_type": "CONSULTATION",
        },
        headers=headers,
    )
    assert admission_response.status_code == 200
    admission_id = admission_response.json()["data"]["id"]

    close_response = client.post(f"/api/v1/admissions/{admission_id}/close", headers=headers)
    assert close_response.status_code == 200
    assert close_response.json()["data"]["status"] == "CLOSED"
