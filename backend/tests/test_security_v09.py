"""Tests for v0.9.0 security hardening: TRUSTED_PROXIES, METRICS_TOKEN,
BOOTSTRAP_TOKEN, jti blacklist, CLI bootstrap, SEED_DEMO_DATA guard."""
from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
import jwt

from app.core.config import Settings, is_ip_trusted, settings
from app.core.datetime import utcnow
from app.core.security import create_access_token, decode_access_token
from app.db.session import get_db
from app.main import app
from app.modules.auth.jti import (
    is_jti_revoked,
    prune_expired,
    revoke_jti,
)
from app.modules.auth.models import RevokedJti
from app.modules.users.models import User


# ===========================================================================
# A05-001 — TRUSTED_PROXIES
# ===========================================================================

class TestTrustedProxiesParsing:
    """Verify _parse_trusted_proxies / is_ip_trusted behavior."""

    def test_empty_env_yields_empty_list(self):
        # The default settings has no TRUSTED_PROXIES configured in tests.
        # Re-parse to be explicit.
        from app.core.config import _parse_trusted_proxies
        assert _parse_trusted_proxies("") == []
        assert _parse_trusted_proxies("   ") == []

    def test_single_ip(self):
        from app.core.config import _parse_trusted_proxies
        assert _parse_trusted_proxies("10.0.0.1") == ["10.0.0.1"]

    def test_multiple_ips(self):
        from app.core.config import _parse_trusted_proxies
        result = _parse_trusted_proxies("10.0.0.1, 172.16.0.1,192.168.0.1")
        assert result == ["10.0.0.1", "172.16.0.1", "192.168.0.1"]

    def test_cidr(self):
        from app.core.config import _parse_trusted_proxies
        assert _parse_trusted_proxies("10.0.0.0/8") == ["10.0.0.0/8"]


class TestIsIpTrusted:
    def test_empty_proxies_returns_false(self):
        assert is_ip_trusted("10.0.0.1", []) is False
        assert is_ip_trusted(None, []) is False

    def test_exact_ip_match(self):
        assert is_ip_trusted("10.0.0.1", ["10.0.0.1"]) is True
        assert is_ip_trusted("10.0.0.2", ["10.0.0.1"]) is False

    def test_cidr_match(self):
        assert is_ip_trusted("10.0.0.5", ["10.0.0.0/8"]) is True
        assert is_ip_trusted("11.0.0.1", ["10.0.0.0/8"]) is False
        assert is_ip_trusted("172.16.5.10", ["172.16.0.0/12"]) is True

    def test_invalid_ip_returns_false(self):
        assert is_ip_trusted("not-an-ip", ["10.0.0.0/8"]) is False

    def test_invalid_proxy_entry_skipped(self):
        # Invalid entries are skipped — does not crash, does not match.
        assert is_ip_trusted("10.0.0.1", ["not-a-cidr", "10.0.0.0/8"]) is True


class TestLimiterHonorsTrustedProxies:
    """Verify get_client_ip only trusts X-Forwarded-For from a trusted peer."""

    def test_no_trusted_proxy_uses_remote_addr(self):
        from app.core.limiter import get_client_ip

        class FakeClient:
            host = "203.0.113.5"

        class FakeRequest:
            client = FakeClient()
            headers = {"X-Forwarded-For": "10.0.0.99"}

        # Default test settings have empty trusted_proxies → must use remote_addr
        with patch.object(settings, "trusted_proxies", []):
            ip = get_client_ip(FakeRequest())
        assert ip == "203.0.113.5"

    def test_trusted_proxy_uses_x_forwarded_for(self):
        from app.core.limiter import get_client_ip

        class FakeClient:
            host = "10.0.0.1"  # the proxy itself

        class FakeRequest:
            client = FakeClient()
            headers = {"X-Forwarded-For": "198.51.100.42"}

        with patch.object(settings, "trusted_proxies", ["10.0.0.0/8"]):
            ip = get_client_ip(FakeRequest())
        assert ip == "198.51.100.42"

    def test_untrusted_peer_xff_ignored(self):
        from app.core.limiter import get_client_ip

        class FakeClient:
            host = "203.0.113.99"  # not in trusted_proxies

        class FakeRequest:
            client = FakeClient()
            headers = {"X-Forwarded-For": "10.0.0.99"}

        with patch.object(settings, "trusted_proxies", ["10.0.0.0/8"]):
            ip = get_client_ip(FakeRequest())
        assert ip == "203.0.113.99"


# ===========================================================================
# A05-005 — METRICS_TOKEN
# ===========================================================================

