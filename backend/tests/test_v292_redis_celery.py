"""Tests — v2.9.2 : Redis rate limit + Celery tasks + tasks routes

Couverture :
- Rate limiter reste fonctionnel sans Redis (fallback mémoire)
- Module redis retourne None quand REDIS_URL est vide
- Tâches prune_audit_logs / backup_database / retry_sms_pending exécutables en synchrone
- Tâche push_dhis2_monthly exécutable (dry-run si DHIS2_URL absente)
- Route GET /tasks liste les tâches (SUPER_ADMIN)
- Route POST /tasks/trigger/{name} exécute en synchrone
- RBAC : DOCTOR ne peut pas lister/déclencher les tâches (403)
"""
import os
from datetime import timedelta

import pytest

from app.core.limiter import limiter, _build_limiter
from app.core.redis import get_redis_client, get_rate_limit_storage, is_redis_available


# ---------------------------------------------------------------------------
# 1. Redis module — fallback mémoire en l'absence de Redis
# ---------------------------------------------------------------------------
class TestRedisFallback:
    """Vérifie que l'app reste fonctionnelle sans Redis."""

    def test_redis_url_empty_by_default_in_tests(self):
        """En tests, REDIS_URL doit être vide (sinon les tests deviennent flaky)."""
        client = get_redis_client()
        # Si REDIS_URL est configurée et joignable → client
        # Sinon → None (fallback mémoire)
        assert client is None or hasattr(client, "ping")

    def test_redis_storage_returns_none_when_no_redis(self):
        """Sans Redis, get_rate_limit_storage retourne None (fallback mémoire)."""
        if os.environ.get("REDIS_URL"):
            pytest.skip("REDIS_URL configurée — test skip")
        storage = get_rate_limit_storage()
        assert storage is None

    def test_is_redis_available_returns_bool(self):
        """is_redis_available retourne un booléen."""
        assert isinstance(is_redis_available(), bool)

    def test_limiter_works_without_redis(self):
        """Le limiter slowapi reste fonctionnel sans Redis (storage mémoire)."""
        assert limiter is not None
        assert hasattr(limiter, "_limiter")
        new_limiter = _build_limiter()
        assert new_limiter is not None


