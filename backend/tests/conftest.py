import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_guineecare.db")
os.environ.setdefault("AUTH_SECRET", "test-secret")

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.modules.rbac.models import Permission, Role, RolePermission
from app.modules.users.models import User


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_security(db)
    finally:
        db.close()
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def admin_headers():
    token = create_access_token("admin@test.local")
    return {"Authorization": f"Bearer {token}"}


def seed_security(db):
    admin = db.query(User).filter(User.email == "admin@test.local").first()
    if not admin:
        db.add(User(
            facility_id="facility-test",
            email="admin@test.local",
            password_hash=hash_password("admin123"),
            first_name="Admin",
            last_name="Test",
            role="SUPER_ADMIN",
            is_active=True,
        ))

    roles = ["SUPER_ADMIN", "ADMIN", "DOCTOR", "NURSE", "PHARMACIST", "LAB_TECH", "CASHIER"]
    for code in roles:
        if not db.query(Role).filter(Role.code == code).first():
            db.add(Role(code=code, name=code, description=f"{code} role"))

    permissions = [
        "facility.read",
        "facility.manage",
        "department.read",
        "department.manage",
        "patient.read",
        "patient.create",
        "admission.read",
        "admission.create",
        "admission.close",
        "emergency.read",
        "emergency.create",
        "emergency.triage",
        "emergency.orient",
        "pharmacy.read",
        "pharmacy.manage",
        "laboratory.read",
        "laboratory.manage",
        "billing.read",
        "billing.manage",
        "billing.payment",
    ]
    for code in permissions:
        if not db.query(Permission).filter(Permission.code == code).first():
            db.add(Permission(code=code, name=code, module=code.split(".")[0]))
        if not db.query(RolePermission).filter(
            RolePermission.role_code == "SUPER_ADMIN",
            RolePermission.permission_code == code,
        ).first():
            db.add(RolePermission(role_code="SUPER_ADMIN", permission_code=code))

    db.commit()
