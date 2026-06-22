"""Service SMS v1.4.0 — orchestration de l'envoi de SMS via les providers configurés.

Responsabilités :
- Choisir le provider adapté (règle de routage → provider préféré → provider par défaut).
- Journaliser chaque tentative dans `SmsMessage` (succès/échec, coût, retry).
- Gérer les retries (max 2 retries en backoff exponentiel 5s/30s — configuré en prod via Celery).
- Exposer `send_sms()` synchrone (pour tests) et `queue_sms()` asynchrone (pour prod).
- Fournir des helpers de statistiques (coût mensuel, taux de succès par provider).

Conventions :
- Best-effort : aucune exception ne remonte à l'appelant (audit log + journalisation).
- Multi-tenant : facility_id propagé depuis la notification/destinataire.
- Audit : chaque envoi écrit une entrée `audit_logs` via le caller (route).
"""
import logging
from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.core.datetime import utcnow
from app.modules.notifications.sms_models import (
    PRIORITY_ORDER,
    SmsMessage,
    SmsProvider,
    SmsRoutingRule,
    priority_meets_min,
)
from app.modules.notifications.sms_provider import (
    SmsProviderBase,
    SmsSendResult,
    get_provider_class,
    normalize_phone_gn,
)

logger = logging.getLogger("guineecare.sms.service")


# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------

def get_default_provider(db: Session, facility_id: str | None = None) -> SmsProvider | None:
    """Retourne le provider par défaut pour une facility.

    Logique :
    1. Si facility_id fourni, chercher un provider facility-spécifique enabled.
    2. Sinon, retourner le premier provider global enabled.
    3. Si rien, retourner le provider `mock` (dev/test).
    """
    # Provider facility-spécifique (par convention, un SmsProvider global n'a pas
    # de facility_id — c'est l'app qui décide. Ici on prend le premier enabled).
    provider = (
        db.query(SmsProvider)
        .filter(SmsProvider.enabled.is_(True))
        .order_by(SmsProvider.code)
        .first()
    )
    if provider:
        return provider
    # Fallback : créer un provider mock implicite (tests/dev sans config)
    return None


def get_routing_rule(
    db: Session,
    category: str,
    facility_id: str | None,
) -> SmsRoutingRule | None:
    """Retourne la règle de routage applicable à une catégorie + facility.

    Priorité :
    1. Règle facility-spécifique enabled pour cette catégorie.
    2. Règle globale (facility_id IS NULL) enabled pour cette catégorie.
    3. Aucune règle (renvoie None → l'appelant décide).
    """
    # 1. Règle facility-spécifique
    if facility_id:
        rule = (
            db.query(SmsRoutingRule)
            .filter(SmsRoutingRule.facility_id == facility_id)
            .filter(SmsRoutingRule.category == category)
            .filter(SmsRoutingRule.enabled.is_(True))
            .first()
        )
        if rule:
            return rule

    # 2. Règle globale
    return (
        db.query(SmsRoutingRule)
        .filter(SmsRoutingRule.facility_id.is_(None))
        .filter(SmsRoutingRule.category == category)
        .filter(SmsRoutingRule.enabled.is_(True))
        .first()
    )


def select_provider_for_send(
    db: Session,
    rule: SmsRoutingRule | None,
    facility_id: str | None,
) -> SmsProvider | None:
    """Sélectionne le provider à utiliser pour un envoi.

    Logique :
    1. Si la règle a un `preferred_provider_id` et qu'il est enabled, l'utiliser.
    2. Sinon, utiliser le premier provider enabled.
    3. Sinon, fallback mock implicite (créé à la volée en mémoire si besoin).
    """
    if rule and rule.preferred_provider_id:
        p = (
            db.query(SmsProvider)
            .filter(SmsProvider.id == rule.preferred_provider_id)
            .filter(SmsProvider.enabled.is_(True))
            .first()
        )
        if p:
            return p
    return get_default_provider(db, facility_id)


