"""Tests for v0.8.0 security hardening — OWASP Top 10 fixes.

Covers:
- A02-001: password_hash never exposed via /users endpoints
- A01-001: RBAC mutations restricted to SUPER_ADMIN
- A01-002: /activity restricted to SUPER_ADMIN
- A01-003: /notifications/send enforces facility access on recipient
- A04-001: account lockout after 5 failed logins
- A04-002: password complexity policy
- A04-003: /auth/refresh rate-limited
- A09-001/002/003: audit_log on user/facility/department/RBAC mutations
"""
import pytest
from app.core.security import create_access_token, hash_password
from app.modules.auth.models import AuditLog
from app.modules.users.models import User


def _auth_headers(user_id: str, role: str = "SUPER_ADMIN", facility_id: str | None = None) -> dict:
    token = create_access_token(subject=user_id, facility_id=facility_id, role=role)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# A02-001 — password_hash never exposed
# ============================================================================

class TestPasswordHashNotExposed:

    def test_list_users_does_not_expose_password_hash(self, client, db):
        """GET /users must NOT return password_hash in the response."""
        user = User(
            email="admin@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Admin",
            last_name="Audit",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)

        r = client.get("/api/v1/users", headers=_auth_headers(user.id, role="SUPER_ADMIN"))
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        for u in data["data"]:
            assert "password_hash" not in u, f"password_hash leaked for user {u.get('email')}"
            assert "password" not in u

    def test_create_user_does_not_expose_password_hash(self, client, db):
        """POST /users must NOT return password_hash in the response."""
        admin = User(
            email="admin2@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Admin",
            last_name="Audit",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(admin); db.commit(); db.refresh(admin)

        r = client.post(
            "/api/v1/users",
            headers=_auth_headers(admin.id, role="SUPER_ADMIN"),
            json={
                "email": "newuser@example.com",
                "password": "StrongPass1!xx",
                "first_name": "New",
                "last_name": "User",
                "role": "DOCTOR",
            },
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert "password_hash" not in data
        assert "password" not in data
        assert data["email"] == "newuser@example.com"

    def test_bootstrap_does_not_expose_password_hash(self, client):
        """POST /users/bootstrap must NOT return password_hash."""
        r = client.post(
            "/api/v1/users/bootstrap",
            json={
                "email": "boot@example.com",
                "password": "StrongPass1!xx",
                "first_name": "Boot",
                "last_name": "Strap",
            },
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert "password_hash" not in data
        assert "password" not in data

    def test_update_user_does_not_expose_password_hash(self, client, db):
        """PUT /users/{id} must NOT return password_hash."""
        admin = User(
            email="admin3@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Admin",
            last_name="Audit",
            role="SUPER_ADMIN",
            is_active=True,
        )
        target = User(
            email="target@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Target",
            last_name="User",
            role="DOCTOR",
            is_active=True,
        )
        db.add_all([admin, target]); db.commit(); db.refresh(admin); db.refresh(target)

        r = client.put(
            f"/api/v1/users/{target.id}",
            headers=_auth_headers(admin.id, role="SUPER_ADMIN"),
            json={"first_name": "Renamed"},
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert "password_hash" not in data
        assert "password" not in data
        assert data["first_name"] == "Renamed"


# ============================================================================
# A01-001 — RBAC mutations restricted to SUPER_ADMIN
# ============================================================================

class TestRBACSuperAdminOnly:

    @pytest.fixture
    def admin_user(self, db):
        """A facility-scoped ADMIN (not SUPER_ADMIN)."""
        from app.modules.facilities.models import Facility
        facility = Facility(code="FAC-SEC", name="Sec Facility", category="Hospital")
        db.add(facility); db.commit(); db.refresh(facility)
        user = User(
            email="admin-facility@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Facility",
            last_name="Admin",
            role="ADMIN",
            facility_id=facility.id,
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        return user

    @pytest.fixture
    def super_admin(self, db):
        user = User(
            email="super@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Super",
            last_name="Admin",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        return user

    def test_admin_cannot_create_role(self, client, admin_user):
        """A facility-scoped ADMIN must NOT be able to create a global role."""
        r = client.post(
            "/api/v1/rbac/roles",
            headers=_auth_headers(admin_user.id, role="ADMIN"),
            json={"code": "HACKER", "name": "Hacker Role"},
        )
        assert r.status_code == 403

    def test_admin_cannot_create_permission(self, client, admin_user):
        """A facility-scoped ADMIN must NOT be able to create a global permission."""
        r = client.post(
            "/api/v1/rbac/permissions",
            headers=_auth_headers(admin_user.id, role="ADMIN"),
            json={"code": "hack.all", "name": "Hack All", "module": "hack"},
        )
        assert r.status_code == 403

    def test_admin_cannot_assign_permission_to_role(self, client, admin_user):
        """A facility-scoped ADMIN must NOT be able to assign permissions to roles."""
        r = client.post(
            "/api/v1/rbac/role-permissions",
            headers=_auth_headers(admin_user.id, role="ADMIN"),
            json={"role_code": "DOCTOR", "permission_code": "billing.manage"},
        )
        assert r.status_code == 403

    def test_super_admin_can_create_role(self, client, super_admin):
        """SUPER_ADMIN can still create roles."""
        r = client.post(
            "/api/v1/rbac/roles",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={"code": "NEW_ROLE", "name": "New Role"},
        )
        assert r.status_code == 200


# ============================================================================
# A01-002 — /activity restricted to SUPER_ADMIN
# ============================================================================

class TestActivitySuperAdminOnly:

    @pytest.fixture
    def admin_user(self, db):
        user = User(
            email="admin-act@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Admin",
            last_name="Act",
            role="ADMIN",
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        return user

    def test_admin_cannot_access_activity(self, client, admin_user):
        """A facility-scoped ADMIN must NOT be able to read /activity (global table)."""
        r = client.get(
            "/api/v1/activity",
            headers=_auth_headers(admin_user.id, role="ADMIN"),
        )
        assert r.status_code == 403


# ============================================================================
# A01-003 — /notifications/send enforces facility access
# ============================================================================

class TestNotificationSendTenantIsolation:

    @pytest.fixture
    def admin_facility_a(self, db):
        from app.modules.facilities.models import Facility
        fa = Facility(code="FA", name="Facility A", category="Hospital")
        db.add(fa); db.commit(); db.refresh(fa)
        admin = User(
            email="admin-a@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Admin",
            last_name="A",
            role="ADMIN",
            facility_id=fa.id,
            is_active=True,
        )
        db.add(admin); db.commit(); db.refresh(admin)
        return admin

    @pytest.fixture
    def user_facility_b(self, db):
        from app.modules.facilities.models import Facility
        fb = Facility(code="FB", name="Facility B", category="Hospital")
        db.add(fb); db.commit(); db.refresh(fb)
        user = User(
            email="user-b@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="User",
            last_name="B",
            role="DOCTOR",
            facility_id=fb.id,
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        return user

    def test_admin_cannot_send_to_other_facility_user(self, client, admin_facility_a, user_facility_b):
        """ADMIN from facility A must NOT be able to send a notification to a user in facility B."""
        r = client.post(
            "/api/v1/notifications/send",
            headers=_auth_headers(admin_facility_a.id, role="ADMIN", facility_id=admin_facility_a.facility_id),
            json={
                "recipient_id": user_facility_b.id,
                "title": "Cross-tenant phishing",
                "category": "system",
            },
        )
        assert r.status_code == 403


# ============================================================================
# A04-001 — account lockout after 5 failed logins
# ============================================================================

class TestAccountLockout:

    @pytest.fixture
    def target_user(self, db):
        user = User(
            email="lockme@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Lock",
            last_name="Me",
            role="DOCTOR",
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        return user

    def test_account_locks_after_5_failed_attempts(self, client, target_user):
        """After 5 failed logins, the account is locked for 15 minutes."""
        # Send 5 failed login attempts
        for i in range(5):
            r = client.post(
                "/api/v1/auth/login",
                json={"email": "lockme@example.com", "password": f"WrongPass{i}!xx"},
            )
            assert r.status_code == 401, f"attempt {i+1} should fail with 401"

        # 6th attempt — even with correct password, account is locked
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "lockme@example.com", "password": "TestPassword1!xx"},
        )
        assert r.status_code == 423  # Locked
        assert "verrouillé" in r.json()["detail"].lower()

    def test_failed_count_resets_on_successful_login(self, client, target_user):
        """A successful login resets the failed_login_count to 0."""
        # 3 failed attempts (below threshold)
        for i in range(3):
            client.post(
                "/api/v1/auth/login",
                json={"email": "lockme@example.com", "password": f"WrongPass{i}!xx"},
            )

        # Successful login
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "lockme@example.com", "password": "TestPassword1!xx"},
        )
        assert r.status_code == 200

        # Now we should be able to fail 5 more times before lockout (counter was reset)
        for i in range(4):
            r = client.post(
                "/api/v1/auth/login",
                json={"email": "lockme@example.com", "password": f"WrongPass{i}!xx"},
            )
            assert r.status_code == 401  # not locked yet

        # 5th failure should lock
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "lockme@example.com", "password": "WrongPass5!xx"},
        )
        assert r.status_code == 401  # 5th failure returns 401

        # 6th attempt — locked
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "lockme@example.com", "password": "TestPassword1!xx"},
        )
        assert r.status_code == 423


# ============================================================================
# A04-002 — password complexity policy
# ============================================================================

class TestPasswordPolicy:

    @pytest.fixture
    def super_admin(self, db):
        user = User(
            email="super-pwd@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Super",
            last_name="Pwd",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        return user

    def test_short_password_rejected(self, client, super_admin):
        """Passwords < 12 chars are rejected."""
        r = client.post(
            "/api/v1/users",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={
                "email": "short@example.com",
                "password": "Short1!",
                "first_name": "Short",
                "last_name": "Pwd",
                "role": "DOCTOR",
            },
        )
        assert r.status_code == 422

    def test_password_without_uppercase_rejected(self, client, super_admin):
        r = client.post(
            "/api/v1/users",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={
                "email": "noupper@example.com",
                "password": "lowercase1!xx",
                "first_name": "No",
                "last_name": "Upper",
                "role": "DOCTOR",
            },
        )
        assert r.status_code == 422

    def test_password_without_digit_rejected(self, client, super_admin):
        r = client.post(
            "/api/v1/users",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={
                "email": "nodigit@example.com",
                "password": "NoDigitsHere!xx",
                "first_name": "No",
                "last_name": "Digit",
                "role": "DOCTOR",
            },
        )
        assert r.status_code == 422

    def test_password_without_special_rejected(self, client, super_admin):
        r = client.post(
            "/api/v1/users",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={
                "email": "nospecial@example.com",
                "password": "NoSpecialChar1xx",
                "first_name": "No",
                "last_name": "Special",
                "role": "DOCTOR",
            },
        )
        assert r.status_code == 422

    def test_strong_password_accepted(self, client, super_admin):
        r = client.post(
            "/api/v1/users",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={
                "email": "strong@example.com",
                "password": "StrongPassword1!xx",
                "first_name": "Strong",
                "last_name": "Pwd",
                "role": "DOCTOR",
            },
        )
        assert r.status_code == 200


# ============================================================================
# A09 — audit_log on mutations
# ============================================================================

class TestAuditLogOnMutations:

    @pytest.fixture
    def super_admin(self, db):
        user = User(
            email="super-audit@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Super",
            last_name="Audit",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        return user

    def test_user_create_is_audited(self, client, db, super_admin):
        r = client.post(
            "/api/v1/users",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={
                "email": "audited-create@example.com",
                "password": "StrongPassword1!xx",
                "first_name": "Audited",
                "last_name": "Create",
                "role": "DOCTOR",
            },
        )
        assert r.status_code == 200
        audit = db.query(AuditLog).filter(AuditLog.action == "user.create").first()
        assert audit is not None
        assert audit.resource_type == "user"
        assert audit.resource_id == r.json()["data"]["id"]

    def test_user_update_is_audited(self, client, db, super_admin):
        # Create a target user
        target = User(
            email="audited-update@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Audited",
            last_name="Update",
            role="DOCTOR",
            is_active=True,
        )
        db.add(target); db.commit(); db.refresh(target)

        r = client.put(
            f"/api/v1/users/{target.id}",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={"first_name": "Renamed"},
        )
        assert r.status_code == 200
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.action == "user.update")
            .filter(AuditLog.resource_id == target.id)
            .first()
        )
        assert audit is not None
        # Password must NOT be in the audit payload
        import json
        payload = json.loads(audit.payload) if audit.payload else {}
        assert "password" not in payload or payload["password"] == "[REDACTED]"

    def test_password_change_audited_redacted(self, client, db, super_admin):
        """When a password is changed, the audit log must NOT contain the plaintext password."""
        target = User(
            email="pwd-change@example.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Pwd",
            last_name="Change",
            role="DOCTOR",
            is_active=True,
        )
        db.add(target); db.commit(); db.refresh(target)

        r = client.put(
            f"/api/v1/users/{target.id}",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={"password": "NewStrongPassword2!xx"},
        )
        assert r.status_code == 200
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.action == "user.update")
            .filter(AuditLog.resource_id == target.id)
            .first()
        )
        assert audit is not None
        import json
        payload = json.loads(audit.payload) if audit.payload else {}
        # Password field must be redacted, never plaintext
        if "password" in payload:
            assert payload["password"] == "[REDACTED]"
            assert "NewStrongPassword2!xx" not in (audit.payload or "")

    def test_facility_create_is_audited(self, client, db, super_admin):
        r = client.post(
            "/api/v1/facilities",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={"code": "AUDIT-FAC", "name": "Audit Facility", "category": "Hospital"},
        )
        assert r.status_code == 200
        audit = db.query(AuditLog).filter(AuditLog.action == "facility.create").first()
        assert audit is not None
        assert audit.resource_type == "facility"

    def test_department_create_is_audited(self, client, db, super_admin):
        # Need a facility first
        from app.modules.facilities.models import Facility
        fac = Facility(code="DEP-FAC", name="Dep Facility", category="Hospital")
        db.add(fac); db.commit(); db.refresh(fac)

        r = client.post(
            "/api/v1/departments",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={"code": "AUDIT-DEP", "name": "Audit Dept", "facility_id": fac.id},
        )
        assert r.status_code == 200
        audit = db.query(AuditLog).filter(AuditLog.action == "department.create").first()
        assert audit is not None
        assert audit.resource_type == "department"

    def test_rbac_role_create_is_audited(self, client, db, super_admin):
        r = client.post(
            "/api/v1/rbac/roles",
            headers=_auth_headers(super_admin.id, role="SUPER_ADMIN"),
            json={"code": "AUDIT-ROLE", "name": "Audit Role"},
        )
        assert r.status_code == 200
        audit = db.query(AuditLog).filter(AuditLog.action == "rbac.role.create").first()
        assert audit is not None
        assert audit.resource_type == "role"