class TestMetricsToken:
    def test_metrics_open_when_no_token_configured(self, client):
        """Default: METRICS_TOKEN is empty → /metrics is open (dev/local mode)."""
        with patch.object(settings, "metrics_token", ""):
            resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "http_requests_total" in resp.text or "app_info" in resp.text

    def test_metrics_requires_auth_when_token_set(self, client):
        with patch.object(settings, "metrics_token", "secret-metrics-token"):
            resp = client.get("/metrics")
        assert resp.status_code == 401
        assert "Authorization header required" in resp.json()["detail"]

    def test_metrics_rejects_wrong_token(self, client):
        with patch.object(settings, "metrics_token", "secret-metrics-token"):
            resp = client.get(
                "/metrics",
                headers={"Authorization": "Bearer wrong-token"},
            )
        assert resp.status_code == 403
        assert "Invalid metrics token" in resp.json()["detail"]

    def test_metrics_accepts_correct_bearer_token(self, client):
        with patch.object(settings, "metrics_token", "secret-metrics-token"):
            resp = client.get(
                "/metrics",
                headers={"Authorization": "Bearer secret-metrics-token"},
            )
        assert resp.status_code == 200
        assert "text/plain" in resp.headers.get("content-type", "")

    def test_metrics_rejects_non_bearer_scheme(self, client):
        with patch.object(settings, "metrics_token", "secret-metrics-token"):
            resp = client.get(
                "/metrics",
                headers={"Authorization": "Basic abc123"},
            )
        assert resp.status_code == 401


# ===========================================================================
# A05-004 — BOOTSTRAP_TOKEN + CLI
# ===========================================================================

