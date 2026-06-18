from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_patients_without_token_is_rejected():
    response = client.get("/api/v1/patients")
    assert response.status_code == 401


def test_admissions_without_token_is_rejected():
    response = client.get("/api/v1/admissions")
    assert response.status_code == 401


def test_facilities_without_token_is_rejected():
    response = client.get("/api/v1/facilities")
    assert response.status_code == 401


def test_departments_without_token_is_rejected():
    response = client.get("/api/v1/departments")
    assert response.status_code == 401
