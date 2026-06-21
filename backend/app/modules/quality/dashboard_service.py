"""Service Dashboard Qualité v1.4.0 — agrégation, calcul d'indicateurs, alertes automatiques.

Responsabilités :
- `compute_dashboard()` : agrège les mesures par facility / période / catégorie.
- `check_thresholds()` : évalue toutes les mesures récentes contre les seuils actifs,
  lève des `QualityAlert` si franchissement (avec cooldown pour éviter le spam).
- `seed_default_indicators()` : initialise les indicateurs OMS/HAS prédéfinis.
- `seed_default_thresholds()` : initialise les seuils par défaut pour les indicateurs OMS.

Catalogue d'indicateurs prédéfinis (basé sur les recommandations OMS / HAS) :
- INOSO_RATE : taux d'infections nosocomiales (cible OMS : < 5%)
- READMIT_30D : taux de réadmissions à 30 jours (cible HAS : < 10%)
- SAT_PATIENT : satisfaction patient (cible : > 80%)
- ED_WAIT_4H : délai moyen de prise en charge aux urgences (cible : < 4h)
- MORTALITY_24H : mortalité 24h post-admission (cible : < 2%)
- MED_ERROR_RATE : taux d'erreurs médicamenteuses (cible : < 1%)
- SURG_SITE_INFECTION : infections du site opératoire (cible : < 3%)
- BED_OCCUPANCY : taux d'occupation des lits (cible : 75-85%)
"""
import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.datetime import utcnow
from app.modules.quality.dashboard_models import (
    COMPARATORS,
    QualityAlert,
    QualityThreshold,
    evaluate_threshold,
)
from app.modules.quality.models import (
    IncidentReport,
    QualityIndicator,
    QualityMeasurement,
)

logger = logging.getLogger("guineecare.quality.dashboard")


# ---------------------------------------------------------------------------
# Catalogue d'indicateurs prédéfinis (OMS / HAS)
# ---------------------------------------------------------------------------

DEFAULT_INDICATORS = [
    {
        "code": "INOSO_RATE",
        "name": "Taux d'infections nosocomiales",
        "category": "SAFETY",
        "description": "Pourcentage de patients ayant contracté une infection pendant l'hospitalisation. Indicateur OMS de sécurité des soins.",
        "unit": "%",
        "target_value": "5",  # < 5% selon OMS
        "frequency": "MONTHLY",
    },
    {
        "code": "READMIT_30D",
        "name": "Taux de réadmissions à 30 jours",
        "category": "CLINICAL_OUTCOME",
        "description": "Pourcentage de patients réadmis dans les 30 jours après leur sortie. Indicateur HAS de qualité des soins.",
        "unit": "%",
        "target_value": "10",  # < 10%
        "frequency": "MONTHLY",
    },
    {
        "code": "SAT_PATIENT",
        "name": "Satisfaction patient",
        "category": "PATIENT_EXPERIENCE",
        "description": "Score moyen de satisfaction des patients (enquête post-séjour). Cible HAS : > 80%.",
        "unit": "%",
        "target_value": "80",  # > 80%
        "frequency": "QUARTERLY",
    },
    {
        "code": "ED_WAIT_4H",
        "name": "Délai moyen de prise en charge aux urgences",
        "category": "EFFICIENCY",
        "description": "Temps moyen entre l'admission aux urgences et la première consultation médicale. Cible : < 4 heures.",
        "unit": "heures",
        "target_value": "4",  # < 4h
        "frequency": "WEEKLY",
    },
    {
        "code": "MORTALITY_24H",
        "name": "Mortalité 24h post-admission",
        "category": "CLINICAL_OUTCOME",
        "description": "Taux de décès dans les 24 heures suivant l'admission. Indicateur sensible de la qualité de la prise en charge initiale.",
        "unit": "%",
        "target_value": "2",  # < 2%
        "frequency": "MONTHLY",
    },
    {
        "code": "MED_ERROR_RATE",
        "name": "Taux d'erreurs médicamenteuses",
        "category": "SAFETY",
        "description": "Nombre d'erreurs médicamenteuses pour 1000 prescriptions. Cible : < 1 pour 1000.",
        "unit": "pour_1000",
        "target_value": "1",  # < 1/1000
        "frequency": "MONTHLY",
    },
    {
        "code": "SURG_SITE_INFECTION",
        "name": "Infections du site opératoire",
        "category": "SAFETY",
        "description": "Pourcentage d'infections du site opératoire dans les 30 jours post-chirurgie. Cible OMS : < 3%.",
        "unit": "%",
        "target_value": "3",  # < 3%
        "frequency": "MONTHLY",
    },
    {
        "code": "BED_OCCUPANCY",
        "name": "Taux d'occupation des lits",
        "category": "EFFICIENCY",
        "description": "Pourcentage de lits occupés. Zone optimale : 75-85%. En dehors : alerte (sous-utilisation ou surcharge).",
        "unit": "%",
        "target_value": "85",  # <= 85%
        "frequency": "DAILY",
    },
    {
        "code": "FALL_RATE",
        "name": "Taux de chutes de patients",
        "category": "SAFETY",
        "description": "Nombre de chutes pour 1000 journées d'hospitalisation. Cible HAS : < 3 pour 1000.",
        "unit": "pour_1000",
        "target_value": "3",  # < 3/1000
        "frequency": "MONTHLY",
    },
    {
        "code": "VAGINAL_DELIVERY_RATE",
        "name": "Taux d'accouchements par voie basse",
        "category": "CLINICAL_OUTCOME",
        "description": "Pourcentage d'accouchements par voie basse vs césarienne. Cible OMS : > 80%.",
        "unit": "%",
        "target_value": "80",  # > 80%
        "frequency": "QUARTERLY",
    },
]


