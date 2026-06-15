from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import engine


def test_auth_login_rejects_unknown_user():
    # Ensure tables exist for this standalone test
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "bad-password"},
    )
    assert response.status_code in [401, 422]


def test_protected_patients_route_requires_token():
    Base.metadata.create_all(bind=engine)
    client = TestClient(app)
    response = client.get("/api/v1/patients")
    assert response.status_code in [401, 403]
