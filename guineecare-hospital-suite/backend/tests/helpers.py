from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.modules.users.models import User


def create_super_admin_and_login(client):
    """Create a SUPER_ADMIN user directly in DB, then login to get a valid JWT."""
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.email == "admin@guineecare.com").first()
        if not admin:
            admin = User(
                email="admin@guineecare.com",
                password_hash=hash_password("StrongPassword123"),
                first_name="Admin",
                last_name="Test",
                role="SUPER_ADMIN",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
    finally:
        db.close()

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@guineecare.com", "password": "StrongPassword123"},
    )
    assert login_response.status_code == 200, f"Login failed: {login_response.text}"
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
