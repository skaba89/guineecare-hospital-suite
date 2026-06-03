from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_root():
    response = client.get("/api/v1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "GuineeCare Hospital Suite"
    assert "modules" in payload
    assert "auth" in payload["modules"]
    assert "rbac" in payload["modules"]
