import os

# ── Set test environment variables BEFORE importing any app modules ──
os.environ["AUTH_SECRET"] = "test-secret-key-for-integration-tests"
os.environ["DATABASE_URL"] = "sqlite:///./test_guineecare.db"
os.environ["ENVIRONMENT"] = "local"
os.environ.pop("SEED_DEMO_DATA", None)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.security import hash_password, create_access_token
from app.core.limiter import limiter

# Import all models so Base.metadata.create_all creates every table
from app.modules.facilities.models import Facility
from app.modules.departments.models import Department
from app.modules.patients.models import Patient
from app.modules.admissions.models import Admission
from app.modules.users.models import User
from app.modules.rbac.models import Role, Permission, RolePermission
from app.modules.activity.models import ActivityEntry
from app.modules.auth.models import RefreshToken, AuditLog
from app.modules.emergency.models import EmergencyVisit
from app.modules.pharmacy.models import PharmacyProduct, PharmacyStock, StockMovement
from app.modules.laboratory.models import LabTest, LabOrder, LabResult
from app.modules.billing.models import TariffItem, Invoice, Payment
from app.modules.clinical.models import ClinicalNote, PatientMeasurement, Diagnosis
from app.modules.hospitalization.models import Room, Bed, HospitalStay
from app.modules.maternity.models import MaternityRecord, MaternityConsultation, DeliveryRecord
from app.modules.personnel.models import StaffMember, OnCallSchedule
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.surgery.models import OperatingRoom, SurgerySchedule, SurgeryTeamMember, SurgeryReport
from app.modules.quality.models import QualityIndicator, QualityMeasurement, IncidentReport
from app.modules.reporting.models import NationalReport, EpidemicAlert, HealthStatistic
from app.modules.notifications.models import Notification

# Use SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_guineecare.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """Reset the slowapi rate limiter storage before each test."""
    limiter._limiter.storage.reset()
    yield


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client, db):
    """Create a test user directly in DB and return auth headers.

    Bypasses the login endpoint to avoid rate-limit interference.
    """
    user = User(
        email="test@admin.com",
        password_hash=hash_password("testpassword123"),
        first_name="Test",
        last_name="Admin",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        subject=user.id,
        facility_id=user.facility_id,
        role=user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, db):
    """SUPER_ADMIN with valid JWT including facility_id and role."""
    user = User(
        email="admin@test.com",
        password_hash=hash_password("testpassword123"),
        first_name="Admin",
        last_name="Admin",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(
        subject=user.id,
        facility_id=user.facility_id,
        role=user.role,
    )
    return {"Authorization": f"Bearer {token}"}
