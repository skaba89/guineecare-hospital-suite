"""Tests for v1.1.0 user_profile module — preferences, feedback, recent items.

Covers:
- Preferences: defaults, partial update, validation, audit log trail.
- Feedback: submit, list (mine + admin), RBAC (cross-facility), resolve flow.
- Recent items: record, bubble-to-top on revisit, prune at MAX_RECENT_ITEMS,
  clear-all, filter by resource_type.
"""
import pytest

from app.core.security import create_access_token, hash_password
from app.modules.facilities.models import Facility
from app.modules.user_profile.models import (
    MAX_RECENT_ITEMS,
    UserFeedback,
    UserPreference,
    UserRecentItem,
)
from app.modules.users.models import User


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def super_admin(db):
    user = User(
        email="admin@profile.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Admin",
        last_name="Profile",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def doctor(db):
    user = User(
        email="doctor@profile.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Doc",
        last_name="Profile",
        role="DOCTOR",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def facility(db):
    fac = Facility(
        name="CHU Test",
        code="CHU-TEST",
        category="CHU",
        region="Conakry",
    )
    db.add(fac)
    db.commit()
    db.refresh(fac)
    return fac


@pytest.fixture
def admin_donka(db, facility):
    user = User(
        email="admin.donka@profile.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Admin",
        last_name="Donka",
        role="ADMIN",
        facility_id=facility.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_other(db):
    other_fac = Facility(name="CHU Other", code="CHU-OTHER", category="CHU", region="Kankan")
    db.add(other_fac)
    db.commit()
    db.refresh(other_fac)
    user = User(
        email="admin.other@profile.test",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Admin",
        last_name="Other",
        role="ADMIN",
        facility_id=other_fac.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth(user) -> dict:
    # Capture primitives BEFORE issuing any request — after a request the
    # SQLAlchemy session is closed by the client fixture and the User object
    # becomes detached, so accessing user.id later in a test would raise
    # DetachedInstanceError.
    user_id = user.id
    facility_id = user.facility_id
    role = user.role
    token = create_access_token(
        subject=user_id,
        facility_id=facility_id,
        role=role,
    )
    return {"Authorization": f"Bearer {token}"}


def _user_id(user, db) -> str:
    """Safely re-fetch the user id after a request (the original User object
    may be detached). Use this in assertions instead of `user.id`.
    """
    from app.modules.users.models import User as UserModel
    row = db.query(UserModel).filter(UserModel.email == user.email).first()
    assert row is not None
    return row.id


# ============================================================================
# Preferences
# ============================================================================

class TestPreferences:
    def test_get_preferences_returns_defaults_when_none(self, client, doctor, db):
        """GET /me/preferences returns defaults if user has no row yet."""
        doctor_id = _user_id(doctor, db)
        resp = client.get("/api/v1/me/preferences", headers=_auth(doctor))
        assert resp.status_code == 200
        body = resp.json()
        assert body["locale"] == "fr"
        assert body["theme"] == "light"
        assert body["default_page_size"] == 20
        assert body["dashboard_refresh_seconds"] == 30
        assert body["extra"] == {}
        assert body["user_id"] == doctor_id

    def test_get_preferences_creates_row_idempotently(self, client, doctor, db):
        """Two GETs return the same row (idempotent creation)."""
        resp1 = client.get("/api/v1/me/preferences", headers=_auth(doctor))
        assert resp1.status_code == 200
        resp2 = client.get("/api/v1/me/preferences", headers=_auth(doctor))
        assert resp2.status_code == 200
        # Only one row should exist
        rows = db.query(UserPreference).filter(UserPreference.user_id == doctor.id).all()
        assert len(rows) == 1

    def test_update_preferences_partial(self, client, doctor):
        """PUT with only locale updates just that field."""
        resp = client.put(
            "/api/v1/me/preferences",
            json={"locale": "en"},
            headers=_auth(doctor),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["locale"] == "en"
        # Other fields unchanged
        assert body["theme"] == "light"
        assert body["default_page_size"] == 20

    def test_update_preferences_full(self, client, doctor):
        resp = client.put(
            "/api/v1/me/preferences",
            json={
                "locale": "en",
                "theme": "dark",
                "default_page_size": 50,
                "dashboard_refresh_seconds": 60,
                "extra": {"pinned_modules": ["patients", "lab"]},
            },
            headers=_auth(doctor),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["locale"] == "en"
        assert body["theme"] == "dark"
        assert body["default_page_size"] == 50
        assert body["dashboard_refresh_seconds"] == 60
        assert body["extra"] == {"pinned_modules": ["patients", "lab"]}

    def test_update_preferences_invalid_locale(self, client, doctor):
        resp = client.put(
            "/api/v1/me/preferences",
            json={"locale": "es"},  # not fr|en
            headers=_auth(doctor),
        )
        assert resp.status_code == 422

    def test_update_preferences_invalid_theme(self, client, doctor):
        resp = client.put(
            "/api/v1/me/preferences",
            json={"theme": "purple"},
            headers=_auth(doctor),
        )
        assert resp.status_code == 422

    def test_update_preferences_page_size_bounds(self, client, doctor):
        # Too small
        resp = client.put(
            "/api/v1/me/preferences",
            json={"default_page_size": 1},
            headers=_auth(doctor),
        )
        assert resp.status_code == 422
        # Too large
        resp = client.put(
            "/api/v1/me/preferences",
            json={"default_page_size": 500},
            headers=_auth(doctor),
        )
        assert resp.status_code == 422

    def test_update_preferences_refresh_bounds(self, client, doctor):
        # Negative
        resp = client.put(
            "/api/v1/me/preferences",
            json={"dashboard_refresh_seconds": -1},
            headers=_auth(doctor),
        )
        assert resp.status_code == 422
        # Too large (>600)
        resp = client.put(
            "/api/v1/me/preferences",
            json={"dashboard_refresh_seconds": 601},
            headers=_auth(doctor),
        )
        assert resp.status_code == 422

    def test_update_preferences_writes_audit_log(self, client, doctor, db):
        from app.modules.auth.models import AuditLog
        doctor_id = _user_id(doctor, db)
        resp = client.put(
            "/api/v1/me/preferences",
            json={"theme": "dark"},
            headers=_auth(doctor),
        )
        assert resp.status_code == 200
        log = (
            db.query(AuditLog)
            .filter(AuditLog.action == "user.preferences.update")
            .filter(AuditLog.user_id == doctor_id)
            .first()
        )
        assert log is not None
        assert log.resource_type == "user_preferences"
        assert log.status_code == 200

    def test_preferences_require_auth(self, client):
        resp = client.get("/api/v1/me/preferences")
        assert resp.status_code == 401


# ============================================================================
# Feedback
# ============================================================================

class TestFeedback:
    def test_submit_feedback_creates_entry(self, client, doctor, db):
        doctor_id = _user_id(doctor, db)
        resp = client.post(
            "/api/v1/feedback",
            json={
                "category": "bug",
                "priority": "high",
                "subject": "Page patients se charge lentement",
                "message": "Quand je clique sur Patients, ça met 10 secondes.",
                "page_url": "/patients",
            },
            headers=_auth(doctor),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["category"] == "bug"
        assert body["priority"] == "high"
        assert body["status"] == "open"
        assert body["user_id"] == doctor_id
        assert body["message"].startswith("Quand je clique")
        # user_agent captured from request
        assert body["user_agent"] is not None
        # Row exists
        rows = db.query(UserFeedback).filter(UserFeedback.user_id == doctor_id).all()
        assert len(rows) == 1

    def test_submit_feedback_minimal(self, client, doctor):
        """Only category + message are required."""
        resp = client.post(
            "/api/v1/feedback",
            json={"category": "praise", "message": "Très belle interface!"},
            headers=_auth(doctor),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["priority"] == "normal"  # default
        assert body["subject"] is None

    def test_submit_feedback_invalid_category(self, client, doctor):
        resp = client.post(
            "/api/v1/feedback",
            json={"category": "complaint", "message": "..."},
            headers=_auth(doctor),
        )
        assert resp.status_code == 422

    def test_submit_feedback_message_too_long(self, client, doctor):
        resp = client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "x" * 4001},
            headers=_auth(doctor),
        )
        assert resp.status_code == 422

    def test_submit_feedback_writes_audit_log(self, client, doctor, db):
        from app.modules.auth.models import AuditLog
        doctor_id = _user_id(doctor, db)
        client.post(
            "/api/v1/feedback",
            json={"category": "suggestion", "message": "Ajouter un export PDF"},
            headers=_auth(doctor),
        )
        log = (
            db.query(AuditLog)
            .filter(AuditLog.action == "feedback.create")
            .filter(AuditLog.user_id == doctor_id)
            .first()
        )
        assert log is not None
        assert log.resource_type == "user_feedback"

    def test_list_feedback_mine_only(self, client, doctor, super_admin):
        """Non-admin users only see their own feedback."""
        client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Doctor's bug"},
            headers=_auth(doctor),
        )
        client.post(
            "/api/v1/feedback",
            json={"category": "praise", "message": "Admin's praise"},
            headers=_auth(super_admin),
        )
        # doctor lists — should only see their own
        resp = client.get("/api/v1/feedback", headers=_auth(doctor))
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["message"] == "Doctor's bug"

    def test_list_feedback_mine_filter(self, client, doctor, super_admin):
        """mine=true explicitly limits to own feedback."""
        client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Doctor's bug"},
            headers=_auth(doctor),
        )
        client.post(
            "/api/v1/feedback",
            json={"category": "praise", "message": "Admin's praise"},
            headers=_auth(super_admin),
        )
        resp = client.get("/api/v1/feedback?mine=true", headers=_auth(super_admin))
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["message"] == "Admin's praise"

    def test_admin_lists_facility_feedback(self, client, admin_donka, doctor):
        """ADMIN sees all feedback in their facility."""
        # admin_donka submits in their own facility
        client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Donka bug"},
            headers=_auth(admin_donka),
        )
        # doctor (no facility) submits — admin_donka cannot see it
        client.post(
            "/api/v1/feedback",
            json={"category": "praise", "message": "Doctor praise (no facility)"},
            headers=_auth(doctor),
        )
        # admin_donka lists — sees only facility feedback
        resp = client.get("/api/v1/feedback", headers=_auth(admin_donka))
        body = resp.json()
        messages = [d["message"] for d in body["data"]]
        assert "Donka bug" in messages
        assert "Doctor praise (no facility)" not in messages

    def test_super_admin_lists_all_feedback(self, client, super_admin, admin_donka, doctor):
        client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Donka bug"},
            headers=_auth(admin_donka),
        )
        client.post(
            "/api/v1/feedback",
            json={"category": "praise", "message": "Doctor praise"},
            headers=_auth(doctor),
        )
        resp = client.get("/api/v1/feedback", headers=_auth(super_admin))
        body = resp.json()
        assert body["total"] == 2

    def test_list_feedback_filter_by_category(self, client, super_admin):
        client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "bug 1"},
            headers=_auth(super_admin),
        )
        client.post(
            "/api/v1/feedback",
            json={"category": "praise", "message": "praise 1"},
            headers=_auth(super_admin),
        )
        resp = client.get("/api/v1/feedback?category=bug", headers=_auth(super_admin))
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["category"] == "bug"

    def test_resolve_feedback_admin(self, client, admin_donka, doctor):
        # doctor submits feedback
        submit = client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Something broken"},
            headers=_auth(doctor),
        )
        # Wait — doctor has no facility, so admin_donka (different facility) can't resolve.
        # Use admin_donka's own feedback for the resolve test.
        submit = client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Donka bug"},
            headers=_auth(admin_donka),
        )
        feedback_id = submit.json()["id"]
        resp = client.patch(
            f"/api/v1/feedback/{feedback_id}",
            json={"status": "resolved", "admin_response": "Corrigé en v1.1.1."},
            headers=_auth(admin_donka),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "resolved"
        assert body["admin_response"] == "Corrigé en v1.1.1."
        assert body["resolved_at"] is not None
        assert body["resolved_by"] == admin_donka.id

    def test_resolve_feedback_cross_facility_forbidden(self, client, admin_donka, admin_other):
        """ADMIN cannot resolve feedback from another facility."""
        submit = client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Other facility bug"},
            headers=_auth(admin_other),
        )
        feedback_id = submit.json()["id"]
        resp = client.patch(
            f"/api/v1/feedback/{feedback_id}",
            json={"status": "resolved"},
            headers=_auth(admin_donka),
        )
        assert resp.status_code == 403

    def test_resolve_feedback_non_admin_forbidden(self, client, doctor):
        submit = client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Doctor's bug"},
            headers=_auth(doctor),
        )
        feedback_id = submit.json()["id"]
        resp = client.patch(
            f"/api/v1/feedback/{feedback_id}",
            json={"status": "resolved"},
            headers=_auth(doctor),
        )
        assert resp.status_code == 403

    def test_resolve_feedback_not_found(self, client, super_admin):
        resp = client.patch(
            "/api/v1/feedback/nonexistent-id",
            json={"status": "resolved"},
            headers=_auth(super_admin),
        )
        assert resp.status_code == 404

    def test_resolve_feedback_writes_audit_log(self, client, admin_donka, db):
        from app.modules.auth.models import AuditLog
        admin_id = _user_id(admin_donka, db)
        submit = client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "Donka bug"},
            headers=_auth(admin_donka),
        )
        feedback_id = submit.json()["id"]
        client.patch(
            f"/api/v1/feedback/{feedback_id}",
            json={"status": "wontfix"},
            headers=_auth(admin_donka),
        )
        log = (
            db.query(AuditLog)
            .filter(AuditLog.action == "feedback.resolve")
            .filter(AuditLog.user_id == admin_id)
            .first()
        )
        assert log is not None
        assert log.resource_type == "user_feedback"

    def test_feedback_require_auth(self, client):
        resp = client.post(
            "/api/v1/feedback",
            json={"category": "bug", "message": "x"},
        )
        assert resp.status_code == 401


