"""Tests for authentication endpoints."""


def test_bootstrap_creates_first_admin(client):
    """Bootstrap endpoint should create the first SUPER_ADMIN user."""
    response = client.post(
        "/api/v1/users/bootstrap",
        json={
            "email": "admin@hospital.com",
            "password": "SecurePassword1!xx",
            "first_name": "Admin",
            "last_name": "User",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["email"] == "admin@hospital.com"
    assert data["data"]["role"] == "SUPER_ADMIN"


def test_bootstrap_fails_if_users_exist(client):
    """Bootstrap should fail once a user already exists."""
    # Create the first user
    client.post(
        "/api/v1/users/bootstrap",
        json={
            "email": "first@admin.com",
            "password": "SecurePassword1!xx",
            "first_name": "First",
            "last_name": "Admin",
        },
    )
    # Try to bootstrap again
    response = client.post(
        "/api/v1/users/bootstrap",
        json={
            "email": "second@admin.com",
            "password": "SecurePassword1!xx",
            "first_name": "Second",
            "last_name": "Admin",
        },
    )
    assert response.status_code == 403


def test_login_success(client):
    """Login with correct credentials should return an access token."""
    client.post(
        "/api/v1/users/bootstrap",
        json={
            "email": "login@test.com",
            "password": "MyPassword1!xx",
            "first_name": "Login",
            "last_name": "Test",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "login@test.com", "password": "MyPassword1!xx"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login@test.com"


def test_login_wrong_password(client):
    """Login with wrong password should return 401."""
    client.post(
        "/api/v1/users/bootstrap",
        json={
            "email": "wrong@test.com",
            "password": "CorrectPassword1!xx",
            "first_name": "Wrong",
            "last_name": "Test",
        },
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@test.com", "password": "BadPassword1!xx"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client):
    """Login with a non-existent email should return 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "Anything1!xx"},
    )
    assert response.status_code == 401


def test_get_current_user(auth_headers, client):
    """GET /auth/me should return the authenticated user's info."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@admin.com"
    assert data["role"] == "SUPER_ADMIN"


def test_get_current_user_no_token(client):
    """GET /auth/me without a token should return 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code in (401, 403)
