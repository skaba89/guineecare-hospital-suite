from tests.helpers import create_super_admin_and_login


def test_login_rejects_unknown_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "unknown@example.com", "password": "bad-password"},
    )
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_first_user_can_login_and_call_me(client):
    headers = create_super_admin_and_login(client)

    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == "admin@guineecare.test"
    assert payload["role"] == "SUPER_ADMIN"


def test_login_rejects_invalid_password(client):
    create_super_admin_and_login(client)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@guineecare.test", "password": "bad-password"},
    )

    assert response.status_code == 401
