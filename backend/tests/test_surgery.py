"""Tests for surgery endpoints (rooms, schedules, reports)."""

PATIENT_PAYLOAD = {
    "facility_id": "facility-surg-001",
    "patient_number": "P-SURG-001",
    "first_name": "Fatoumata",
    "last_name": "Bah",
    "gender": "F",
}


def _create_patient(client, auth_headers):
    """Helper: create a patient and return its id."""
    resp = client.post("/api/v1/patients", json=PATIENT_PAYLOAD, headers=auth_headers)
    return resp.json()["data"]["id"]


def _create_operating_room(client, auth_headers):
    """Helper: create an operating room and return its id."""
    resp = client.post(
        "/api/v1/surgery/rooms",
        json={
            "facility_id": "facility-surg-001",
            "code": "OR-01",
            "name": "Salle Opératoire 1",
        },
        headers=auth_headers,
    )
    return resp.json()["data"]["id"]


def test_create_operating_room(auth_headers, client):
    """POST /surgery/rooms should create an operating room."""
    payload = {
        "facility_id": "facility-surg-001",
        "code": "OR-TEST",
        "name": "Salle Opératoire Test",
    }
    response = client.post(
        "/api/v1/surgery/rooms", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["code"] == "OR-TEST"
    assert data["data"]["name"] == "Salle Opératoire Test"
    assert data["data"]["status"] == "AVAILABLE"


def test_list_operating_rooms(auth_headers, client):
    """GET /surgery/rooms should return a list of operating rooms."""
    client.post(
        "/api/v1/surgery/rooms",
        json={
            "facility_id": "facility-surg-001",
            "code": "OR-LIST",
            "name": "Salle Opératoire List",
        },
        headers=auth_headers,
    )

    response = client.get("/api/v1/surgery/rooms", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


def test_create_surgery_schedule(auth_headers, client):
    """POST /surgery/schedules should create a surgery schedule."""
    patient_id = _create_patient(client, auth_headers)
    payload = {
        "facility_id": "facility-surg-001",
        "patient_id": patient_id,
        "procedure_name": "Appendicectomie",
    }
    response = client.post(
        "/api/v1/surgery/schedules", json=payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["procedure_name"] == "Appendicectomie"
    assert data["data"]["status"] == "SCHEDULED"


def test_start_surgery(auth_headers, client):
    """POST /surgery/schedules/{id}/start should transition SCHEDULED → IN_PROGRESS
    and mark room as OCCUPIED."""
    patient_id = _create_patient(client, auth_headers)
    room_id = _create_operating_room(client, auth_headers)

    # Create schedule with room assigned
    create_resp = client.post(
        "/api/v1/surgery/schedules",
        json={
            "facility_id": "facility-surg-001",
            "patient_id": patient_id,
            "operating_room_id": room_id,
            "procedure_name": "Cholécystectomie",
        },
        headers=auth_headers,
    )
    schedule_id = create_resp.json()["data"]["id"]

    response = client.post(
        f"/api/v1/surgery/schedules/{schedule_id}/start", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "IN_PROGRESS"

    # Room should now be OCCUPIED
    room_resp = client.get("/api/v1/surgery/rooms", headers=auth_headers)
    rooms = room_resp.json()["data"]
    target_room = [r for r in rooms if r["id"] == room_id][0]
    assert target_room["status"] == "OCCUPIED"


def test_complete_surgery(auth_headers, client):
    """POST /surgery/schedules/{id}/complete should transition IN_PROGRESS → COMPLETED
    and mark room as AVAILABLE."""
    patient_id = _create_patient(client, auth_headers)
    room_id = _create_operating_room(client, auth_headers)

    # Create and start surgery
    create_resp = client.post(
        "/api/v1/surgery/schedules",
        json={
            "facility_id": "facility-surg-001",
            "patient_id": patient_id,
            "operating_room_id": room_id,
            "procedure_name": "Herniorraphie",
        },
        headers=auth_headers,
    )
    schedule_id = create_resp.json()["data"]["id"]
    client.post(
        f"/api/v1/surgery/schedules/{schedule_id}/start", headers=auth_headers
    )

    # Complete the surgery
    response = client.post(
        f"/api/v1/surgery/schedules/{schedule_id}/complete", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "COMPLETED"

    # Room should now be AVAILABLE
    room_resp = client.get("/api/v1/surgery/rooms", headers=auth_headers)
    rooms = room_resp.json()["data"]
    target_room = [r for r in rooms if r["id"] == room_id][0]
    assert target_room["status"] == "AVAILABLE"


def test_create_surgery_report(auth_headers, client):
    """POST /surgery/reports should create a surgery report."""
    patient_id = _create_patient(client, auth_headers)

    # Create schedule
    sched_resp = client.post(
        "/api/v1/surgery/schedules",
        json={
            "facility_id": "facility-surg-001",
            "patient_id": patient_id,
            "procedure_name": "Appendicectomie",
        },
        headers=auth_headers,
    )
    schedule_id = sched_resp.json()["data"]["id"]

    # Create report
    report_payload = {
        "facility_id": "facility-surg-001",
        "schedule_id": schedule_id,
        "patient_id": patient_id,
        "operative_findings": "Appendice inflammatoire",
        "procedure_performed": "Appendicectomie par cœlioscopie",
    }
    response = client.post(
        "/api/v1/surgery/reports", json=report_payload, headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["operative_findings"] == "Appendice inflammatoire"
    assert data["data"]["status"] == "DRAFT"


def test_validate_surgery_report(auth_headers, client):
    """POST /surgery/reports/{id}/validate should transition DRAFT → VALIDATED."""
    patient_id = _create_patient(client, auth_headers)

    # Create schedule
    sched_resp = client.post(
        "/api/v1/surgery/schedules",
        json={
            "facility_id": "facility-surg-001",
            "patient_id": patient_id,
            "procedure_name": "Césarienne",
        },
        headers=auth_headers,
    )
    schedule_id = sched_resp.json()["data"]["id"]

    # Create report
    report_resp = client.post(
        "/api/v1/surgery/reports",
        json={
            "facility_id": "facility-surg-001",
            "schedule_id": schedule_id,
            "patient_id": patient_id,
        },
        headers=auth_headers,
    )
    report_id = report_resp.json()["data"]["id"]

    # Validate the report
    response = client.post(
        f"/api/v1/surgery/reports/{report_id}/validate", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "VALIDATED"
