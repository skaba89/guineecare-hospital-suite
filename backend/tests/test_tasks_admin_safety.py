"""Sécurité des tâches d'administration système."""

import pytest

from app.core.security import create_access_token, hash_password
from app.modules.users.models import User


def _headers_for_role(db, role: str, email: str) -> dict[str, str]:
    user = User(
        email=email,
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Test",
        last_name=role,
        role=role,
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


def test_tasks_admin_routes_are_super_admin_only(client, db):
    admin_headers = _headers_for_role(db, "ADMIN", "facility-admin@tasks.test")

    list_response = client.get("/api/v1/tasks", headers=admin_headers)
    trigger_response = client.post(
        "/api/v1/tasks/trigger/backup_database",
        headers=admin_headers,
        json={},
    )

    assert list_response.status_code == 403
    assert trigger_response.status_code == 403


def test_manual_prune_requires_explicit_retention(client, auth_headers, monkeypatch):
    def should_not_run(*args, **kwargs):  # pragma: no cover - assertion path
        raise AssertionError("submit_task ne doit pas être appelé")

    monkeypatch.setattr("app.tasks.celery_app.submit_task", should_not_run)

    response = client.post(
        "/api/v1/tasks/trigger/prune_audit_logs",
        headers=auth_headers,
        json={},
    )

    assert response.status_code == 422
    assert "retention_days" in response.json()["detail"]


@pytest.mark.parametrize("value", [-1, 0, 1, 29, 3651, True, "abc", None])
def test_manual_prune_rejects_unsafe_retention(
    client,
    auth_headers,
    monkeypatch,
    value,
):
    def should_not_run(*args, **kwargs):  # pragma: no cover - assertion path
        raise AssertionError("submit_task ne doit pas être appelé")

    monkeypatch.setattr("app.tasks.celery_app.submit_task", should_not_run)

    response = client.post(
        "/api/v1/tasks/trigger/prune_audit_logs",
        headers=auth_headers,
        json={"retention_days": value},
    )

    assert response.status_code == 422


def test_manual_prune_forwards_valid_retention(client, auth_headers, monkeypatch):
    captured: dict = {}

    def fake_submit(task_path: str, **kwargs):
        captured["task_path"] = task_path
        captured["kwargs"] = kwargs
        return {"deleted": 0, "retention_days": kwargs["retention_days"]}

    monkeypatch.setattr("app.tasks.celery_app.submit_task", fake_submit)
    monkeypatch.setattr("app.tasks.celery_app.celery_app", None)

    response = client.post(
        "/api/v1/tasks/trigger/prune_audit_logs",
        headers=auth_headers,
        json={"retention_days": 365},
    )

    assert response.status_code == 200
    assert captured["task_path"] == "app.tasks.maintenance_tasks.prune_audit_logs"
    assert captured["kwargs"] == {"retention_days": 365}
    assert response.json()["status"] == "sync_executed"
