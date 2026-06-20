"""Tests for v0.6.0 features: refresh token rotation + audit log."""
import pytest
from app.core.security import hash_password
from app.modules.auth.models import RefreshToken, AuditLog
from app.modules.users.models import User


@pytest.fixture
def seeded_user(db):
    """Create a user with known credentials for login tests.
    Returns the user ID (not the SQLAlchemy instance) to avoid
    DetachedInstanceError after the test client commits through its own session.
    """
    user = User(
        email="refresh@test.com",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Refresh",
        last_name="Test",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id  # Return the ID, not the detached instance


# ============================================================================
# REFRESH TOKEN — issue, rotate, revoke
# ============================================================================

class TestRefreshTokenFlow:
    """Test the full refresh token lifecycle."""

    def test_login_returns_both_tokens(self, client, seeded_user):
        """POST /auth/login should return access_token + refresh_token."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0
        assert data["user"]["email"] == "refresh@test.com"
        assert data["refresh_token"]  # non-empty

    def test_refresh_returns_new_token_pair(self, client, seeded_user):
        """POST /auth/refresh with a valid refresh token returns a new pair."""
        # Login to get initial tokens
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )
        old_refresh = login_resp.json()["refresh_token"]

        # Refresh
        refresh_resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert refresh_resp.status_code == 200
        new_data = refresh_resp.json()
        assert new_data["access_token"]
        assert new_data["refresh_token"]
        # Refresh token MUST be different (rotation)
        assert new_data["refresh_token"] != old_refresh
        # Access token may be identical if issued within the same second (same exp claim),
        # but the structure is valid JWT (3 dot-separated base64 parts)
        assert new_data["access_token"].count(".") == 2
        assert new_data["user"]["email"] == "refresh@test.com"

    def test_refresh_rotates_old_token_is_invalid(self, client, seeded_user):
        """After refresh, the old refresh token is revoked and cannot be reused."""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )
        old_refresh = login_resp.json()["refresh_token"]

        # First refresh succeeds
        r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert r1.status_code == 200

        # Second refresh with the OLD token must fail
        r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
        assert r2.status_code == 401

    def test_refresh_unknown_token_returns_401(self, client, seeded_user):
        """POST /auth/refresh with an unknown token returns 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "totally-fake-token-not-in-db"},
        )
        assert response.status_code == 401

    def test_refresh_missing_token_returns_400(self, client, seeded_user):
        """POST /auth/refresh without a token returns 400."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": ""},
        )
        assert response.status_code == 400

    def test_logout_revokes_refresh_token(self, client, seeded_user, db):
        """POST /auth/logout revokes the refresh token."""
        # Login → get refresh token
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )
        refresh = login_resp.json()["refresh_token"]
        access = login_resp.json()["access_token"]

        # Logout
        logout_resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert logout_resp.status_code == 200
        assert "réussie" in logout_resp.json()["message"].lower()

        # Refresh with revoked token must fail
        r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
        assert r.status_code == 401

    def test_logout_without_token_still_succeeds(self, client, seeded_user):
        """POST /auth/logout without a refresh_token still returns 200."""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )
        access = login_resp.json()["access_token"]

        logout_resp = client.post(
            "/api/v1/auth/logout",
            json={},
            headers={"Authorization": f"Bearer {access}"},
        )
        assert logout_resp.status_code == 200

    def test_refresh_token_hashed_in_db(self, client, seeded_user, db):
        """The refresh token stored in DB is hashed, not the raw token."""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )
        raw_refresh = login_resp.json()["refresh_token"]

        # DB should contain a hashed version, not the raw token
        tokens = db.query(RefreshToken).all()
        assert len(tokens) == 1
        assert tokens[0].token_hash != raw_refresh
        assert tokens[0].token_hash  # non-empty hash
        assert tokens[0].user_id == seeded_user
        assert tokens[0].revoked_at is None
        assert tokens[0].expires_at is not None


# ============================================================================
# AUDIT LOG — login events recorded
# ============================================================================

class TestAuditLog:
    """Test that auth events are recorded in the audit log."""

    def test_successful_login_is_audited(self, client, seeded_user, db):
        """A successful login creates an audit log entry with action='auth.login'."""
        client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )
        logs = db.query(AuditLog).filter(AuditLog.action == "auth.login").all()
        assert len(logs) == 1
        log = logs[0]
        assert log.user_id == seeded_user
        assert log.resource_type == "user"
        assert log.resource_id == str(seeded_user)
        assert log.status_code == 200
        assert log.http_method == "POST"
        assert "/auth/login" in (log.http_path or "")

    def test_failed_login_is_audited(self, client, seeded_user, db):
        """A failed login creates an audit log entry with action='auth.login_failed'."""
        client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "wrong-password"},
        )
        logs = db.query(AuditLog).filter(AuditLog.action == "auth.login_failed").all()
        assert len(logs) == 1
        log = logs[0]
        assert log.status_code == 401
        assert log.user_id is None  # No user context for failed login

    def test_logout_is_audited(self, client, seeded_user, db):
        """A logout creates an audit log entry with action='auth.logout'."""
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )
        access = login_resp.json()["access_token"]
        refresh = login_resp.json()["refresh_token"]

        client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh},
            headers={"Authorization": f"Bearer {access}"},
        )
        logs = db.query(AuditLog).filter(AuditLog.action == "auth.logout").all()
        assert len(logs) == 1
        assert logs[0].user_id == seeded_user
        assert logs[0].status_code == 200

    def test_audit_logs_endpoint_requires_auth(self, client, seeded_user):
        """GET /audit/logs without a token returns 401."""
        response = client.get("/api/v1/audit/logs")
        assert response.status_code == 401

    def test_audit_logs_endpoint_returns_entries(self, client, seeded_user, auth_headers):
        """GET /audit/logs returns paginated audit entries for SUPER_ADMIN."""
        # Generate some audit log entries by logging in
        client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )

        response = client.get("/api/v1/audit/logs", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert data["total"] >= 1  # at least the login audit
        # Most recent entry first
        assert data["data"][0]["action"] in ("auth.login", "auth.logout", "auth.login_failed")

    def test_audit_logs_filter_by_action(self, client, seeded_user, auth_headers):
        """GET /audit/logs?action=auth.login filters by action."""
        # Generate entries
        client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
        )

        response = client.get(
            "/api/v1/audit/logs",
            params={"action": "auth.login"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        for entry in data["data"]:
            assert entry["action"] == "auth.login"

    def test_audit_logs_pagination(self, client, seeded_user, auth_headers):
        """GET /audit/logs supports page_size pagination."""
        # Generate multiple login events
        for _ in range(5):
            client.post(
                "/api/v1/auth/login",
                json={"email": "refresh@test.com", "password": "TestPassword1!xx"},
            )

        response = client.get(
            "/api/v1/audit/logs",
            params={"page": 1, "page_size": 3},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 3
        assert data["total"] >= 5
        assert data["total_pages"] >= 2