# ---------------------------------------------------------------------------
# Seuils par défaut (liés aux indicateurs prédéfinis)
# ---------------------------------------------------------------------------

DEFAULT_THRESHOLDS = [
    {
        "indicator_code": "INOSO_RATE",
        "comparator": "GT",
        "threshold_value": "5",
        "severity": "CRITICAL",
        "alert_message": "Taux d'infections nosocomiales critique : {{value}}% (seuil OMS : {{threshold}}%)",
        "notify_roles": "ADMIN,DOCTOR",
        "channels": "in_app,sms,email",
        "cooldown_hours": "24",
    },
    {
        "indicator_code": "READMIT_30D",
        "comparator": "GT",
        "threshold_value": "10",
        "severity": "HIGH",
        "alert_message": "Taux de réadmission 30j élevé : {{value}}% (seuil HAS : {{threshold}}%)",
        "notify_roles": "ADMIN",
        "channels": "in_app,sms",
        "cooldown_hours": "168",  # 1 semaine
    },
    {
        "indicator_code": "SAT_PATIENT",
        "comparator": "LT",
        "threshold_value": "80",
        "severity": "HIGH",
        "alert_message": "Satisfaction patient faible : {{value}}% (cible : > {{threshold}}%)",
        "notify_roles": "ADMIN",
        "channels": "in_app",
        "cooldown_hours": "168",
    },
    {
        "indicator_code": "ED_WAIT_4H",
        "comparator": "GT",
        "threshold_value": "4",
        "severity": "MEDIUM",
        "alert_message": "Délai d'attente aux urgences dépassé : {{value}}h (seuil : {{threshold}}h)",
        "notify_roles": "ADMIN,DOCTOR",
        "channels": "in_app",
        "cooldown_hours": "12",
    },
    {
        "indicator_code": "MORTALITY_24H",
        "comparator": "GT",
        "threshold_value": "2",
        "severity": "CRITICAL",
        "alert_message": "Mortalité 24h post-admission élevée : {{value}}% (seuil : {{threshold}}%)",
        "notify_roles": "ADMIN",
        "channels": "in_app,sms,email",
        "cooldown_hours": "24",
    },
    {
        "indicator_code": "MED_ERROR_RATE",
        "comparator": "GT",
        "threshold_value": "1",
        "severity": "HIGH",
        "alert_message": "Taux d'erreurs médicamenteuses élevé : {{value}}/1000 (seuil : {{threshold}}/1000)",
        "notify_roles": "ADMIN,PHARMACIST",
        "channels": "in_app,sms",
        "cooldown_hours": "24",
    },
    {
        "indicator_code": "SURG_SITE_INFECTION",
        "comparator": "GT",
        "threshold_value": "3",
        "severity": "HIGH",
        "alert_message": "Infections du site opératoire > seuil OMS : {{value}}% (seuil : {{threshold}}%)",
        "notify_roles": "ADMIN,DOCTOR",
        "channels": "in_app,sms",
        "cooldown_hours": "168",
    },
    {
        "indicator_code": "BED_OCCUPANCY",
        "comparator": "GT",
        "threshold_value": "85",
        "severity": "MEDIUM",
        "alert_message": "Surcharge d'occupation des lits : {{value}}% (seuil : {{threshold}}%)",
        "notify_roles": "ADMIN",
        "channels": "in_app",
        "cooldown_hours": "6",
    },
    {
        "indicator_code": "FALL_RATE",
        "comparator": "GT",
        "threshold_value": "3",
        "severity": "HIGH",
        "alert_message": "Taux de chutes patient élevé : {{value}}/1000 (seuil HAS : {{threshold}}/1000)",
        "notify_roles": "ADMIN",
        "channels": "in_app",
        "cooldown_hours": "168",
    },
    {
        "indicator_code": "VAGINAL_DELIVERY_RATE",
        "comparator": "LT",
        "threshold_value": "80",
        "severity": "MEDIUM",
        "alert_message": "Taux d'accouchements voie basse faible : {{value}}% (cible OMS : > {{threshold}}%)",
        "notify_roles": "ADMIN,MIDWIFE",
        "channels": "in_app",
        "cooldown_hours": "720",  # 30 jours (monthly indicator)
    },
]


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed_default_indicators(db: Session, facility_id: str | None = None) -> int:
    """Insère les indicateurs prédéfinis (OMS/HAS) s'ils n'existent pas encore.

    Args:
        db: session SQLAlchemy
        facility_id: si fourni, ne crée que pour cette facility. Si None, crée
                     pour toutes les facilities existantes (ou global si aucune).

    Returns:
        Nombre d'indicateurs créés.
    """
    created = 0
    facilities = []
    if facility_id:
        facilities = [facility_id]
    else:
        from app.modules.facilities.models import Facility
        facilities = [f.id for f in db.query(Facility.id).all()]
        if not facilities:
            # Aucune facility — ne crée rien (les indicateurs seront seedés
            # ultérieurement quand une facility existera)
            return 0

    for fid in facilities:
        for ind_data in DEFAULT_INDICATORS:
            existing = (
                db.query(QualityIndicator)
                .filter(QualityIndicator.facility_id == fid)
                .filter(QualityIndicator.code == ind_data["code"])
                .first()
            )
            if existing:
                continue
            ind = QualityIndicator(
                facility_id=fid,
                code=ind_data["code"],
                name=ind_data["name"],
                category=ind_data["category"],
                description=ind_data["description"],
                unit=ind_data["unit"],
                target_value=ind_data["target_value"],
                frequency=ind_data["frequency"],
            )
            db.add(ind)
            created += 1

    db.commit()
    return created