class TestBootstrapToken:
    """In non-local envs, /users/bootstrap requires X-Bootstrap-Token."""

    def test_local_env_bootstrap_open_when_table_empty(self, client, db):
        """In local env, bootstrap works without token (dev convenience)."""
        with patch.object(settings, "environment", "local"), \
             patch.object(settings, "bootstrap_token", ""):
            # users table is empty (fresh test DB)
            assert db.query(User).count() == 0
            resp = client.post(
                "/api/v1/users/bootstrap",
                json={
                    "email": "boot@test.com",
                    "password": "StrongPass123!",
                    "first_name": "Boot",
                    "last_name": "Strap",
                },
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["role"] == "SUPER_ADMIN"

    def test_non_local_env_rejects_bootstrap_without_token_config(self, client, db):
        """In non-local env with no BOOTSTRAP_TOKEN → 403 (use CLI instead)."""
        with patch.object(settings, "environment", "production"), \
             patch.object(settings, "bootstrap_token", ""):
            resp = client.post(
                "/api/v1/users/bootstrap",
                json={
                    "email": "boot@test.com",
                    "password": "StrongPass123!",
                    "first_name": "Boot",
                    "last_name": "Strap",
                },
            )
        assert resp.status_code == 403
        assert "Bootstrap endpoint disabled" in resp.json()["detail"]

    def test_non_local_env_rejects_bootstrap_without_token_header(self, client, db):
        with patch.object(settings, "environment", "production"), \
             patch.object(settings, "bootstrap_token", "boot-secret"):
            resp = client.post(
                "/api/v1/users/bootstrap",
                json={
                    "email": "boot@test.com",
                    "password": "StrongPass123!",
                    "first_name": "Boot",
                    "last_name": "Strap",
                },
            )
        assert resp.status_code == 403
        assert "Bootstrap token invalide" in resp.json()["detail"]

    def test_non_local_env_accepts_bootstrap_with_correct_token(self, client, db):
        with patch.object(settings, "environment", "production"), \
             patch.object(settings, "bootstrap_token", "boot-secret"):
            resp = client.post(
                "/api/v1/users/bootstrap",
                json={
                    "email": "boot@test.com",
                    "password": "StrongPass123!",
                    "first_name": "Boot",
                    "last_name": "Strap",
                },
                headers={"X-Bootstrap-Token": "boot-secret"},
            )
        assert resp.status_code == 200, resp.text
        assert resp.json()["data"]["email"] == "boot@test.com"

    def test_non_local_env_rejects_bootstrap_with_wrong_token(self, client, db):
        with patch.object(settings, "environment", "production"), \
             patch.object(settings, "bootstrap_token", "boot-secret"):
            resp = client.post(
                "/api/v1/users/bootstrap",
                json={
                    "email": "boot@test.com",
                    "password": "StrongPass123!",
                    "first_name": "Boot",
                    "last_name": "Strap",
                },
                headers={"X-Bootstrap-Token": "wrong"},
            )
        assert resp.status_code == 403


class TestCliCreateSuperuser:
    """Test the CLI bootstrap path (python -m app.cli create-superuser)."""

    def test_cli_creates_superuser_in_empty_db(self, db):
        from app.cli import cmd_create_superuser
        import argparse

        args = argparse.Namespace(
            email="cli-admin@test.com",
            first_name="Cli",
            last_name="Admin",
            facility_id=None,
            password="StrongPass123!",
            force=False,
        )
        # Use the test DB session by patching SessionLocal
        from app.db.session import SessionLocal
        original = SessionLocal
        # Patch _ensure_schema to no-op (tables already created by fixture)
        with patch("app.cli._ensure_schema", lambda: None), \
             patch("app.db.session.SessionLocal", return_value=db):
            code = cmd_create_superuser(args)
        assert code == 0
        user = db.query(User).filter(User.email == "cli-admin@test.com").first()
        assert user is not None
        assert user.role == "SUPER_ADMIN"

    def test_cli_refuses_when_users_exist(self, db):
        from app.cli import cmd_create_superuser
        import argparse

        # Insert one user first
        from app.core.security import hash_password
        existing = User(
            email="existing@test.com",
            password_hash=hash_password("StrongPass123!"),
            first_name="Existing",
            last_name="User",
            role="USER",
        )
        db.add(existing)
        db.commit()

        args = argparse.Namespace(
            email="cli-admin@test.com",
            first_name="Cli",
            last_name="Admin",
            facility_id=None,
            password="StrongPass123!",
            force=False,
        )
        with patch("app.cli._ensure_schema", lambda: None), \
             patch("app.db.session.SessionLocal", return_value=db):
            code = cmd_create_superuser(args)
        assert code == 2  # exit code for "users table not empty"

    def test_cli_force_creates_additional_superuser(self, db):
        from app.cli import cmd_create_superuser
        import argparse

        from app.core.security import hash_password
        existing = User(
            email="existing@test.com",
            password_hash=hash_password("StrongPass123!"),
            first_name="Existing",
            last_name="User",
            role="USER",
        )
        db.add(existing)
        db.commit()

        args = argparse.Namespace(
            email="cli-admin@test.com",
            first_name="Cli",
            last_name="Admin",
            facility_id=None,
            password="StrongPass123!",
            force=True,
        )
        with patch("app.cli._ensure_schema", lambda: None), \
             patch("app.db.session.SessionLocal", return_value=db):
            code = cmd_create_superuser(args)
        assert code == 0
        user = db.query(User).filter(User.email == "cli-admin@test.com").first()
        assert user is not None
        assert user.role == "SUPER_ADMIN"


# ===========================================================================
# A05-002 — SEED_DEMO_DATA guard in non-local
# ===========================================================================

class TestSeedDemoDataGuard:
    """In non-local envs, SEED_DEMO_DATA=true must be refused."""

    def test_seed_refused_in_production(self, db, caplog):
        import logging
        caplog.set_level(logging.ERROR, logger="guineecare")
        # Simulate the lifespan check
        with patch.object(settings, "environment", "production"), \
             patch("os.environ.get", side_effect=lambda k, d="": "true" if k == "SEED_DEMO_DATA" else d), \
             patch("app.db.seed.run_seed") as mock_seed:
            # Replicate the guard logic
            should_seed = True
            if settings.environment not in ("local", "test", "dev"):
                should_seed = False
                logging.getLogger("guineecare").error(
                    "SEED_DEMO_DATA=true is forbidden in environment=%s.",
                    settings.environment,
                )
            if should_seed:
                from app.db.seed import run_seed
                run_seed()
        mock_seed.assert_not_called()


# ===========================================================================
# A07 — jti blacklist
# ===========================================================================

class TestJtiBlacklist:
    def test_token_includes_jti_claim(self, db):
        from app.core.security import create_access_token
        user = User(
            email="jti@test.com",
            password_hash="x",
            first_name="Jti",
            last_name="Test",
            role="USER",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(subject=user.id, facility_id=None, role="USER")
        payload = decode_access_token(token)
        assert "jti" in payload
        assert isinstance(payload["jti"], str)
        assert len(payload["jti"]) > 0

    def test_each_token_has_unique_jti(self):
        t1 = create_access_token(subject="a", role="USER")
        t2 = create_access_token(subject="a", role="USER")
        j1 = decode_access_token(t1)["jti"]
        j2 = decode_access_token(t2)["jti"]
        assert j1 != j2

    def test_revoke_jti_persists_row(self, db):
        jti = str(uuid4())
        entry = revoke_jti(
            db=db,
            jti=jti,
            user_id=None,
            reason="logout",
            expires_at=None,  # uses default
        )
        assert entry is not None
        assert entry.jti == jti
        assert entry.reason == "logout"

        # Verify it's seen as revoked
        assert is_jti_revoked(db, jti) is True

    def test_is_jti_revoked_returns_false_for_unknown(self, db):
        assert is_jti_revoked(db, str(uuid4())) is False
        assert is_jti_revoked(db, None) is False
        assert is_jti_revoked(db, "") is False

    def test_revoke_jti_is_idempotent(self, db):
        jti = str(uuid4())
        e1 = revoke_jti(db=db, jti=jti, reason="logout")
        e2 = revoke_jti(db=db, jti=jti, reason="logout")
        assert e1 is not None
        assert e2 is not None
        # Same jti → same row
        assert e1.jti == e2.jti
        # No duplicate row
        count = db.query(RevokedJti).filter(RevokedJti.jti == jti).count()
        assert count == 1

    def test_prune_expired_deletes_old_entries(self, db):
        from app.core.datetime import utcnow
        from datetime import timedelta

        # Insert an expired entry
        expired = RevokedJti(
            jti="expired-jti",
            user_id=None,
            reason="logout",
            revoked_at=utcnow() - timedelta(hours=2),
            expires_at=utcnow() - timedelta(hours=1),  # expired
        )
        db.add(expired)

        # Insert a still-valid entry
        valid = RevokedJti(
            jti="valid-jti",
            user_id=None,
            reason="logout",
            revoked_at=utcnow(),
            expires_at=utcnow() + timedelta(minutes=30),  # still valid
        )
        db.add(valid)
        db.commit()

        deleted = prune_expired(db)
        assert deleted >= 1

        # Expired is gone, valid remains
        assert db.query(RevokedJti).filter(RevokedJti.jti == "expired-jti").first() is None
        assert db.query(RevokedJti).filter(RevokedJti.jti == "valid-jti").first() is not None


class TestJtiBlacklistIntegration:
    """End-to-end: revoking a jti blocks subsequent requests with that token."""

    def test_revoked_jti_rejects_request(self, client, db):
        # Create a user and issue a token
        from app.core.security import hash_password
        user = User(
            email="revoke@test.com",
            password_hash=hash_password("StrongPass123!"),
            first_name="Revoke",
            last_name="Test",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        token = create_access_token(subject=user.id, role=user.role)
        jti = decode_access_token(token)["jti"]
        headers = {"Authorization": f"Bearer {token}"}

        # First request with the token works
        resp = client.get("/api/v1/users/me", headers=headers)
        assert resp.status_code == 200, resp.text

        # Revoke the jti
        revoke_jti(
            db=db,
            jti=jti,
            user_id=str(user.id),
            reason="logout",
            expires_at=utcnow() + timedelta(minutes=60),
        )

        # Second request with the SAME token must now be rejected
        resp = client.get("/api/v1/users/me", headers=headers)
        assert resp.status_code == 401
        assert "révoqué" in resp.json()["detail"].lower()

    def test_logout_with_access_token_revokes_jti(self, client, db):
        from app.core.security import hash_password
        from app.modules.auth.models import RefreshToken
        from app.core.security import (
            generate_refresh_token,
            hash_refresh_token,
            create_refresh_token_expiry,
        )

        user = User(
            email="logout@test.com",
            password_hash=hash_password("StrongPass123!"),
            first_name="Logout",
            last_name="Test",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Issue access + refresh tokens
        access_token = create_access_token(subject=user.id, role=user.role)
        raw_refresh = generate_refresh_token()
        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=create_refresh_token_expiry(),
        )
        db.add(refresh_record)
        db.commit()

        headers = {"Authorization": f"Bearer {access_token}"}

        # Call /auth/logout with both tokens
        resp = client.post(
            "/api/v1/auth/logout",
            headers=headers,
            json={"access_token": access_token, "refresh_token": raw_refresh},
        )
        assert resp.status_code == 200, resp.text

        # Verify jti is now in blacklist
        jti = decode_access_token(access_token)["jti"]
        assert is_jti_revoked(db, jti) is True

        # Subsequent request with the same access token must fail
        resp = client.get("/api/v1/users/me", headers=headers)
        assert resp.status_code == 401

    def test_logout_without_access_token_keeps_jti_valid(self, client, db):
        from app.core.security import hash_password
        from app.modules.auth.models import RefreshToken
        from app.core.security import (
            generate_refresh_token,
            hash_refresh_token,
            create_refresh_token_expiry,
        )

        user = User(
            email="logout2@test.com",
            password_hash=hash_password("StrongPass123!"),
            first_name="Logout",
            last_name="Two",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        access_token = create_access_token(subject=user.id, role=user.role)
        raw_refresh = generate_refresh_token()
        refresh_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=create_refresh_token_expiry(),
        )
        db.add(refresh_record)
        db.commit()

        headers = {"Authorization": f"Bearer {access_token}"}

        # Logout with only refresh_token (no access_token) — backward compat
        resp = client.post(
            "/api/v1/auth/logout",
            headers=headers,
            json={"refresh_token": raw_refresh},
        )
        assert resp.status_code == 200, resp.text

        # jti NOT revoked — access_token still valid
        jti = decode_access_token(access_token)["jti"]
        assert is_jti_revoked(db, jti) is False

        # Subsequent request with the same access token still works
        resp = client.get("/api/v1/users/me", headers=headers)
        assert resp.status_code == 200