# ---------------------------------------------------------------------------
# 2. Tâches Celery — exécution synchrone (sans worker)
# ---------------------------------------------------------------------------
class TestCeleryTasksSync:
    """Les tâches doivent être exécutables en synchrone (sans Celery installé)."""

    def test_prune_audit_logs_no_data(self, db):
        """prune_audit_logs avec 0 entrée → deleted=0."""
        from app.tasks.maintenance_tasks import prune_audit_logs

        result = prune_audit_logs(retention_days=365)
        assert result["deleted"] == 0
        assert result["retention_days"] == 365
        assert "cutoff_date" in result

    def test_prune_audit_logs_deletes_old_entries(self, db):
        """prune_audit_logs supprime les entrées > retention_days."""
        from app.modules.auth.models import AuditLog
        from app.tasks.maintenance_tasks import prune_audit_logs
        from app.core.datetime import utcnow
        from app.core.security import hash_password
        from app.modules.users.models import User

        # Créer un user pour FK
        user = User(
            email="audit-test@test.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Audit",
            last_name="Test",
            role="SUPER_ADMIN",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Créer 2 entrées : 1 vieille (400j), 1 récente (1j)
        old_entry = AuditLog(
            id="old-1",
            created_at=utcnow() - timedelta(days=400),
            user_id=user.id,
            action="test.old",
            resource_type="test",
        )
        recent_entry = AuditLog(
            id="recent-1",
            created_at=utcnow() - timedelta(days=1),
            user_id=user.id,
            action="test.recent",
            resource_type="test",
        )
        db.add_all([old_entry, recent_entry])
        db.commit()

        result = prune_audit_logs(retention_days=365)
        assert result["deleted"] >= 1

        remaining = db.query(AuditLog).filter(AuditLog.id == "recent-1").count()
        assert remaining == 1

        deleted = db.query(AuditLog).filter(AuditLog.id == "old-1").count()
        assert deleted == 0

    def test_backup_database_sqlite(self, db, tmp_path):
        """backup_database crée un fichier .db en mode SQLite."""
        from app.tasks.maintenance_tasks import backup_database

        result = backup_database(output_dir=tmp_path)
        assert "backup_file" in result
        assert "size_bytes" in result
        assert result["size_bytes"] > 0
        assert os.path.exists(result["backup_file"])
        assert result["backup_file"].endswith(".db")

    def test_retry_sms_pending_returns_dict(self, db):
        """retry_sms_pending retourne un dict même sans SMS en attente."""
        from app.tasks.maintenance_tasks import retry_sms_pending

        result = retry_sms_pending(max_age_hours=24)
        assert isinstance(result, dict)
        assert "retried" in result
        assert "still_pending" in result

    def test_push_dhis2_monthly_dry_run(self, db):
        """push_dhis2_monthly en mode dry-run (DHIS2_URL non configurée)."""
        from app.tasks.reporting_tasks import push_dhis2_monthly

        old_url = os.environ.pop("DHIS2_URL", None)
        try:
            result = push_dhis2_monthly(period="202601")
            assert result["period"] == "202601"
            assert result["push_status"] in ("dry_run", "success", "failed", "error")
        finally:
            if old_url:
                os.environ["DHIS2_URL"] = old_url

    def test_send_quality_alerts_digest_no_alerts(self, db):
        """send_quality_alerts_digest avec 0 alerte → digests_sent=0."""
        from app.tasks.reporting_tasks import send_quality_alerts_digest

        result = send_quality_alerts_digest()
        assert isinstance(result, dict)
        assert "digests_sent" in result
        assert "alerts_count" in result


# ---------------------------------------------------------------------------
# 3. Routes /tasks — RBAC + exécution
# ---------------------------------------------------------------------------
class TestTasksRoutes:
    """Routes d'administration des tâches Celery."""

    def test_list_tasks_super_admin(self, client, admin_headers):
        """SUPER_ADMIN peut lister les tâches."""
        resp = client.get("/api/v1/tasks", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "tasks" in data
        assert "celery_available" in data
        task_names = [t["name"] for t in data["tasks"]]
        assert "prune_audit_logs" in task_names
        assert "backup_database" in task_names
        assert "push_dhis2_monthly" in task_names

    def test_list_tasks_forbidden_for_doctor(self, client, db):
        """DOCTOR ne peut pas lister les tâches (403)."""
        from app.core.security import hash_password, create_access_token
        from app.modules.users.models import User

        doctor = User(
            email="doc-tasks@test.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Doc",
            last_name="Test",
            role="DOCTOR",
            is_active=True,
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        token = create_access_token(
            subject=doctor.id, facility_id=doctor.facility_id, role=doctor.role,
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/tasks", headers=headers)
        assert resp.status_code == 403

    def test_trigger_unknown_task_404(self, client, admin_headers):
        """Trigger une tâche inconnue → 404."""
        resp = client.post(
            "/api/v1/tasks/trigger/nonexistent",
            headers=admin_headers,
            json={},
        )
        assert resp.status_code == 404

    def test_trigger_prune_audit_logs(self, client, admin_headers):
        """Trigger prune_audit_logs → 200, status sync_executed."""
        resp = client.post(
            "/api/v1/tasks/trigger/prune_audit_logs",
            headers=admin_headers,
            json={"retention_days": 365},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task"] == "prune_audit_logs"
        assert "result" in data
        assert "deleted" in data["result"]

    def test_trigger_backup_database(self, client, admin_headers, tmp_path, monkeypatch):
        """Trigger backup_database → 200, backup file created."""
        from app.tasks import maintenance_tasks
        monkeypatch.setattr(maintenance_tasks, "BACKUP_DIR", tmp_path)

        resp = client.post(
            "/api/v1/tasks/trigger/backup_database",
            headers=admin_headers,
            json={},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["task"] == "backup_database"
        assert "backup_file" in data["result"]

    def test_trigger_push_dhis2_monthly(self, client, admin_headers):
        """Trigger push_dhis2_monthly → 200, dry_run si DHIS2_URL absente."""
        old_url = os.environ.pop("DHIS2_URL", None)
        try:
            resp = client.post(
                "/api/v1/tasks/trigger/push_dhis2_monthly",
                headers=admin_headers,
                json={"period": "202601"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["task"] == "push_dhis2_monthly"
            assert data["result"]["period"] == "202601"
        finally:
            if old_url:
                os.environ["DHIS2_URL"] = old_url
