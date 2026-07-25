"""Modèles SMS v1.4.0 — providers multicanal (Orange/MTN/Moov), messages, règles de routage.

Ces tables permettent :
- `SmsProvider` : configuration des opérateurs locaux (URL endpoint, credentials, sender ID).
- `SmsMessage` : journal de tous les SMS envoyés (succès/échec, provider utilisé, coût).
- `SmsRoutingRule` : règles de routage par catégorie de notification (urgences → SMS, etc.).

Conventions :
- Multi-tenant via `facility_id` (nullable pour les providers globaux SUPER_ADMIN).
- Jamais de credentials en clair : stockés chiffrés côté service (Fernet optionnel).
- Audit trail : toute émission SMS est journalisée dans `audit_logs` par l'appelant.
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.datetime import utcnow
from app.db.base import Base


def _uuid() -> str:
    return str(uuid4())


class SmsProvider(Base):
    """Configuration d'un opérateur SMS local (Orange, MTN, Moov, Mock).

    Les credentials (api_key, api_secret) sont stockés sous forme chiffrée via
    le service `sms_service._encrypt_credential`. En environnement local/test
    sans clé Fernet, ils sont stockés en clair (mode dev uniquement).
    """
    __tablename__ = "sms_providers"

    id = Column(String(36), primary_key=True, default=_uuid)
    code = Column(String(32), unique=True, index=True, nullable=False)  # orange | mtn | moov | mock
    name = Column(String(128), nullable=False)  # "Orange Guinée SMS Pro"
    enabled = Column(Boolean, nullable=False, default=True, index=True)

    # Endpoint HTTP de l'opérateur (mock = in-process, jamais réseau)
    api_url = Column(String(512), nullable=True)
    # Credentials chiffrés (jamais lus par l'API en clair — write-only côté admin)
    api_key_encrypted = Column(Text, nullable=True)
    api_secret_encrypted = Column(Text, nullable=True)
    sender_id = Column(String(32), nullable=True)  # "GUINEECARE" ou numéro court

    # Coût par SMS en GNF (Franc Guinéen) — pour le suivi budgétaire
    cost_per_sms_gnf = Column(Integer, nullable=True, default=0)

    # Limits opérateur (par défaut Orange Guinée = 10 SMS/s)
    rate_per_second = Column(Integer, nullable=False, default=10)
    daily_quota = Column(Integer, nullable=True)  # null = illimité

    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    messages = relationship("SmsMessage", back_populates="provider", lazy="select")

    def to_dict(self, include_credentials: bool = False) -> dict:
        d = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "enabled": bool(self.enabled),
            "api_url": self.api_url,
            "sender_id": self.sender_id,
            "cost_per_sms_gnf": self.cost_per_sms_gnf,
            "rate_per_second": self.rate_per_second,
            "daily_quota": self.daily_quota,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_credentials:
            d["has_api_key"] = bool(self.api_key_encrypted)
            d["has_api_secret"] = bool(self.api_secret_encrypted)
        return d


class SmsMessage(Base):
    """Journal de tous les SMS envoyés (succès, échec, coût, provider utilisé).

    Permet :
    - Le suivi budgétaire (somme de `cost_gnf`).
    - Le diagnostic des échecs (`error_code`, `error_message`).
    - L'audit forensique (lien vers `notification_id` et `recipient_id`).
    """
    __tablename__ = "sms_messages"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)

    # Multi-tenant : facility_id du destinataire (null pour les SMS système globaux)
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=True, index=True)

    # Provider utilisé pour l'envoi
    provider_id = Column(String(36), ForeignKey("sms_providers.id"), nullable=True, index=True)
    provider_code = Column(String(32), nullable=False)  # snapshot au moment de l'envoi

    # Destinataire
    recipient_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    recipient_phone = Column(String(32), nullable=False, index=True)  # E.164 +224XXXXXXXXX

    # Contenu
    body = Column(Text, nullable=False)
    category = Column(String(32), nullable=False, index=True)  # lab_critical, appointment, etc.
    priority = Column(String(16), nullable=False, default="normal")  # low|normal|high|urgent

    # Lien vers la notification in-app (pour traçabilité multi-canal)
    notification_id = Column(String(36), ForeignKey("notifications.id"), nullable=True, index=True)

    # État de livraison
    status = Column(String(32), nullable=False, default="PENDING", index=True)
    # PENDING | SENT | DELIVERED | FAILED | REJECTED | EXPIRED
    operator_message_id = Column(String(128), nullable=True)  # ID retourné par l'opérateur
    error_code = Column(String(32), nullable=True)
    error_message = Column(Text, nullable=True)

    # Coût effectif (peut différer de `cost_per_sms_gnf` en cas de retry)
    cost_gnf = Column(Integer, nullable=True, default=0)

    # Tentatives
    attempts = Column(Integer, nullable=False, default=0)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    provider = relationship("SmsProvider", back_populates="messages", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "facility_id": self.facility_id,
            "provider_id": self.provider_id,
            "provider_code": self.provider_code,
            "recipient_id": self.recipient_id,
            "recipient_phone": self.recipient_phone,
            "body": self.body,
            "category": self.category,
            "priority": self.priority,
            "notification_id": self.notification_id,
            "status": self.status,
            "operator_message_id": self.operator_message_id,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "cost_gnf": self.cost_gnf,
            "attempts": self.attempts,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }


class SmsRoutingRule(Base):
    """Règle de routage : quelle catégorie de notification va sur quel canal.

    Exemples :
    - `lab_critical` → channels=[sms,in_app], priority=urgent, min_severity=CRITICAL
    - `appointment` → channels=[in_app], priority=normal
    - `incident_critical` → channels=[sms,in_app,email], priority=urgent

    La règle est matchée par `category` (priorité au code le plus spécifique).
    `min_priority` filtre les notifications : seules celles avec priorité >= min_priority
    déclenchent un SMS.
    """
    __tablename__ = "sms_routing_rules"

    id = Column(String(36), primary_key=True, default=_uuid)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    # Périmètre : null = global, sinon facility-spécifique
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=True, index=True)

    # Catégorie de notification à laquelle la règle s'applique
    category = Column(String(32), nullable=False, index=True)

    # Canaux activés pour cette catégorie (CSV : in_app,sms,email)
    channels = Column(String(64), nullable=False, default="in_app")

    # Priorité minimale pour déclencher le SMS
    # low < normal < high < urgent
    min_priority = Column(String(16), nullable=False, default="normal")

    # Provider préféré pour cette catégorie (null = provider par défaut de la facility)
    preferred_provider_id = Column(String(36), ForeignKey("sms_providers.id"), nullable=True)

    # Activer/désactiver la règle sans la supprimer
    enabled = Column(Boolean, nullable=False, default=True, index=True)

    # Description libre (aide-mémoire)
    description = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "facility_id": self.facility_id,
            "category": self.category,
            "channels": [c for c in (self.channels or "").split(",") if c],
            "min_priority": self.min_priority,
            "preferred_provider_id": self.preferred_provider_id,
            "enabled": bool(self.enabled),
            "description": self.description,
        }


# Constantes d'ordres de priorité pour comparaison
PRIORITY_ORDER = {"low": 1, "normal": 2, "high": 3, "urgent": 4}


def priority_meets_min(priority: str, min_priority: str) -> bool:
    """Vérifie qu'une priorité donnée atteint le seuil minimal requis.

    >>> priority_meets_min("urgent", "normal")
    True
    >>> priority_meets_min("low", "normal")
    False
    """
    return PRIORITY_ORDER.get(priority, 2) >= PRIORITY_ORDER.get(min_priority, 2)
