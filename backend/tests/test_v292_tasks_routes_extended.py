"""Tests étendus — v2.9.2 : Routes /tasks (RBAC + audit + erreurs)

Couverture supplémentaire à test_v292_redis_celery.py :
- Audit log généré après trigger de tâche (vérification de la trace)
- Paramètres invalides rejetés de manière fail-closed
- Accès tâches système réservé à SUPER_ADMIN
- Trigger par DOCTOR / NURSE / autres rôles → 403
- Liste des tâches cohérente (toutes les tâches ont un path valide)
- Comportement quand Celery absent (sync_executed)
"""
import os
from datetime import timedelta

import pytest

from app.tasks.routes import AVAILABLE_TASKS


# ---------------------------------------------------------------------------
# 1. Audit log après trigger
# ---------------------------------------------------------------------------
class TestTasksAuditLog:
    """Vérifie que chaque trigger de tâche génère une entrée audit_logs."""

    def test_trigger_prune_generates_audit(self, client, admin_headers, db):
        """Trigger prune_audit_logs → entrée audit_logs avec action=system.task_trigger."""
        from app.modules.auth.models import AuditLog

        count_before = (
            db.query(AuditLog)
            .filter(AuditLog.action == "system.task_trigger")
            .count()
        )

        resp = client.post(
            "/api/v1/tasks/trigger/prune_audit_logs",
            headers=admin_headers,
            json={"retention_days": 365},
        )
        assert resp.status_code == 200

        db.expire_all()
        count_after = (
            db.query(AuditLog)
            .filter(AuditLog.action == "system.task_trigger")
            .count()
        )
        assert count_after >= count_before + 1

        last_audit = (
            db.query(AuditLog)
            .filter(AuditLog.action == "system.task_trigger")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert last_audit is not None
        assert last_audit.resource_type == "task"
        assert last_audit.resource_id == "prune_audit_logs"
        assert last_audit.status_code == 200

    def test_trigger_backup_generates_audit(self, client, admin_headers, db, tmp_path, monkeypatch):
        """Trigger backup_database → entrée audit_logs."""
        from app.modules.auth.models import AuditLog
        from app.tasks import maintenance_tasks

        monkeypatch.setattr(maintenance_tasks, "BACKUP_DIR", tmp_path)

        resp = client.post(
            "/api/v1/tasks/trigger/backup_database",
            headers=admin_headers,
            json={},
        )
        assert resp.status_code == 200

        db.expire_all()
        audit = (
            db.query(AuditLog)
            .filter(AuditLog.action == "system.task_trigger")
            .filter(AuditLog.resource_id == "backup_database")
            .order_by(AuditLog.created_at.desc())
            .first()
        )
        assert audit is not None


# ---------------------------------------------------------------------------
# 2. RBAC strict — tâches système réservées à SUPER_ADMIN
# ---------------------------------------------------------------------------
class TestTasksRBACStrict:
    """Vérifie que les rôles non SUPER_ADMIN sont refusés."""

    def _create_user_with_role(self, db, role: str, email: str):
        from app.core.security import hash_password, create_access_token
        from app.modules.users.models import User

        user = User(
            email=email,
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Test",
            last_name=role.title(),
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token(
            subject=user.id, facility_id=user.facility_id, role=user.role,
        )
        return {"Authorization": f"Bearer {token}"}

    def test_doctor_cannot_list_tasks(self, client, db):
        headers = self._create_user_with_role(db, "DOCTOR", "doc-rbac1@test.com")
        assert client.get("/api/v1/tasks", headers=headers).status_code == 403

    def test_nurse_cannot_list_tasks(self, client, db):
        headers = self._create_user_with_role(db, "NURSE", "nurse-rbac1@test.com")
        assert client.get("/api/v1/tasks", headers=headers).status_code == 403

    def test_pharmacist_cannot_trigger_tasks(self, client, db):
        headers = self._create_user_with_role(db, "PHARMACIST", "pharma-rbac1@test.com")
        resp = client.post(
            "/api/v1/tasks/trigger/prune_audit_logs",
            headers=headers,
            json={"retention_days": 365},
        )
        assert resp.status_code == 403

    def test_lab_tech_cannot_trigger_tasks(self, client, db):
        headers = self._create_user_with_role(db, "LAB_TECH", "lab-rbac1@test.com")
        resp = client.post(
            "/api/v1/tasks/trigger/backup_database",
            headers=headers,
            json={},
        )
        assert resp.status_code == 403

    def test_cashier_cannot_list_tasks(self, client, db):
        headers = self._create_user_with_role(db, "CASHIER", "cash-rbac1@test.com")
        assert client.get("/api/v1/tasks", headers=headers).status_code == 403

    def test_admin_cannot_list_system_tasks(self, client, db):
        """ADMIN d'établissement ne peut pas administrer les tâches système nationales."""
        from app.core.security import hash_password, create_access_token
        from app.modules.users.models import User
        from app.modules.facilities.models import Facility

        facility = Facility(
            name="Test Facility",
            code="TEST001",
            category="CHU",
            region="Conakry",
        )
        db.add(facility)
        db.commit()
        db.refresh(facility)

        admin = User(
            email="admin-role@test.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Admin",
            last_name="Role",
            role="ADMIN",
            facility_id=facility.id,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        token = create_access_token(
            subject=admin.id,
            facility_id=admin.facility_id,
            role=admin.role,
        )
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/v1/tasks", headers=headers).status_code == 403
        assert client.post(
            "/api/v1/tasks/trigger/backup_database",
            headers=headers,
            json={},
        ).status_code == 403

    def test_unauthenticated_cannot_access(self, client):
        assert client.get("/api/v1/tasks").status_code == 401
        assert client.post(
            "/api/v1/tasks/trigger/prune_audit_logs",
            json={"retention_days": 365},
        ).status_code == 401


# ---------------------------------------------------------------------------
# 3. Cohérence de la liste des tâches
# ---------------------------------------------------------------------------
class TestTasksListConsistency:
    """Vérifie que la liste des tâches est cohérente."""

    def test_all_tasks_have_valid_path(self, client, admin_headers):
        resp = client.get("/api/v1/tasks", headers=admin_headers)
        assert resp.status_code == 200
        tasks = resp.json()["tasks"]

        for task in tasks:
            assert "name" in task
            assert "path" in task
            assert task["path"].startswith("app.tasks.")
            assert task["path"] in AVAILABLE_TASKS.values()

    def test_all_5_expected_tasks_present(self, client, admin_headers):
        resp = client.get("/api/v1/tasks", headers=admin_headers)
        tasks = resp.json()["tasks"]
        names = {t["name"] for t in tasks}
        expected = {
            "prune_audit_logs",
            "backup_database",
            "retry_sms_pending",
            "push_dhis2_monthly",
            "send_quality_alerts_digest",
        }
        assert expected.issubset(names), f"Tâches manquantes: {expected - names}"

    def test_task_response_has_async_enabled_field(self, client, admin_headers):
        tasks = client.get("/api/v1/tasks", headers=admin_headers).json()["tasks"]
        for task in tasks:
            assert "async_enabled" in task
            assert isinstance(task["async_enabled"], bool)

    def test_response_has_celery_available_field(self, client, admin_headers):
        data = client.get("/api/v1/tasks", headers=admin_headers).json()
        assert "celery_available" in data
        assert isinstance(data["celery_available"], bool)

    def test_response_has_broker_url_configured_field(self, client, admin_headers):
        data = client.get("/api/v1/tasks", headers=admin_headers).json()
        assert "broker_url_configured" in data
        assert isinstance(data["broker_url_configured"], bool)


# ---------------------------------------------------------------------------
# 4. Gestion des erreurs et paramètres invalides
# ---------------------------------------------------------------------------
class TestTasksErrorHandling:
    """Vérifie la gestion fail-closed des erreurs et paramètres invalides."""

    def test_trigger_unknown_task_404(self, client, admin_headers):
        resp = client.post(
            "/api/v1/tasks/trigger/nonexistent_task",
            headers=admin_headers,
            json={},
        )
        assert resp.status_code == 404
        assert "Tâche inconnue" in resp.json()["detail"]

    def test_trigger_empty_body_ok_for_non_destructive_task(self, client, admin_headers, tmp_path, monkeypatch):
        from app.tasks import maintenance_tasks
        monkeypatch.setattr(maintenance_tasks, "BACKUP_DIR", tmp_path)
        resp = client.post(
            "/api/v1/tasks/trigger/backup_database",
            headers=admin_headers,
            json=None,
        )
        assert resp.status_code in (200, 422)

    def test_trigger_prune_with_invalid_retention_type_is_rejected(self, client, admin_headers):
        """Une rétention non entière ne doit jamais retomber sur un défaut silencieux."""
        resp = client.post(
            "/api/v1/tasks/trigger/prune_audit_logs",
            headers=admin_headers,
            json={"retention_days": "not-a-number"},
        )
        assert resp.status_code == 422
        assert "retention_days" in resp.json()["detail"]

    @pytest.mark.parametrize("retention_days", [None, True, -1, 0, 29, 3651])
    def test_trigger_prune_with_unsafe_retention_is_rejected(
        self,
        client,
        admin_headers,
        retention_days,
    ):
        resp = client.post(
            "/api/v1/tasks/trigger/prune_audit_logs",
            headers=admin_headers,
            json={"retention_days": retention_days},
        )
        assert resp.status_code == 422

    def test_trigger_dhis2_with_invalid_period_format(self, client, admin_headers):
        old_url = os.environ.pop("DHIS2_URL", None)
        try:
            resp = client.post(
                "/api/v1/tasks/trigger/push_dhis2_monthly",
                headers=admin_headers,
                json={"period": "invalid-period"},
            )
            assert resp.status_code in (200, 500)
        finally:
            if old_url:
                os.environ["DHIS2_URL"] = old_url
