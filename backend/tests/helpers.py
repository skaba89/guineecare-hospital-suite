def create_super_admin_and_login(client):
    user_payload = {
        "email": "admin@guineecare.test",
        "password": "StrongPassword123",
        "first_name": "Admin",
        "last_name": "Test",
        "facility_id": None,
        "role": "ADMIN",
    }
    create_response = client.post("/api/v1/users", json=user_payload)
    assert create_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
