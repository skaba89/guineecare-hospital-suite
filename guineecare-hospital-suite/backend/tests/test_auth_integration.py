def test_login_success(client, db):
    # Create a user first so we can log in
    from app.core.security import hash_password
    from app.modules.users.models import User
    user = User(
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        first_name="Admin",
        last_name="Test",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@test.com", "password": "admin123"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"


def test_me_success(client, admin_headers):
    response = client.get("/api/v1/auth/me", headers=admin_headers)
    assert response.status_code == 200


def test_protected_route_without_token_is_rejected(client):
    response = client.get("/api/v1/patients")
    assert response.status_code in (401, 403)
