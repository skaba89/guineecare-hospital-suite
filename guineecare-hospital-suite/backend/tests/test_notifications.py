"""Tests for v0.7.0 notifications module — send, list, mark-read, dismiss, RBAC."""
import pytest
from app.core.security import create_access_token, hash_password
from app.modules.notifications.models import Notification
from app.modules.notifications.service import notify, mark_read, dismiss, mark_all_read
from app.modules.users.models import User


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def admin_user(db):
    user = User(
        email="admin@notif.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Admin",
        last_name="Notif",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


@pytest.fixture
def recipient_user(db):
    user = User(
        email="recipient@notif.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Recip",
        last_name="Notif",
        role="DOCTOR",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


@pytest.fixture
def another_user(db):
    user = User(
        email="other@notif.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Other",
        last_name="User",
        role="NURSE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


def _auth_headers(user_id: str, role: str = "SUPER_ADMIN", facility_id: str | None = None) -> dict:
    token = create_access_token(subject=user_id, facility_id=facility_id, role=role)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Service-level tests
# ============================================================================

class TestNotifyService:
    """Test the notify() service directly."""

    def test_notify_creates_notification_with_in_app_channel(self, db, recipient_user):
        notif = notify(
            db=db,
            recipient_id=recipient_user,
            title="Résultat de laboratoire disponible",
            body="Le résultat de la NFS est disponible pour le patient Jean Diallo.",
            category="lab_result",
            priority="normal",
            action_url="/lab/orders/abc-123",
            resource_type="lab_order",
            resource_id="abc-123",
        )
        assert notif.id
        assert notif.recipient_id == recipient_user
        assert notif.title == "Résultat de laboratoire disponible"
        assert notif.category == "lab_result"
        assert notif.priority == "normal"
        assert notif.in_app_delivered is True
        assert notif.email_delivered is False  # no SMTP configured
        assert notif.sms_delivered is False  # no Twilio configured
        assert notif.read_at is None
        assert notif.dismissed_at is None
        assert "in_app" in (notif.channels or "")

    def test_notify_never_raises_on_unknown_channel(self, db, recipient_user):
        """If a channel provider fails, the notification is still created."""
        notif = notify(
            db=db,
            recipient_id=recipient_user,
            title="Test unknown channel",
            body="body",
            category="system",
            channels=["in_app", "email", "sms"],  # email + sms are not configured
        )
        # in_app always succeeds; email + sms record errors
        assert notif.in_app_delivered is True
        # Delivery error should be populated with both email + sms failures
        assert notif.delivery_error is not None
        assert "email" in notif.delivery_error
        assert "sms" in notif.delivery_error

    def test_notify_deduplicates_channels(self, db, recipient_user):
        """If 'in_app' is passed twice, the channels list should be unique."""
        notif = notify(
            db=db,
            recipient_id=recipient_user,
            title="Dedupe test",
            body="body",
            category="system",
            channels=["in_app", "in_app", "in_app"],
        )
        # Should result in only one "in_app" entry
        channels = [c for c in (notif.channels or "").split(",") if c]
        assert channels == ["in_app"]


# ============================================================================
# Mark-read / dismiss / mark-all-read
# ============================================================================

class TestReadDismissService:

    def test_mark_read_sets_read_at(self, db, recipient_user):
        notif = notify(
            db=db, recipient_id=recipient_user,
            title="read test", body="b", category="system",
        )
        assert notif.read_at is None
        result = mark_read(db, notif.id, recipient_user)
        assert result is not None
        assert result.read_at is not None

    def test_mark_read_only_recipient_can_read(self, db, recipient_user, another_user):
        notif = notify(
            db=db, recipient_id=recipient_user,
            title="read test", body="b", category="system",
        )
        # Another user attempts to mark it read — should return None
        result = mark_read(db, notif.id, another_user)
        assert result is None

    def test_mark_read_unknown_id_returns_none(self, db, recipient_user):
        result = mark_read(db, "nonexistent-id", recipient_user)
        assert result is None

    def test_mark_read_idempotent(self, db, recipient_user):
        notif = notify(
            db=db, recipient_id=recipient_user,
            title="idem", body="b", category="system",
        )
        first = mark_read(db, notif.id, recipient_user)
        first_read_at = first.read_at
        second = mark_read(db, notif.id, recipient_user)
        # read_at should not change on second call (idempotent)
        assert second.read_at == first_read_at

    def test_dismiss_sets_dismissed_at(self, db, recipient_user):
        notif = notify(
            db=db, recipient_id=recipient_user,
            title="dismiss", body="b", category="system",
        )
        result = dismiss(db, notif.id, recipient_user)
        assert result.dismissed_at is not None

    def test_mark_all_read(self, db, recipient_user):
        # Create 3 unread notifications
        for i in range(3):
            notify(
                db=db, recipient_id=recipient_user,
                title=f"n{i}", body="b", category="system",
            )
        count = mark_all_read(db, recipient_user)
        assert count == 3
        # Calling again should return 0 (all already read)
        count2 = mark_all_read(db, recipient_user)
        assert count2 == 0


# ============================================================================
# HTTP API tests
# ============================================================================

class TestNotificationsHTTP:

    def test_list_requires_auth(self, client):
        r = client.get("/api/v1/notifications")
        assert r.status_code == 401

    def test_list_returns_empty_for_new_user(self, client, db):
        user = User(
            email="empty@notif.test",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Empty",
            last_name="List",
            role="DOCTOR",
            is_active=True,
        )
        db.add(user); db.commit(); db.refresh(user)
        r = client.get("/api/v1/notifications", headers=_auth_headers(user.id, role="DOCTOR"))
        assert r.status_code == 200
        data = r.json()
        assert data["data"] == []
        assert data["total"] == 0
        assert data["unread_count"] == 0

    def test_list_returns_user_notifications(self, client, db, recipient_user):
        # Create 2 notifications for the recipient
        notify(db=db, recipient_id=recipient_user, title="n1", body="b1", category="system")
        notify(db=db, recipient_id=recipient_user, title="n2", body="b2", category="lab_result")
        r = client.get("/api/v1/notifications", headers=_auth_headers(recipient_user, role="DOCTOR"))
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert data["unread_count"] == 2
        # Should be ordered by created_at DESC — n2 first
        assert data["data"][0]["title"] == "n2"
        assert data["data"][1]["title"] == "n1"

    def test_list_filters_by_category(self, client, db, recipient_user):
        notify(db=db, recipient_id=recipient_user, title="a", body="b", category="system")
        notify(db=db, recipient_id=recipient_user, title="b", body="b", category="lab_result")
        r = client.get(
            "/api/v1/notifications?category=lab_result",
            headers=_auth_headers(recipient_user, role="DOCTOR"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["data"][0]["category"] == "lab_result"

    def test_list_filters_unread_only(self, client, db, recipient_user):
        n1 = notify(db=db, recipient_id=recipient_user, title="a", body="b", category="system")
        notify(db=db, recipient_id=recipient_user, title="b", body="b", category="system")
        # Mark n1 as read
        mark_read(db, n1.id, recipient_user)
        r = client.get(
            "/api/v1/notifications?unread_only=true",
            headers=_auth_headers(recipient_user, role="DOCTOR"),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["data"][0]["title"] == "b"  # only unread

    def test_unread_count_endpoint(self, client, db, recipient_user):
        notify(db=db, recipient_id=recipient_user, title="a", body="b", category="system")
        notify(db=db, recipient_id=recipient_user, title="b", body="b", category="system")
        r = client.get(
            "/api/v1/notifications/unread-count",
            headers=_auth_headers(recipient_user, role="DOCTOR"),
        )
        assert r.status_code == 200
        assert r.json()["unread_count"] == 2

    def test_mark_read_endpoint(self, client, db, recipient_user):
        notif = notify(db=db, recipient_id=recipient_user, title="r", body="b", category="system")
        r = client.patch(
            f"/api/v1/notifications/{notif.id}/read",
            headers=_auth_headers(recipient_user, role="DOCTOR"),
        )
        assert r.status_code == 200
        assert r.json()["is_read"] is True

    def test_mark_read_forbidden_for_other_user(self, client, db, recipient_user, another_user):
        notif = notify(db=db, recipient_id=recipient_user, title="r", body="b", category="system")
        r = client.patch(
            f"/api/v1/notifications/{notif.id}/read",
            headers=_auth_headers(another_user, role="NURSE"),
        )
        assert r.status_code == 404  # returns 404 (not 403) to avoid info leak

    def test_dismiss_endpoint(self, client, db, recipient_user):
        notif = notify(db=db, recipient_id=recipient_user, title="d", body="b", category="system")
        r = client.delete(
            f"/api/v1/notifications/{notif.id}",
            headers=_auth_headers(recipient_user, role="DOCTOR"),
        )
        assert r.status_code == 200
        assert r.json()["dismissed_at"] is not None
        # Now list should not show it
        r2 = client.get(
            "/api/v1/notifications",
            headers=_auth_headers(recipient_user, role="DOCTOR"),
        )
        assert r2.json()["total"] == 0

    def test_mark_all_read_endpoint(self, client, db, recipient_user):
        for i in range(3):
            notify(db=db, recipient_id=recipient_user, title=f"n{i}", body="b", category="system")
        r = client.post(
            "/api/v1/notifications/mark-all-read",
            headers=_auth_headers(recipient_user, role="DOCTOR"),
        )
        assert r.status_code == 200
        assert r.json()["unread_count"] == 0


# ============================================================================
# Admin send endpoint — RBAC
# ============================================================================

class TestAdminSend:

    def test_admin_can_send(self, client, db, admin_user, recipient_user):
        r = client.post(
            "/api/v1/notifications/send",
            headers=_auth_headers(admin_user, role="SUPER_ADMIN"),
            json={
                "recipient_id": recipient_user,
                "title": "Test admin notification",
                "body": "Sent by admin",
                "category": "system",
                "priority": "high",
                "channels": ["in_app"],
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Test admin notification"
        assert data["recipient_id"] == recipient_user
        assert data["priority"] == "high"
        assert data["in_app_delivered"] is True

    def test_admin_send_unknown_recipient_404(self, client, db, admin_user):
        r = client.post(
            "/api/v1/notifications/send",
            headers=_auth_headers(admin_user, role="SUPER_ADMIN"),
            json={
                "recipient_id": "nonexistent-id",
                "title": "Test",
                "category": "system",
            },
        )
        assert r.status_code == 404

    def test_doctor_cannot_send(self, client, db, recipient_user, another_user):
        """A regular DOCTOR does not have the notification.send permission."""
        r = client.post(
            "/api/v1/notifications/send",
            headers=_auth_headers(recipient_user, role="DOCTOR"),
            json={
                "recipient_id": another_user,
                "title": "Test",
                "category": "system",
            },
        )
        assert r.status_code == 403

    def test_admin_send_audited(self, client, db, admin_user, recipient_user):
        """Admin send creates an audit log entry."""
        from app.modules.auth.models import AuditLog
        r = client.post(
            "/api/v1/notifications/send",
            headers=_auth_headers(admin_user, role="SUPER_ADMIN"),
            json={
                "recipient_id": recipient_user,
                "title": "Audited notification",
                "category": "system",
            },
        )
        assert r.status_code == 201
        # Verify an audit log entry was created
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.action == "notification.send")
            .first()
        )
        assert audit is not None
        assert audit.resource_type == "notification"
        assert audit.resource_id == r.json()["id"]

    def test_admin_send_validation_error(self, client, db, admin_user):
        """Missing required fields should return 422."""
        r = client.post(
            "/api/v1/notifications/send",
            headers=_auth_headers(admin_user, role="SUPER_ADMIN"),
            json={"recipient_id": "x"},  # missing title, category
        )
        assert r.status_code == 422