# ============================================================================
# Recent items
# ============================================================================

class TestRecentItems:
    def test_record_recent_item(self, client, doctor, db):
        doctor_id = _user_id(doctor, db)
        resp = client.post(
            "/api/v1/me/recent",
            json={
                "resource_type": "patient",
                "resource_id": "pat-001",
                "resource_label": "Diallo, Jean (1985-03-12)",
            },
            headers=_auth(doctor),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["resource_type"] == "patient"
        assert body["resource_id"] == "pat-001"
        assert body["resource_label"].startswith("Diallo")
        assert body["user_id"] == doctor_id

    def test_record_recent_bubbles_to_top_on_revisit(self, client, doctor, db):
        """Re-recording the same (type, id) updates viewed_at instead of inserting."""
        import time
        doctor_id = _user_id(doctor, db)
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "patient", "resource_id": "pat-001", "resource_label": "First"},
            headers=_auth(doctor),
        )
        time.sleep(0.05)
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "patient", "resource_id": "pat-001", "resource_label": "Second"},
            headers=_auth(doctor),
        )
        # Only one row should exist
        rows = (
            db.query(UserRecentItem)
            .filter(UserRecentItem.user_id == doctor_id)
            .filter(UserRecentItem.resource_id == "pat-001")
            .all()
        )
        assert len(rows) == 1
        assert rows[0].resource_label == "Second"
        # List returns just one
        resp = client.get("/api/v1/me/recent", headers=_auth(doctor))
        body = resp.json()
        assert body["total"] == 1

    def test_list_recent_items_order(self, client, doctor):
        """Most recent first."""
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "patient", "resource_id": "pat-001"},
            headers=_auth(doctor),
        )
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "lab_order", "resource_id": "lab-001"},
            headers=_auth(doctor),
        )
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "patient", "resource_id": "pat-002"},
            headers=_auth(doctor),
        )
        resp = client.get("/api/v1/me/recent", headers=_auth(doctor))
        body = resp.json()
        assert body["total"] == 3
        # Most recent first
        assert body["data"][0]["resource_id"] == "pat-002"
        assert body["data"][1]["resource_id"] == "lab-001"
        assert body["data"][2]["resource_id"] == "pat-001"

    def test_list_recent_filter_by_type(self, client, doctor):
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "patient", "resource_id": "pat-001"},
            headers=_auth(doctor),
        )
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "lab_order", "resource_id": "lab-001"},
            headers=_auth(doctor),
        )
        resp = client.get(
            "/api/v1/me/recent?resource_type=patient",
            headers=_auth(doctor),
        )
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["resource_type"] == "patient"

    def test_list_recent_limit(self, client, doctor):
        for i in range(10):
            client.post(
                "/api/v1/me/recent",
                json={"resource_type": "patient", "resource_id": f"pat-{i:03d}"},
                headers=_auth(doctor),
            )
        resp = client.get("/api/v1/me/recent?limit=5", headers=_auth(doctor))
        body = resp.json()
        assert body["total"] == 5

    def test_recent_items_prune_at_max(self, client, doctor, db):
        """Inserting MAX_RECENT_ITEMS + N rows keeps only MAX_RECENT_ITEMS."""
        doctor_id = _user_id(doctor, db)
        # Insert more than the cap
        n = MAX_RECENT_ITEMS + 10
        for i in range(n):
            client.post(
                "/api/v1/me/recent",
                json={"resource_type": "patient", "resource_id": f"pat-{i:04d}"},
                headers=_auth(doctor),
            )
        rows = (
            db.query(UserRecentItem)
            .filter(UserRecentItem.user_id == doctor_id)
            .all()
        )
        assert len(rows) == MAX_RECENT_ITEMS
        # The oldest ones (pat-0000 ... pat-0009) should have been pruned
        ids = {r.resource_id for r in rows}
        assert "pat-0000" not in ids
        assert f"pat-{n-1:04d}" in ids

    def test_clear_recent_items(self, client, doctor, db):
        doctor_id = _user_id(doctor, db)
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "patient", "resource_id": "pat-001"},
            headers=_auth(doctor),
        )
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "lab_order", "resource_id": "lab-001"},
            headers=_auth(doctor),
        )
        resp = client.delete("/api/v1/me/recent", headers=_auth(doctor))
        assert resp.status_code == 204
        rows = (
            db.query(UserRecentItem)
            .filter(UserRecentItem.user_id == doctor_id)
            .all()
        )
        assert len(rows) == 0

    def test_recent_items_isolated_per_user(self, client, doctor, super_admin, db):
        """User A's recent items are not visible to user B."""
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "patient", "resource_id": "pat-A"},
            headers=_auth(doctor),
        )
        client.post(
            "/api/v1/me/recent",
            json={"resource_type": "patient", "resource_id": "pat-B"},
            headers=_auth(super_admin),
        )
        resp = client.get("/api/v1/me/recent", headers=_auth(doctor))
        body = resp.json()
        assert body["total"] == 1
        assert body["data"][0]["resource_id"] == "pat-A"

    def test_recent_items_invalid_resource_type(self, client, doctor):
        resp = client.post(
            "/api/v1/me/recent",
            json={"resource_type": "unknown_thing", "resource_id": "x"},
            headers=_auth(doctor),
        )
        assert resp.status_code == 422

    def test_recent_items_require_auth(self, client):
        resp = client.get("/api/v1/me/recent")
        assert resp.status_code == 401
