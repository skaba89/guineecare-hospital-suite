"""Modèles Dashboard Qualité v1.4.0 — seuils d'alerte automatique et alertes levées.

Deux nouvelles tables :
- `QualityThreshold` : définit pour un indicateur (par facility + service) un seuil
  au-delà duquel une alerte est automatiquement levée. Supporte 4 comparateurs
  (LT, LE, GT, GE, EQ) et une fenêtre temporelle (rolling window).
- `QualityAlert` : alerte concrète levée quand une mesure dépasse un seuil. Liée
  à la mesure déclencheuse, avec statut (OPEN, ACKNOWLEDGED, RESOLVED) et
  assignée à un responsable.

Conventions :
- Multi-tenant via `facility_id`.
- Audit trail : toute ouverture/resolution d'alerte est tracée dans `audit_logs`.
- Notifications : à l'ouverture d'une alerte OPEN, le service `notify()` du module
  notifications est appelé pour pousser une notification multi-canal à la direction
  qualité (la catégorie `quality_alert` déclenche un SMS via la règle de routage).
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.datetime import utcnow
from app.db.base import Base


def _uuid() -> str:
    return str(uuid4())


# Comparateurs supportés pour les seuils
COMPARATORS = {"LT", "LE", "GT", "GE", "EQ"}
# LT = <  (alerte si mesure < threshold)
# LE = <= (alerte si mesure <= threshold)
# GT = >  (alerte si mesure > threshold)  — défaut (ex: taux infection > 5%)
# GE = >= (alerte si mesure >= threshold)
# EQ = == (alerte si mesure == threshold — utile pour compteurs critiques)


class QualityThreshold(Base):
    """Seuil d'alerte pour un indicateur qualité.

    Exemples :
    - Taux d'infection nosocomiale > 5% → alerte CRITICAL
    - Taux de réadmission 30j > 10% → alerte HIGH
    - Satisfaction patient < 80% → alerte HIGH
    - Délai moyen prise en charge urgences > 4h → alerte MEDIUM

    Un threshold peut être facility-spécifique ou global (facility_id NULL).
    Il peut être service-spécifique (department_id) ou global au facility.
    """
    __tablename__ = "quality_thresholds"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Périmètre
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)

    # Indicateur concerné
    indicator_id = Column(String(36), ForeignKey("quality_indicators.id"), nullable=False, index=True)

    # Définition du seuil
    comparator = Column(String(8), nullable=False, default="GT")  # LT|LE|GT|GE|EQ
    threshold_value = Column(String(100), nullable=False)  # string car certains indicateurs sont qualitatifs

    # Gravité de l'alerte levée
    severity = Column(String(16), nullable=False, default="HIGH")  # LOW|MEDIUM|HIGH|CRITICAL

    # Message d'alerte (template — {{value}} et {{threshold}} substitués)
    alert_message = Column(Text, nullable=True)

    # Destinataires : rôles à notifier (CSV). Défaut : ADMIN, le cas échéant DOCTOR du service.
    notify_roles = Column(String(128), nullable=True, default="ADMIN")

    # Canaux de notification (CSV : in_app,sms,email). Surcharge la règle de routage.
    channels = Column(String(64), nullable=False, default="in_app")

    enabled = Column(String(8), nullable=False, default="true")  # SQLite-compatible bool

    # Fenêtre temporelle (en heures) pour éviter les alertes répétées
    cooldown_hours = Column(String(8), nullable=True, default="24")  # 24h entre 2 alertes identiques

    indicator = relationship("QualityIndicator", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "facility_id": self.facility_id,
            "department_id": self.department_id,
            "indicator_id": self.indicator_id,
            "comparator": self.comparator,
            "threshold_value": self.threshold_value,
            "severity": self.severity,
            "alert_message": self.alert_message,
            "notify_roles": [r for r in (self.notify_roles or "").split(",") if r],
            "channels": [c for c in (self.channels or "").split(",") if c],
            "enabled": str(self.enabled).lower() == "true",
            "cooldown_hours": int(self.cooldown_hours) if self.cooldown_hours and str(self.cooldown_hours).isdigit() else 24,
        }


class QualityAlert(Base):
    """Alerte qualité levée quand une mesure dépasse un seuil.

    Cycle de vie :
    - OPEN : alerte levée automatiquement par le service `check_thresholds()`.
    - ACKNOWLEDGED : un humain a pris connaissance (assigné à `assigned_to`).
    - RESOLVED : la cause racine a été traitée, `resolution_note` documente l'action.
    - CLOSED : clôturée (pas d'action supplémentaire nécessaire).

    Liens :
    - `threshold_id` : seuil déclencheur.
    - `measurement_id` : mesure qui a déclenché l'alerte.
    - `notification_id` : notification envoyée (pour traçabilité multi-canal).
    """
    __tablename__ = "quality_alerts"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    # Périmètre
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=True, index=True)
    department_id = Column(String(36), ForeignKey("departments.id"), nullable=True, index=True)

    # Liens
    threshold_id = Column(String(36), ForeignKey("quality_thresholds.id"), nullable=True, index=True)
    measurement_id = Column(String(36), ForeignKey("quality_measurements.id"), nullable=True, index=True)
    notification_id = Column(String(36), ForeignKey("notifications.id"), nullable=True, index=True)
    indicator_id = Column(String(36), ForeignKey("quality_indicators.id"), nullable=True, index=True)

    # État
    status = Column(String(16), nullable=False, default="OPEN", index=True)
    # OPEN | ACKNOWLEDGED | RESOLVED | CLOSED

    severity = Column(String(16), nullable=False, default="HIGH")
    # LOW | MEDIUM | HIGH | CRITICAL

    # Contenu
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)
    observed_value = Column(String(100), nullable=True)
    threshold_value = Column(String(100), nullable=True)
    comparator = Column(String(8), nullable=True)

    # Gestion humaine
    assigned_to = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(36), ForeignKey("users.id"), nullable=True)
    resolution_note = Column(Text, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    threshold = relationship("QualityThreshold", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "facility_id": self.facility_id,
            "department_id": self.department_id,
            "threshold_id": self.threshold_id,
            "measurement_id": self.measurement_id,
            "notification_id": self.notification_id,
            "indicator_id": self.indicator_id,
            "status": self.status,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "observed_value": self.observed_value,
            "threshold_value": self.threshold_value,
            "comparator": self.comparator,
            "assigned_to": self.assigned_to,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "resolution_note": self.resolution_note,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }


# ---------------------------------------------------------------------------
# Comparaison seuil / mesure
# ---------------------------------------------------------------------------

def _to_float(value: str | None) -> float | None:
    """Tente de convertir une valeur en float. Retourne None si impossible."""
    if value is None:
        return None
    try:
        return float(str(value).strip().rstrip("%"))
    except (ValueError, TypeError):
        return None


def evaluate_threshold(
    comparator: str,
    observed_value: str,
    threshold_value: str,
) -> bool:
    """Retourne True si l'alerte doit être levée (i.e. le seuil est franchi).

    >>> evaluate_threshold("GT", "8", "5")
    True
    >>> evaluate_threshold("LT", "8", "5")
    False
    >>> evaluate_threshold("GE", "5", "5")
    True
    """
    obs = _to_float(observed_value)
    thr = _to_float(threshold_value)
    if obs is None or thr is None:
        # Comparaison string pour les valeurs non numériques (ex: catégories)
        if comparator == "EQ":
            return str(observed_value) == str(threshold_value)
        return False

    if comparator == "LT":
        return obs < thr
    if comparator == "LE":
        return obs <= thr
    if comparator == "GT":
        return obs > thr
    if comparator == "GE":
        return obs >= thr
    if comparator == "EQ":
        return obs == thr
    return False
