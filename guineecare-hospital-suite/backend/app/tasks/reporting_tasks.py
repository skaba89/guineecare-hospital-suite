"""Tâches de reporting — v2.9.2

Tâches planifiées pour la soumission automatique des rapports nationaux :
- push_dhis2_monthly : push automatique du dataset DHIS2 mensuel
- send_quality_alerts_digest : digest quotidien des alertes qualité
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("guineecare.tasks.reporting")


def push_dhis2_monthly(period: str | None = None) -> dict[str, Any]:
    """Push automatique du dataset DHIS2 mensuel.

    Args:
        period: période au format YYYYMM (ex: "202607"). Si None, prend
                le mois précédent (le 5 du mois, on push M-1).

    Returns:
        {"push_status": "success"|"failed"|"dry_run", "period": "...", "total_values": N}
    """
    from app.db.session import SessionLocal
    from app.modules.users.models import User

    if period is None:
        # Le 5 du mois courant, on push le mois précédent
        now = datetime.utcnow()
        first_this_month = now.replace(day=1)
        last_month = first_this_month - timedelta(days=1)
        period = last_month.strftime("%Y%m")

    db = SessionLocal()
    try:
        # Utiliser un SUPER_ADMIN système pour le push automatique
        # (le push DHIS2 requires SUPER_ADMIN or ADMIN with reporting.push)
        system_user = db.query(User).filter(User.role == "SUPER_ADMIN").first()
        if system_user is None:
            logger.error("push_dhis2_monthly: aucun SUPER_ADMIN trouvé pour le push auto")
            return {
                "push_status": "error",
                "period": period,
                "error": "no_super_admin_available",
            }

        from app.modules.reporting.national_service import push_dhis2_dataset
        result = push_dhis2_dataset(db, system_user, period=period)

        logger.info(
            "push_dhis2_monthly: status=%s period=%s values=%s",
            result.get("push_status"), period, result.get("total_values"),
        )
        return {
            "push_status": result.get("push_status", "unknown"),
            "period": period,
            "total_values": result.get("total_values", 0),
            "push_url": result.get("push_url"),
            "push_error": result.get("push_error"),
        }
    except Exception as exc:
        logger.error("push_dhis2_monthly échec: %s", exc)
        return {
            "push_status": "error",
            "period": period,
            "error": str(exc),
        }
    finally:
        db.close()


def send_quality_alerts_digest() -> dict:
    """Digest quotidien des alertes qualité non acquittées.

    Récupère les alertes qualité OPEN/CRITICAL et envoie un digest
    aux administrateurs de l'établissement concerné.

    Returns:
        {"digests_sent": N, "alerts_count": N}
    """
    from app.db.session import SessionLocal
    from app.core.datetime import utcnow
    try:
        from app.modules.quality.dashboard_models import QualityAlert
        from app.modules.notifications.models import Notification
        from app.modules.users.models import User
    except ImportError:
        logger.warning("Quality/notifications modules non disponibles")
        return {"digests_sent": 0, "alerts_count": 0, "error": "module_unavailable"}

    cutoff = utcnow() - timedelta(hours=24)
    db = SessionLocal()
    try:
        # Alertes non acquittées récentes
        alerts = (
            db.query(QualityAlert)
            .filter(QualityAlert.status.in_(["OPEN", "CRITICAL"]))
            .filter(QualityAlert.created_at >= cutoff)
            .all()
        )

        if not alerts:
            logger.info("send_quality_alerts_digest: 0 alerte — skip")
            return {"digests_sent": 0, "alerts_count": 0}

        # Grouper par facility_id
        by_facility: dict[str | None, list] = {}
        for alert in alerts:
            by_facility.setdefault(alert.facility_id, []).append(alert)

        digests_sent = 0
        for facility_id, fac_alerts in by_facility.items():
            # Trouver les ADMIN/SUPER_ADMIN de l'établissement
            admin_query = db.query(User).filter(User.role.in_(["SUPER_ADMIN", "ADMIN"]))
            if facility_id is not None:
                admin_query = admin_query.filter(
                    (User.facility_id == facility_id) | (User.role == "SUPER_ADMIN")
                )
            admins = admin_query.all()

            critical_count = sum(1 for a in fac_alerts if a.severity == "CRITICAL")
            body = (
                f"Digest qualité — {len(fac_alerts)} alerte(s) dont "
                f"{critical_count} critique(s) dans les dernières 24h."
            )

            for admin in admins:
                notif = Notification(
                    user_id=admin.id,
                    facility_id=facility_id,
                    title="Digest qualité quotidien",
                    body=body,
                    type="QUALITY_DIGEST",
                    priority="HIGH" if critical_count else "NORMAL",
                )
                db.add(notif)
                digests_sent += 1

        db.commit()
        logger.info(
            "send_quality_alerts_digest: %d digest(s) envoyé(s) pour %d alerte(s)",
            digests_sent, len(alerts),
        )
        return {"digests_sent": digests_sent, "alerts_count": len(alerts)}
    except Exception as exc:
        logger.error("send_quality_alerts_digest échec: %s", exc)
        db.rollback()
        raise
    finally:
        db.close()


# --- Bind Celery tasks ---
try:
    from app.tasks.celery_app import celery_app

    if celery_app is not None:
        @celery_app.task(name="app.tasks.reporting_tasks.push_dhis2_monthly", bind=True, max_retries=3)
        def _push_dhis2_monthly_task(self, period: str | None = None):
            try:
                return push_dhis2_monthly(period)
            except Exception as exc:
                raise self.retry(exc=exc, countdown=600)

        @celery_app.task(name="app.tasks.reporting_tasks.send_quality_alerts_digest", bind=True, max_retries=2)
        def _send_quality_alerts_digest_task(self):
            try:
                return send_quality_alerts_digest()
            except Exception as exc:
                raise self.retry(exc=exc, countdown=300)
except ImportError:
    pass