def seed_default_thresholds(db: Session, facility_id: str | None = None) -> int:
    """Insère les seuils par défaut liés aux indicateurs prédéfinis."""
    created = 0
    facilities = []
    if facility_id:
        facilities = [facility_id]
    else:
        from app.modules.facilities.models import Facility
        facilities = [f.id for f in db.query(Facility.id).all()]
        if not facilities:
            return 0

    for fid in facilities:
        for th_data in DEFAULT_THRESHOLDS:
            indicator = (
                db.query(QualityIndicator)
                .filter(QualityIndicator.facility_id == fid)
                .filter(QualityIndicator.code == th_data["indicator_code"])
                .first()
            )
            if not indicator:
                continue
            existing = (
                db.query(QualityThreshold)
                .filter(QualityThreshold.facility_id == fid)
                .filter(QualityThreshold.indicator_id == indicator.id)
                .filter(QualityThreshold.comparator == th_data["comparator"])
                .filter(QualityThreshold.threshold_value == th_data["threshold_value"])
                .first()
            )
            if existing:
                continue
            th = QualityThreshold(
                facility_id=fid,
                indicator_id=indicator.id,
                comparator=th_data["comparator"],
                threshold_value=th_data["threshold_value"],
                severity=th_data["severity"],
                alert_message=th_data["alert_message"],
                notify_roles=th_data["notify_roles"],
                channels=th_data["channels"],
                cooldown_hours=th_data["cooldown_hours"],
                enabled="true",
            )
            db.add(th)
            created += 1

    db.commit()
    return created