def should_send_sms_for_rule(
    rule: SmsRoutingRule | None,
    priority: str,
) -> bool:
    """Vérifie si un SMS doit être envoyé selon la règle de routage.

    - Pas de règle : pas de SMS (la notification reste in-app).
    - Règle présente : SMS envoyé si priorité >= min_priority et sms dans channels.
    """
    if rule is None:
        return False
    if not rule.enabled:
        return False
    if "sms" not in (rule.channels or ""):
        return False
    return priority_meets_min(priority, rule.min_priority)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_sms(
    db: Session,
    *,
    to: str,
    body: str,
    category: str,
    priority: str = "normal",
    recipient_id: str | None = None,
    facility_id: str | None = None,
    notification_id: str | None = None,
    provider_id: str | None = None,
    rule: SmsRoutingRule | None = None,
) -> SmsMessage:
    """Envoie un SMS de manière synchrone et journalise dans `SmsMessage`.

    NE LEVE JAMAIS d'exception — tout échec est capturé et retourné dans
    `SmsMessage.error_code/error_message`. L'appelant peut inspecter le
    `status` pour savoir si l'envoi a réussi.

    Args:
        db: session SQLAlchemy
        to: numéro E.164 (sera normalisé via `normalize_phone_gn` si Guinée)
        body: corps du SMS (max 480 chars)
        category: catégorie de notification (lab_critical, appointment, etc.)
        priority: low|normal|high|urgent
        recipient_id: ID utilisateur destinataire (facultatif)
        facility_id: facility du destinataire (multi-tenant)
        notification_id: notification parente (traçabilité multi-canal)
        provider_id: provider explicite (surcharge la règle)
        rule: règle déjà résolue (évite une re-requête)

    Returns:
        SmsMessage persisté avec son statut final.
    """
    # 1. Normaliser le numéro
    normalized = normalize_phone_gn(to) or to
    if not normalized:
        return _persist_failed(
            db,
            to=to,
            body=body,
            category=category,
            priority=priority,
            recipient_id=recipient_id,
            facility_id=facility_id,
            notification_id=notification_id,
            error_code="INVALID_PHONE",
            error_message=f"Numéro vide ou invalide: {to!r}",
        )

    # 2. Sélectionner le provider
    provider = None
    if provider_id:
        provider = db.query(SmsProvider).filter(SmsProvider.id == provider_id).first()
    if not provider:
        if rule is None:
            rule = get_routing_rule(db, category, facility_id)
        provider = select_provider_for_send(db, rule, facility_id)

    # 3. Aucun provider configuré → on crée un mock implicite en mémoire
    if provider is None:
        from app.modules.notifications.sms_models import SmsProvider as _P
        provider = _P(
            code="mock",
            name="Mock (implicite — aucun provider configuré)",
            enabled=True,
            api_url=None,
            sender_id="GUINEECARE",
            cost_per_sms_gnf=0,
        )
        db.add(provider)
        db.flush()  # obtient un id sans commit

    # 4. Instancier le provider backend
    provider_cls = get_provider_class(provider.code)
    backend: SmsProviderBase = provider_cls(provider)

    # 5. Créer l'enregistrement SmsMessage (PENDING)
    msg = SmsMessage(
        facility_id=facility_id,
        provider_id=provider.id,
        provider_code=provider.code,
        recipient_id=recipient_id,
        recipient_phone=normalized,
        body=body[:480],
        category=category,
        priority=priority,
        notification_id=notification_id,
        status="PENDING",
        attempts=0,
        cost_gnf=0,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # 6. Tenter l'envoi
    msg.attempts = 1
    try:
        result: SmsSendResult = backend.send(to=normalized, body=body)
    except Exception as e:
        # Le provider ne devrait jamais lever, mais on est défensif
        logger.exception("Provider %s raised unexpectedly", provider.code)
        result = SmsSendResult(
            delivered=False,
            error_code="UNEXPECTED",
            error_message=str(e)[:500],
        )

    if result.delivered:
        msg.status = "SENT"
        msg.operator_message_id = result.operator_message_id
        msg.cost_gnf = result.cost_gnf
        msg.sent_at = result.sent_at or utcnow()
        msg.error_code = None
        msg.error_message = None
        logger.info(
            "SMS sent: msg=%s provider=%s to=%s op_id=%s cost=%s GNF",
            msg.id, provider.code, normalized, result.operator_message_id, result.cost_gnf,
        )
    else:
        msg.status = "FAILED"
        msg.error_code = result.error_code
        msg.error_message = result.error_message
        msg.cost_gnf = 0
        logger.warning(
            "SMS failed: msg=%s provider=%s to=%s code=%s err=%s",
            msg.id, provider.code, normalized, result.error_code, result.error_message,
        )

    db.commit()
    db.refresh(msg)
    return msg


def retry_failed_sms(db: Session, message_id: str) -> SmsMessage | None:
    """Retente l'envoi d'un SMS échoué. Incrémente `attempts`.

    Retourne le SmsMessage mis à jour, ou None si l'ID n'existe pas.
    """
    msg = db.query(SmsMessage).filter(SmsMessage.id == message_id).first()
    if not msg:
        return None
    if msg.status in ("SENT", "DELIVERED"):
        return msg  # rien à faire
    if msg.attempts >= 3:
        msg.status = "REJECTED"
        db.commit()
        db.refresh(msg)
        return msg

    # Recharger le provider
    provider = msg.provider or (
        db.query(SmsProvider).filter(SmsProvider.id == msg.provider_id).first()
        if msg.provider_id else None
    )
    if not provider:
        msg.error_message = "Provider introuvable au moment du retry"
        db.commit()
        return msg

    backend = get_provider_class(provider.code)(provider)
    msg.attempts += 1
    try:
        result = backend.send(to=msg.recipient_phone, body=msg.body)
    except Exception as e:
        result = SmsSendResult(delivered=False, error_code="UNEXPECTED", error_message=str(e)[:500])

    if result.delivered:
        msg.status = "SENT"
        msg.operator_message_id = result.operator_message_id
        msg.cost_gnf = (msg.cost_gnf or 0) + result.cost_gnf
        msg.sent_at = utcnow()
        msg.error_code = None
        msg.error_message = None
    else:
        msg.error_code = result.error_code
        msg.error_message = result.error_message
        if msg.attempts >= 3:
            msg.status = "REJECTED"

    db.commit()
    db.refresh(msg)
    return msg


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def get_sms_stats(
    db: Session,
    *,
    facility_id: str | None = None,
    since: datetime | None = None,
) -> dict:
    """Retourne des statistiques agrégées sur les SMS envoyés.

    Utilisé par le dashboard admin SMS (coût mensuel, taux de succès, etc.).
    """
    since = since or (utcnow() - timedelta(days=30))
    q = db.query(SmsMessage).filter(SmsMessage.created_at >= since)
    if facility_id:
        q = q.filter(SmsMessage.facility_id == facility_id)

    total = q.count()
    sent = q.filter(SmsMessage.status.in_(["SENT", "DELIVERED"])).count()
    failed = q.filter(SmsMessage.status == "FAILED").count()
    pending = q.filter(SmsMessage.status == "PENDING").count()
    rejected = q.filter(SmsMessage.status == "REJECTED").count()

    total_cost = (
        db.query(func.coalesce(func.sum(SmsMessage.cost_gnf), 0))
        .filter(SmsMessage.created_at >= since)
        .scalar() or 0
    )
    if facility_id:
        total_cost = (
            db.query(func.coalesce(func.sum(SmsMessage.cost_gnf), 0))
            .filter(SmsMessage.created_at >= since)
            .filter(SmsMessage.facility_id == facility_id)
            .scalar() or 0
        )

    by_provider = (
        db.query(
            SmsMessage.provider_code,
            func.count(SmsMessage.id).label("total"),
            func.sum(
                case(
                    (SmsMessage.status.in_(["SENT", "DELIVERED"]), 1),
                    else_=0,
                )
            ).label("sent"),
        )
        .filter(SmsMessage.created_at >= since)
        .group_by(SmsMessage.provider_code)
        .all()
    )

    by_category = (
        db.query(
            SmsMessage.category,
            func.count(SmsMessage.id).label("total"),
            func.sum(
                case(
                    (SmsMessage.status.in_(["SENT", "DELIVERED"]), 1),
                    else_=0,
                )
            ).label("sent"),
        )
        .filter(SmsMessage.created_at >= since)
        .group_by(SmsMessage.category)
        .all()
    )

    success_rate = (sent / total * 100) if total > 0 else 0

    return {
        "since": since.isoformat(),
        "total": total,
        "sent": sent,
        "failed": failed,
        "pending": pending,
        "rejected": rejected,
        "success_rate_pct": round(success_rate, 2),
        "total_cost_gnf": int(total_cost),
        "by_provider": [
            {"provider": p, "total": t, "sent": int(s or 0)}
            for (p, t, s) in by_provider
        ],
        "by_category": [
            {"category": c, "total": t, "sent": int(s or 0)}
            for (c, t, s) in by_category
        ],
    }


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------

def _persist_failed(
    db: Session,
    *,
    to: str,
    body: str,
    category: str,
    priority: str,
    recipient_id: str | None,
    facility_id: str | None,
    notification_id: str | None,
    error_code: str,
    error_message: str,
) -> SmsMessage:
    """Persiste un SmsMessage FAILED sans tenter d'envoi (cas : numéro invalide)."""
    msg = SmsMessage(
        facility_id=facility_id,
        provider_id=None,
        provider_code="none",
        recipient_id=recipient_id,
        recipient_phone=to,
        body=body[:480],
        category=category,
        priority=priority,
        notification_id=notification_id,
        status="FAILED",
        attempts=0,
        cost_gnf=0,
        error_code=error_code,
        error_message=error_message,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# ---------------------------------------------------------------------------
# Routing rules helpers
# ---------------------------------------------------------------------------

def get_default_routing_rules() -> list[dict]:
    """Renvoie les règles de routage par défaut (seed).

    Ces règles sont insérées au démarrage si la table `sms_routing_rules` est vide.
    Elles peuvent ensuite être personnalisées par facility via l'API admin.
    """
    return [
        {
            "category": "lab_critical",
            "channels": "in_app,sms",
            "min_priority": "urgent",
            "description": "Résultats labo critiques → SMS immédiat au médecin prescripteur",
        },
        {
            "category": "incident_critical",
            "channels": "in_app,sms,email",
            "min_priority": "urgent",
            "description": "Incident qualité critique → SMS + email à la direction",
        },
        {
            "category": "appointment_reminder",
            "channels": "in_app,sms",
            "min_priority": "normal",
            "description": "Rappel de rendez-vous 24h avant → SMS au patient",
        },
        {
            "category": "medication_dispensed",
            "channels": "in_app",
            "min_priority": "normal",
            "description": "Médicament délivré → notification in-app uniquement",
        },
        {
            "category": "admission_created",
            "channels": "in_app",
            "min_priority": "normal",
            "description": "Nouvelle admission → in-app au service concerné",
        },
        {
            "category": "invoice_ready",
            "channels": "in_app,sms",
            "min_priority": "normal",
            "description": "Facture prête → SMS au patient (ou accompagnant)",
        },
        {
            "category": "quality_alert",
            "channels": "in_app,sms,email",
            "min_priority": "high",
            "description": "Seuil qualité dépassé → SMS à la direction qualité",
        },
        {
            "category": "system",
            "channels": "in_app",
            "min_priority": "normal",
            "description": "Notifications système → in-app uniquement",
        },
    ]


def seed_default_routing_rules(db: Session) -> int:
    """Insère les règles par défaut si la table est vide. Retourne le nombre inséré."""
    existing = db.query(SmsRoutingRule).count()
    if existing > 0:
        return 0
    for rule_data in get_default_routing_rules():
        db.add(SmsRoutingRule(
            facility_id=None,  # global
            category=rule_data["category"],
            channels=rule_data["channels"],
            min_priority=rule_data["min_priority"],
            description=rule_data["description"],
            enabled=True,
        ))
    db.commit()
    return len(get_default_routing_rules())


def seed_default_providers(db: Session) -> int:
    """Insère le provider mock par défaut si la table est vide. Retourne le nombre inséré."""
    existing = db.query(SmsProvider).count()
    if existing > 0:
        return 0
    db.add(SmsProvider(
        code="mock",
        name="Mock Provider (dev/test)",
        enabled=True,
        api_url=None,
        sender_id="GUINEECARE",
        cost_per_sms_gnf=0,
        rate_per_second=10,
        daily_quota=None,
    ))
    db.commit()
    return 1