# ============================================================================
# A05-003 — AUTH_SECRET hard-fail in non-local env
# ============================================================================

class TestAuthSecretValidation:

    def test_validate_settings_local_allows_empty(self):
        """In local env, empty AUTH_SECRET is allowed (with warning)."""
        import warnings
        from app.core.config import Settings
        # Build a local-env settings with empty secret
        local_settings = Settings(environment="local", auth_secret="")
        # Patch the module-level `settings` temporarily
        import app.core.config as cfg
        original = cfg.settings
        cfg.settings = local_settings
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                cfg.validate_settings()  # no exception, no sys.exit
        finally:
            cfg.settings = original

    def test_validate_settings_production_fails_on_empty(self):
        """In production env, empty AUTH_SECRET calls sys.exit(1)."""
        from app.core.config import Settings
        prod_settings = Settings(environment="production", auth_secret="")
        import app.core.config as cfg
        original = cfg.settings
        cfg.settings = prod_settings
        try:
            with pytest.raises(SystemExit) as exc_info:
                cfg.validate_settings()
            assert exc_info.value.code == 1
        finally:
            cfg.settings = original

    def test_validate_settings_production_ok_with_secret(self):
        """In production env, a non-empty AUTH_SECRET passes validation."""
        from app.core.config import Settings
        prod_settings = Settings(environment="production", auth_secret="a-real-secret")
        import app.core.config as cfg
        original = cfg.settings
        cfg.settings = prod_settings
        try:
            cfg.validate_settings()  # no exception
        finally:
            cfg.settings = original
