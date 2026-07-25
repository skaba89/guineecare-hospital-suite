from app.db.session import SessionLocal
from app.modules.activity.models import ActivityEntry
from tests.helpers import create_super_admin_and_login


def test_patient_creation_records_activity(client):
    headers = create_super_admin_and_login(client)
    facility = client.post(
        "/api/v1/facilities",
        json={"code": "FAC-ACT-1", "name": "Facility Activity 1", "category": "Hospital"},
        headers=headers,
    ).json()["data"]

    response = client.post(
        "/api/v1/patients",
        json={
            "facility_id": facility["id"],
            "patient_number": "PAT-ACT-1",
            "first_name": "Test",
            "last_name": "Patient",
        },
        headers=headers,
    )

    assert response.status_code == 200

    db = SessionLocal()
    try:
        entry = db.query(ActivityEntry).filter(ActivityEntry.action_name == "patient.created").first()
        assert entry is not None
        assert entry.entity_type == "patient"
    finally:
        db.close()


def test_admission_create_and_close_record_activity(client):
    headers = create_super_admin_and_login(client)
    facility = client.post(
        "/api/v1/facilities",
        json={"code": "FAC-ACT-2", "name": "Facility Activity 2", "category": "Hospital"},
        headers=headers,
    ).json()["data"]
    patient = client.post(
        "/api/v1/patients",
        json={
            "facility_id": facility["id"],
            "patient_number": "PAT-ACT-2",
            "first_name": "Test",
            "last_name": "Admission",
        },
        headers=headers,
    ).json()["data"]

    admission = client.post(
        "/api/v1/admissions",
        json={
            "facility_id": facility["id"],
            "patient_id": patient["id"],
            "department_id": None,
            "admission_type": "CONSULTATION",
        },
        headers=headers,
    ).json()["data"]

    close_response = client.post(f"/api/v1/admissions/{admission['id']}/close", headers=headers)
    assert close_response.status_code == 200

    db = SessionLocal()
    try:
        created = db.query(ActivityEntry).filter(ActivityEntry.action_name == "admission.created").first()
        closed = db.query(ActivityEntry).filter(ActivityEntry.action_name == "admission.closed").first()
        assert created is not None
        assert closed is not None
    finally:
        db.close()
