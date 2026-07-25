"""Tâches de maintenance — v2.9.2

Tâches planifiées pour la conformité RGPD et la robustesse opérationnelle :
- prune_audit_logs : purge des audit_logs > N jours (RGPD Art. 25 minimisation)
- backup_database : dump PostgreSQL automatique (rotation M jours)
- retry_sms_pending : retry des SMS en échec (v1.4.0 SMS service)
"""
from __future__ import annotations

import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger("guineecare.tasks.maintenance")

# Rétention audit log (RGPD — minimisation des données)
AUDIT_LOG_RETENTION_DAYS = int(os.environ.get("AUDIT_LOG_RETENTION_DAYS", "365"))
# Rétention backups (rotation locale — le cloud storage a sa propre lifecycle)
BACKUP_RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "30"))
# Répertoire de stockage des backups
BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "/tmp/guineecare-backups"))


def prune_audit_logs(retention_days: int | None = None) -> dict:
    """Supprime les audit_logs âgés de plus de `retention_days` jours.

    RGPD Art. 25 (minimization) + Art. 5 (limitation de conservation) :
    les données d'audit doivent être purgées après la durée nécessaire.

    Args:
        retention_days: durée de rétention en jours (défaut: env ou 365)

    Returns:
        {"deleted": N, "retention_days": N, "cutoff_date": ISO}
    """
    from app.db.session import SessionLocal
    from app.modules.auth.models import AuditLog
    from app.core.datetime import utcnow

    retention = retention_days or AUDIT_LOG_RETENTION_DAYS
    cutoff = utcnow() - timedelta(days=retention)

    db = SessionLocal()
    try:
        # Compter avant suppression
        count_before = db.query(AuditLog).filter(AuditLog.created_at < cutoff).count()

        if count_before == 0:
            logger.info("prune_audit_logs: 0 entrée à purger (cutoff=%s)", cutoff.isoformat())
            return {
                "deleted": 0,
                "retention_days": retention,
                "cutoff_date": cutoff.isoformat(),
            }

        # Suppression par batch de 1000 pour éviter de bloquer la DB
        total_deleted = 0
        batch_size = 1000
        while True:
            rows = (
                db.query(AuditLog)
                .filter(AuditLog.created_at < cutoff)
                .limit(batch_size)
                .all()
            )
            if not rows:
                break
            for row in rows:
                db.delete(row)
            db.commit()
            total_deleted += len(rows)
            if len(rows) < batch_size:
                break

        logger.info(
            "prune_audit_logs: %d entrées purgées (cutoff=%s, retention=%dj)",
            total_deleted, cutoff.isoformat(), retention,
        )

        # Audit de la purge elle-même (méta-audit)
        try:
            from app.modules.audit.service import audit_log
            audit_log(
                db=db,
                action="system.audit_prune",
                resource_type="audit_log",
                resource_id=None,
                status_code=200,
                payload={
                    "deleted": total_deleted,
                    "retention_days": retention,
                    "cutoff_date": cutoff.isoformat(),
                },
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Méta-audit prune échoué: %s", exc)

        return {
            "deleted": total_deleted,
            "retention_days": retention,
            "cutoff_date": cutoff.isoformat(),
        }
    except Exception as exc:
        logger.error("prune_audit_logs échec: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()


def backup_database(output_dir: Path | None = None) -> dict:
    """Dump PostgreSQL via `pg_dump` + rotation des anciens backups.

    En SQLite (dev/test), copie le fichier .db directement.

    Returns:
        {"backup_file": path, "size_bytes": N, "rotation_deleted": N}
    """
    from app.core.config import settings

    out_dir = output_dir or BACKUP_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    db_url = settings.database_url

    # Détection SQLite vs PostgreSQL
    if db_url.startswith("sqlite"):
        # Copie simple du fichier
        db_path = db_url.replace("sqlite:///", "")
        backup_path = out_dir / f"guineecare_{timestamp}.db"
        try:
            import shutil
            shutil.copy2(db_path, backup_path)
            size = backup_path.stat().st_size
            logger.info("Backup SQLite: %s (%d bytes)", backup_path, size)
        except Exception as exc:
            logger.error("Backup SQLite échec: %s", exc)
            raise
    else:
        # PostgreSQL : pg_dump
        backup_path = out_dir / f"guineecare_{timestamp}.sql"
        try:
            # pg_dump lit DATABASE_URL directement via -d
            cmd = ["pg_dump", "--no-password", "-d", db_url, "-f", str(backup_path)]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600, check=False,
            )
            if result.returncode != 0:
                logger.error("pg_dump échec: %s", result.stderr[:500])
                raise RuntimeError(f"pg_dump failed: {result.stderr[:200]}")
            size = backup_path.stat().st_size
            logger.info("Backup PostgreSQL: %s (%d bytes)", backup_path, size)
        except FileNotFoundError:
            logger.error("pg_dump non disponible — installer postgresql-client")
            raise
        except Exception as exc:
            logger.error("Backup PostgreSQL échec: %s", exc)
            raise

    # Rotation : supprimer les backups > BACKUP_RETENTION_DAYS
    rotation_deleted = 0
    cutoff = datetime.utcnow() - timedelta(days=BACKUP_RETENTION_DAYS)
    for old_backup in out_dir.glob("guineecare_*.*"):
        try:
            mtime = datetime.fromtimestamp(old_backup.stat().st_mtime)
            if mtime < cutoff:
                old_backup.unlink()
                rotation_deleted += 1
        except Exception as exc:  # noqa: BLE001
            logger.warning("Rotation: impossible de supprimer %s: %s", old_backup, exc)

    # Audit du backup
    try:
        from app.db.session import SessionLocal
        from app.modules.audit.service import audit_log
        db = SessionLocal()
        try:
            audit_log(
                db=db,
                action="system.backup",
                resource_type="database",
                resource_id=str(backup_path),
                status_code=200,
                payload={
                    "backup_file": str(backup_path),
                    "size_bytes": size,
                    "rotation_deleted": rotation_deleted,
                },
            )
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Méta-audit backup échoué: %s", exc)

    return {
        "backup_file": str(backup_path),
        "size_bytes": size,
        "rotation_deleted": rotation_deleted,
        "retention_days": BACKUP_RETENTION_DAYS,
    }


def retry_sms_pending(max_age_hours: int = 24) -> dict:
    """Retry des SMS en statut PENDING ou FAILED depuis < max_age_hours.

    v1.4.0 — Le service SMS utilise déjà un retry intégré, mais en cas de
    crash worker, certains SMS peuvent rester bloqués en PENDING. Cette
    tâche planifiée les re-déclenche.

    Returns:
        {"retried": N, "still_pending": N}
    """
    from app.db.session import SessionLocal
    from app.core.datetime import utcnow
    try:
        from app.modules.notifications.sms_models import SmsMessage
        from app.modules.notifications.sms_service import send_sms
    except ImportError:
        logger.warning("SMS module non disponible — retry_sms_pending skip")
        return {"retried": 0, "still_pending": 0, "error": "sms_module_unavailable"}

    cutoff = utcnow() - timedelta(hours=max_age_hours)
    db = SessionLocal()
    try:
        pending = (
            db.query(SmsMessage)
            .filter(SmsMessage.status.in_(["PENDING", "FAILED"]))
            .filter(SmsMessage.created_at >= cutoff)
            .limit(100)
            .all()
        )

        retried = 0
        still_pending = 0
        for sms in pending:
            try:
                send_sms(db, sms)
                retried += 1
            except Exception as exc:  # noqa: BLE001
                logger.warning("Retry SMS %s échec: %s", sms.id, exc)
                still_pending += 1

        logger.info(
            "retry_sms_pending: %d retry, %d encore en échec (cutoff=%dh)",
            retried, still_pending, max_age_hours,
        )
        return {"retried": retried, "still_pending": still_pending}
    except Exception as exc:
        logger.error("retry_sms_pending échec: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()


# --- Bind Celery tasks (si Celery est disponible) ---
try:
    from app.tasks.celery_app import celery_app

    if celery_app is not None:
        @celery_app.task(name="app.tasks.maintenance_tasks.prune_audit_logs", bind=True, max_retries=3)
        def _prune_audit_logs_task(self, retention_days: int | None = None):
            try:
                return prune_audit_logs(retention_days)
            except Exception as exc:
                raise self.retry(exc=exc, countdown=300)

        @celery_app.task(name="app.tasks.maintenance_tasks.backup_database", bind=True, max_retries=2)
        def _backup_database_task(self):
            try:
                return backup_database()
            except Exception as exc:
                raise self.retry(exc=exc, countdown=600)

        @celery_app.task(name="app.tasks.maintenance_tasks.retry_sms_pending", bind=True, max_retries=3)
        def _retry_sms_pending_task(self, max_age_hours: int = 24):
            try:
                return retry_sms_pending(max_age_hours)
            except Exception as exc:
                raise self.retry(exc=exc, countdown=120)
except ImportError:
    pass