# ---------------------------------------------------------------------------
# Dashboard computation
# ---------------------------------------------------------------------------

def compute_dashboard(
    db: Session,
    *,
    facility_id: str | None = None,
    department_id: str | None = None,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> dict[str, Any]:
    """Calcule le dashboard qualité agrégé pour une période.

    Retourne :
    - `kpis` : liste des derniers KPIs mesurés (par indicateur).
    - `incidents` : agrégats par type/sévérité/statut.
    - `alerts` : alertes ouvertes récentes.
    - `trends` : séries temporelles sur la période (par indicateur principal).
    """
    period_end = period_end or utcnow()
    period_start = period_start or (period_end - timedelta(days=30))

    # KPIs : dernières mesures par indicateur
    indicators_q = db.query(QualityIndicator)
    if facility_id:
        indicators_q = indicators_q.filter(QualityIndicator.facility_id == facility_id)
    indicators = indicators_q.order_by(QualityIndicator.category, QualityIndicator.code).all()

    kpis = []
    for ind in indicators:
        last_measure = (
            db.query(QualityMeasurement)
            .filter(QualityMeasurement.indicator_id == ind.id)
            .filter(QualityMeasurement.period_start >= period_start)
            .filter(QualityMeasurement.period_end <= period_end)
            .order_by(QualityMeasurement.period_end.desc())
            .first()
        )
        if not last_measure:
            # Pas de mesure sur la période — on prend la plus récente absolue
            last_measure = (
                db.query(QualityMeasurement)
                .filter(QualityMeasurement.indicator_id == ind.id)
                .order_by(QualityMeasurement.period_end.desc())
                .first()
            )
        kpis.append({
            "indicator_id": ind.id,
            "indicator_code": ind.code,
            "indicator_name": ind.name,
            "category": ind.category,
            "unit": ind.unit,
            "target_value": ind.target_value,
            "frequency": ind.frequency,
            "last_value": last_measure.value if last_measure else None,
            "last_period_start": last_measure.period_start.isoformat() if last_measure and last_measure.period_start else None,
            "last_period_end": last_measure.period_end.isoformat() if last_measure and last_measure.period_end else None,
            "has_data": last_measure is not None,
        })

    # Incidents : agrégats
    inc_q = db.query(IncidentReport)
    if facility_id:
        inc_q = inc_q.filter(IncidentReport.facility_id == facility_id)
    inc_q = inc_q.filter(IncidentReport.incident_date >= period_start).filter(IncidentReport.incident_date <= period_end)
    incidents_total = inc_q.count()
    incidents_by_type = (
        db.query(IncidentReport.incident_type, func.count(IncidentReport.id))
        .filter(IncidentReport.facility_id == facility_id if facility_id else True)
        .filter(IncidentReport.incident_date >= period_start)
        .filter(IncidentReport.incident_date <= period_end)
        .group_by(IncidentReport.incident_type)
        .all()
    )
    incidents_by_severity = (
        db.query(IncidentReport.severity, func.count(IncidentReport.id))
        .filter(IncidentReport.facility_id == facility_id if facility_id else True)
        .filter(IncidentReport.incident_date >= period_start)
        .filter(IncidentReport.incident_date <= period_end)
        .group_by(IncidentReport.severity)
        .all()
    )
    incidents_by_status = (
        db.query(IncidentReport.status, func.count(IncidentReport.id))
        .filter(IncidentReport.facility_id == facility_id if facility_id else True)
        .filter(IncidentReport.incident_date >= period_start)
        .filter(IncidentReport.incident_date <= period_end)
        .group_by(IncidentReport.status)
        .all()
    )

    # Délai moyen de traitement des incidents (RESOLVED uniquement)
    resolved_incidents = (
        db.query(IncidentReport)
        .filter(IncidentReport.status.in_(["RESOLVED", "CLOSED"]))
        .filter(IncidentReport.facility_id == facility_id if facility_id else True)
        .filter(IncidentReport.incident_date >= period_start)
        .filter(IncidentReport.incident_date <= period_end)
        .all()
    )
    # Pour le délai, on utilise created_at → résolution (le statut RESOLVED ne
    # porte pas de timestamp dédié — approximation)
    avg_resolution_hours = None
    if resolved_incidents:
        total_hours = 0
        count = 0
        for inc in resolved_incidents:
            if inc.created_at:
                delta = (period_end - inc.created_at).total_seconds() / 3600
                total_hours += delta
                count += 1
        if count > 0:
            avg_resolution_hours = round(total_hours / count, 1)

    # Alertes ouvertes
    alerts_q = db.query(QualityAlert)
    if facility_id:
        alerts_q = alerts_q.filter(QualityAlert.facility_id == facility_id)
    alerts_open = alerts_q.filter(QualityAlert.status == "OPEN").count()
    alerts_acked = alerts_q.filter(QualityAlert.status == "ACKNOWLEDGED").count()
    alerts_resolved = alerts_q.filter(QualityAlert.status == "RESOLVED").count()
    alerts_recent = (
        alerts_q.order_by(QualityAlert.created_at.desc())
        .limit(10)
        .all()
    )

    # Tendances : séries temporelles sur la période pour les 5 premiers indicateurs
    trends = []
    for ind in indicators[:5]:
        measures = (
            db.query(QualityMeasurement)
            .filter(QualityMeasurement.indicator_id == ind.id)
            .filter(QualityMeasurement.period_start >= period_start)
            .filter(QualityMeasurement.period_end <= period_end)
            .order_by(QualityMeasurement.period_start)
            .all()
        )
        trends.append({
            "indicator_code": ind.code,
            "indicator_name": ind.name,
            "unit": ind.unit,
            "target_value": ind.target_value,
            "data_points": [
                {
                    "period_start": m.period_start.isoformat() if m.period_start else None,
                    "period_end": m.period_end.isoformat() if m.period_end else None,
                    "value": m.value,
                }
                for m in measures
            ],
        })

    return {
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "facility_id": facility_id,
        "department_id": department_id,
        "kpis": kpis,
        "incidents": {
            "total": incidents_total,
            "by_type": [{"type": t, "count": int(c)} for (t, c) in incidents_by_type],
            "by_severity": [{"severity": s, "count": int(c)} for (s, c) in incidents_by_severity],
            "by_status": [{"status": s, "count": int(c)} for (s, c) in incidents_by_status],
            "avg_resolution_hours": avg_resolution_hours,
        },
        "alerts": {
            "open": alerts_open,
            "acknowledged": alerts_acked,
            "resolved": alerts_resolved,
            "recent": [a.to_dict() for a in alerts_recent],
        },
        "trends": trends,
        "thresholds_count": db.query(QualityThreshold).filter(
            QualityThreshold.facility_id == facility_id if facility_id else True
        ).count(),
    }


# ---------------------------------------------------------------------------
# Threshold evaluation + alert raising
# ---------------------------------------------------------------------------

def check_thresholds(
    db: Session,
    *,
    measurement: QualityMeasurement | None = None,
    facility_id: str | None = None,
) -> list[QualityAlert]:
    """Évalue les seuils pour une mesure donnée (ou toutes les mesures récentes).

    Si `measurement` est fourni, n'évalue que les thresholds de son indicateur.
    Sinon, évalue toutes les mesures des 7 derniers jours pour `facility_id`.

    Pour chaque seuil franchi :
    1. Vérifie le cooldown (pas d'alerte similaire dans les `cooldown_hours` dernières heures).
    2. Lève une `QualityAlert` OPEN.
    3. Notifie les rôles configurés via `notify()` du module notifications.
    4. Déclenche un SMS si la règle de routage le permet (catégorie `quality_alert`).

    NE LEVE JAMAIS d'exception — toute erreur de notification est journalisée.
    """
    raised: list[QualityAlert] = []

    # Déterminer les thresholds à évaluer
    if measurement:
        thresholds_q = (
            db.query(QualityThreshold)
            .filter(QualityThreshold.indicator_id == measurement.indicator_id)
            .filter(QualityThreshold.enabled == "true")
        )
        if measurement.facility_id:
            thresholds_q = thresholds_q.filter(
                (QualityThreshold.facility_id == measurement.facility_id) |
                (QualityThreshold.facility_id.is_(None))
            )
        thresholds = thresholds_q.all()
        measurements_to_check = [measurement]
    else:
        # Toutes les mesures des 7 derniers jours
        since = utcnow() - timedelta(days=7)
        measures_q = (
            db.query(QualityMeasurement)
            .filter(QualityMeasurement.created_at >= since)
        )
        if facility_id:
            measures_q = measures_q.filter(QualityMeasurement.facility_id == facility_id)
        measurements_to_check = measures_q.all()

        # Tous les thresholds enabled
        thresholds_q = db.query(QualityThreshold).filter(QualityThreshold.enabled == "true")
        if facility_id:
            thresholds_q = thresholds_q.filter(
                (QualityThreshold.facility_id == facility_id) |
                (QualityThreshold.facility_id.is_(None))
            )
        thresholds = thresholds_q.all()

    # Indexer les thresholds par indicator_id pour lookup rapide
    thresholds_by_indicator: dict[str, list[QualityThreshold]] = {}
    for th in thresholds:
        thresholds_by_indicator.setdefault(th.indicator_id, []).append(th)

    for m in measurements_to_check:
        ths = thresholds_by_indicator.get(m.indicator_id, [])
        for th in ths:
            # Vérifier le comparateur
            if th.comparator not in COMPARATORS:
                continue
            if not evaluate_threshold(th.comparator, m.value, th.threshold_value):
                continue

            # Cooldown : pas d'alerte similaire dans la fenêtre
            cooldown_hours = 24
            if th.cooldown_hours and str(th.cooldown_hours).isdigit():
                cooldown_hours = int(th.cooldown_hours)
            cooldown_since = utcnow() - timedelta(hours=cooldown_hours)
            recent_alert = (
                db.query(QualityAlert)
                .filter(QualityAlert.threshold_id == th.id)
                .filter(QualityAlert.created_at >= cooldown_since)
                .filter(QualityAlert.status.in_(["OPEN", "ACKNOWLEDGED"]))
                .first()
            )
            if recent_alert:
                continue  # cooldown actif

            # Lever l'alerte
            title = f"[{th.severity}] Seuil qualité franchi"
            message = (th.alert_message or "").replace("{{value}}", str(m.value)).replace("{{threshold}}", str(th.threshold_value))

            alert = QualityAlert(
                facility_id=m.facility_id,
                department_id=th.department_id,
                threshold_id=th.id,
                measurement_id=m.id,
                indicator_id=m.indicator_id,
                status="OPEN",
                severity=th.severity,
                title=title,
                message=message,
                observed_value=str(m.value),
                threshold_value=str(th.threshold_value),
                comparator=th.comparator,
            )
            db.add(alert)
            db.commit()
            db.refresh(alert)
            raised.append(alert)

            # Notifier (best-effort)
            try:
                _notify_alert(db, alert, th)
            except Exception as e:
                logger.warning("Alert notification failed for alert %s: %s", alert.id, e)

    return raised


def _notify_alert(db: Session, alert: QualityAlert, threshold: QualityThreshold) -> None:
    """Envoie une notification multi-canal pour une alerte qualité.

    - Identifie les destinataires par rôle (notify_roles) dans la facility.
    - Appelle `notify()` du module notifications.
    - Si la catégorie `quality_alert` a une règle de routage SMS, un SMS est envoyé.
    """
    from app.modules.notifications.service import notify
    from app.modules.users.models import User

    if not threshold.notify_roles:
        return

    roles = [r for r in threshold.notify_roles.split(",") if r]
    channels = [c for c in (threshold.channels or "in_app").split(",") if c]

    # Trouver les destinataires (SUPER_ADMIN toujours + rôles configurés dans la facility)
    recipients_q = db.query(User).filter(User.is_active.is_(True))
    if alert.facility_id:
        recipients_q = recipients_q.filter(
            (User.facility_id == alert.facility_id) | (User.role == "SUPER_ADMIN")
        )
    recipients_q = recipients_q.filter(User.role.in_(roles))
    recipients = recipients_q.all()

    # Si aucun destinataire direct, notifier les SUPER_ADMIN globaux
    if not recipients:
        recipients = db.query(User).filter(User.role == "SUPER_ADMIN").filter(User.is_active.is_(True)).all()

    priority = "urgent" if alert.severity == "CRITICAL" else "high"

    for recipient in recipients:
        try:
            notif = notify(
                db=db,
                recipient_id=recipient.id,
                title=alert.title,
                body=alert.message,
                category="quality_alert",
                priority=priority,
                channels=channels,
                facility_id=alert.facility_id,
                resource_type="quality_alert",
                resource_id=alert.id,
                recipient_email=getattr(recipient, "email", None),
                recipient_phone=getattr(recipient, "phone", None),
            )
            # Lier la notification à l'alerte (premier destinataire seulement)
            if not alert.notification_id:
                alert.notification_id = notif.id
                db.commit()
        except Exception as e:
            logger.warning("notify() failed for recipient %s: %s", recipient.id, e)


# ---------------------------------------------------------------------------
# Alert lifecycle helpers
# ---------------------------------------------------------------------------

def acknowledge_alert(
    db: Session,
    alert_id: str,
    user_id: str,
    assign_to: str | None = None,
) -> QualityAlert | None:
    """Marque une alerte comme prise en charge (ACKNOWLEDGED)."""
    alert = db.query(QualityAlert).filter(QualityAlert.id == alert_id).first()
    if not alert:
        return None
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_at = utcnow()
    alert.acknowledged_by = user_id
    if assign_to:
        alert.assigned_to = assign_to
    elif not alert.assigned_to:
        alert.assigned_to = user_id
    db.commit()
    db.refresh(alert)
    return alert


def resolve_alert(
    db: Session,
    alert_id: str,
    user_id: str,
    resolution_note: str,
) -> QualityAlert | None:
    """Marque une alerte comme résolue (RESOLVED) avec note de résolution."""
    alert = db.query(QualityAlert).filter(QualityAlert.id == alert_id).first()
    if not alert:
        return None
    alert.status = "RESOLVED"
    alert.resolved_at = utcnow()
    alert.resolved_by = user_id
    alert.resolution_note = resolution_note
    db.commit()
    db.refresh(alert)
    return alert


def close_alert(
    db: Session,
    alert_id: str,
    user_id: str,
) -> QualityAlert | None:
    """Clôture une alerte résolue (CLOSED)."""
    alert = db.query(QualityAlert).filter(QualityAlert.id == alert_id).first()
    if not alert:
        return None
    alert.status = "CLOSED"
    alert.closed_at = utcnow()
    db.commit()
    db.refresh(alert)
    return alert
