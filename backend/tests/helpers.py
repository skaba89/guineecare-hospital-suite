from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.modules.users.models import User


def create_super_admin_and_login(client):
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@test.com").first()
        admin_id = admin.id if admin else "unknown"
    finally:
        db.close()

    admin_token = create_access_token(subject=admin_id)
    headers = {"Authorization": f"Bearer {admin_token}"}

    user_payload = {
        "email": "admin@guineecare.com",
        "password": "StrongPassword123",
        "first_name": "Admin",
        "last_name": "Test",
        "facility_id": None,
        "role": "SUPER_ADMIN",
    }
    create_response = client.post("/api/v1/users", json=user_payload, headers=headers)
    assert create_response.status_code == 200

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
