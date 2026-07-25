"""Routes SMS v1.4.0 — administration des providers, règles de routage, envoi et historique.

Sous-module monté sous `/api/v1/notifications/sms/*`.

Permissions RBAC requises :
- `notification.send` : envoi manuel (SUPER_ADMIN/ADMIN).
- `notification.manage` : CRUD providers + règles (SUPER_ADMIN/ADMIN).
- `notification.read` : consultation historique (tout rôle authentifié).
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.core.tenant import enforce_facility_access, tenant_query
from app.db.session import get_db
from app.modules.audit.service import audit_log
from app.modules.notifications.sms_models import (
    SmsMessage,
    SmsProvider,
    SmsRoutingRule,
)
from app.modules.notifications.sms_provider import (
    encrypt_credential,
    get_provider_class,
    list_supported_providers,
)
from app.modules.notifications.sms_schemas import (
    SmsMessageListResponse,
    SmsMessageRead,
    SmsProviderCreate,
    SmsProviderListResponse,
    SmsProviderRead,
    SmsProviderTestRequest,
    SmsProviderTestResponse,
    SmsProviderUpdate,
    SmsRoutingRuleCreate,
    SmsRoutingRuleListResponse,
    SmsRoutingRuleRead,
    SmsRoutingRuleUpdate,
    SmsSendRequest,
    SmsStatsResponse,
)
from app.modules.notifications.sms_service import (
    get_sms_stats,
    retry_failed_sms,
    seed_default_providers,
    seed_default_routing_rules,
    send_sms,
)
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/notifications/sms", tags=["notifications-sms"])


# ── Providers ───────────────────────────────────────────────────────────────

@router.get("/providers", response_model=SmsProviderListResponse)
def list_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.read")),
):
    """Liste tous les providers SMS configurés.

    Sécurise les credentials : seuls les flags `has_api_key/has_api_secret` sont retournés.
    """
    # Seed lazy si la table est vide (dev convenience)
    seed_default_providers(db)
    rows = db.query(SmsProvider).order_by(SmsProvider.code).all()
    return SmsProviderListResponse(
        data=[SmsProviderRead.from_model(r) for r in rows],
        total=len(rows),
    )


@router.get("/providers/supported")
def list_supported(current_user: User = Depends(require_permission("notification.read"))):
    """Liste les codes de providers supportés par l'application (catalogue statique)."""
    return {"data": list_supported_providers()}


@router.post("/providers", response_model=SmsProviderRead, status_code=201)
def create_provider(
    payload: SmsProviderCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.manage")),
):
    """Crée un provider SMS. Les credentials sont chiffrés avant stockage."""
    existing = db.query(SmsProvider).filter(SmsProvider.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Provider {payload.code} déjà configuré")

    row = SmsProvider(
        code=payload.code,
        name=payload.name,
        enabled=payload.enabled,
        api_url=payload.api_url,
        api_key_encrypted=encrypt_credential(payload.api_key),
        api_secret_encrypted=encrypt_credential(payload.api_secret),
        sender_id=payload.sender_id,
        cost_per_sms_gnf=payload.cost_per_sms_gnf,
        rate_per_second=payload.rate_per_second,
        daily_quota=payload.daily_quota,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        user=current_user,
        action="sms.provider.create",
        resource_type="sms_provider",
        resource_id=row.id,
        request=request,
        status_code=201,
        payload={"code": row.code, "name": row.name},
    )
    return SmsProviderRead.from_model(row)


@router.patch("/providers/{provider_id}", response_model=SmsProviderRead)
def update_provider(
    provider_id: str,
    payload: SmsProviderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.manage")),
):
    """Met à jour un provider SMS. Seuls les champs fournis sont écrasés."""
    row = db.query(SmsProvider).filter(SmsProvider.id == provider_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Provider introuvable")

    if payload.name is not None:
        row.name = payload.name
    if payload.enabled is not None:
        row.enabled = payload.enabled
    if payload.api_url is not None:
        row.api_url = payload.api_url
    if payload.api_key is not None:
        row.api_key_encrypted = encrypt_credential(payload.api_key)
    if payload.api_secret is not None:
        row.api_secret_encrypted = encrypt_credential(payload.api_secret)
    if payload.sender_id is not None:
        row.sender_id = payload.sender_id
    if payload.cost_per_sms_gnf is not None:
        row.cost_per_sms_gnf = payload.cost_per_sms_gnf
    if payload.rate_per_second is not None:
        row.rate_per_second = payload.rate_per_second
    if payload.daily_quota is not None:
        row.daily_quota = payload.daily_quota

    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        user=current_user,
        action="sms.provider.update",
        resource_type="sms_provider",
        resource_id=row.id,
        request=request,
        status_code=200,
        payload={"code": row.code, "updated_fields": list(payload.model_dump(exclude_unset=True).keys())},
    )
    return SmsProviderRead.from_model(row)


@router.delete("/providers/{provider_id}", status_code=204)
def delete_provider(
    provider_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.manage")),
):
    """Supprime un provider SMS. Les SmsMessages historiques sont conservés (provider_id nullifié)."""
    row = db.query(SmsProvider).filter(SmsProvider.id == provider_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Provider introuvable")
    if row.code == "mock":
        raise HTTPException(status_code=400, detail="Le provider mock ne peut pas être supprimé")

    # Détacher les messages historiques
    db.query(SmsMessage).filter(SmsMessage.provider_id == provider_id).update(
        {"provider_id": None}
    )
    code_snapshot = row.code
    db.delete(row)
    db.commit()

    audit_log(
        db=db,
        user=current_user,
        action="sms.provider.delete",
        resource_type="sms_provider",
        resource_id=provider_id,
        request=request,
        status_code=204,
        payload={"code": code_snapshot},
    )
    return None


@router.post("/providers/{provider_id}/test", response_model=SmsProviderTestResponse)
def test_provider(
    provider_id: str,
    payload: SmsProviderTestRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.manage")),
):
    """Teste un provider en envoyant un SMS à un numéro de test.

    Coût réel si le provider est un opérateur (Orange/MTN/Moov) — à utiliser
    avec parcimonie.
    """
    row = db.query(SmsProvider).filter(SmsProvider.id == provider_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Provider introuvable")

    body = payload.body or "Test GuinéeCare v1.4 — veuillez ignorer"
    msg = send_sms(
        db=db,
        to=payload.to,
        body=body,
        category="provider_test",
        priority="low",
        facility_id=current_user.facility_id,
        provider_id=provider_id,
    )

    audit_log(
        db=db,
        user=current_user,
        action="sms.provider.test",
        resource_type="sms_provider",
        resource_id=provider_id,
        request=request,
        status_code=200,
        payload={"to": payload.to, "message_id": msg.id, "status": msg.status},
    )

    return SmsProviderTestResponse(
        success=msg.status in ("SENT", "DELIVERED"),
        message_id=msg.id,
        error_code=msg.error_code,
        error_message=msg.error_message,
        cost_gnf=msg.cost_gnf or 0,
    )


# ── Routing Rules ───────────────────────────────────────────────────────────

@router.get("/rules", response_model=SmsRoutingRuleListResponse)
def list_rules(
    facility_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.read")),
):
    """Liste les règles de routage SMS.

    SUPER_ADMIN voit toutes les règles. ADMIN ne voit que celles de sa facility
    + les règles globales.
    """
    # Seed lazy si la table est vide
    seed_default_routing_rules(db)

    query = db.query(SmsRoutingRule)
    if current_user.role != "SUPER_ADMIN":
        # ADMIN : règles globales + règles de sa facility
        query = query.filter(
            (SmsRoutingRule.facility_id.is_(None)) |
            (SmsRoutingRule.facility_id == current_user.facility_id)
        )
    if facility_id:
        enforce_facility_access(current_user, facility_id)
        query = query.filter(SmsRoutingRule.facility_id == facility_id)

    rows = query.order_by(SmsRoutingRule.category).all()
    return SmsRoutingRuleListResponse(
        data=[SmsRoutingRuleRead.from_model(r) for r in rows],
        total=len(rows),
    )


@router.post("/rules", response_model=SmsRoutingRuleRead, status_code=201)
def create_rule(
    payload: SmsRoutingRuleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.manage")),
):
    """Crée une règle de routage SMS."""
    if payload.facility_id:
        enforce_facility_access(current_user, payload.facility_id)

    # Dédoublonnage : une seule règle enabled par (facility_id, category)
    base_q = (
        db.query(SmsRoutingRule)
        .filter(SmsRoutingRule.category == payload.category)
        .filter(SmsRoutingRule.enabled.is_(True))
    )
    if payload.facility_id:
        existing = base_q.filter(SmsRoutingRule.facility_id == payload.facility_id).first()
    else:
        existing = base_q.filter(SmsRoutingRule.facility_id.is_(None)).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Une règle enabled existe déjà pour la catégorie {payload.category}",
        )

    row = SmsRoutingRule(
        facility_id=payload.facility_id,
        category=payload.category,
        channels=",".join(payload.channels) if payload.channels else "in_app",
        min_priority=payload.min_priority,
        preferred_provider_id=payload.preferred_provider_id,
        enabled=payload.enabled,
        description=payload.description,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        user=current_user,
        action="sms.rule.create",
        resource_type="sms_routing_rule",
        resource_id=row.id,
        request=request,
        status_code=201,
        payload={"category": row.category, "facility_id": row.facility_id},
    )
    return SmsRoutingRuleRead.from_model(row)


@router.patch("/rules/{rule_id}", response_model=SmsRoutingRuleRead)
def update_rule(
    rule_id: str,
    payload: SmsRoutingRuleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.manage")),
):
    """Met à jour une règle de routage SMS."""
    row = db.query(SmsRoutingRule).filter(SmsRoutingRule.id == rule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Règle introuvable")
    enforce_facility_access(current_user, row.facility_id)

    if payload.channels is not None:
        row.channels = ",".join(payload.channels) if payload.channels else "in_app"
    if payload.min_priority is not None:
        row.min_priority = payload.min_priority
    if payload.preferred_provider_id is not None:
        row.preferred_provider_id = payload.preferred_provider_id
    if payload.enabled is not None:
        row.enabled = payload.enabled
    if payload.description is not None:
        row.description = payload.description

    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        user=current_user,
        action="sms.rule.update",
        resource_type="sms_routing_rule",
        resource_id=row.id,
        request=request,
        status_code=200,
        payload={"updated_fields": list(payload.model_dump(exclude_unset=True).keys())},
    )
    return SmsRoutingRuleRead.from_model(row)


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(
    rule_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.manage")),
):
    """Supprime une règle de routage SMS."""
    row = db.query(SmsRoutingRule).filter(SmsRoutingRule.id == rule_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Règle introuvable")
    enforce_facility_access(current_user, row.facility_id)
    cat_snapshot = row.category
    db.delete(row)
    db.commit()

    audit_log(
        db=db,
        user=current_user,
        action="sms.rule.delete",
        resource_type="sms_routing_rule",
        resource_id=rule_id,
        request=request,
        status_code=204,
        payload={"category": cat_snapshot},
    )
    return None


# ── Envoi manuel + Historique + Stats ───────────────────────────────────────

@router.post("/send", response_model=SmsMessageRead, status_code=201)
def admin_send_sms(
    payload: SmsSendRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.send")),
):
    """Envoie un SMS manuellement (admin). Coût réel selon le provider sélectionné.

    Pour les envois automatiques liés à une notification, utiliser le service
    `send_sms()` directement depuis la route métier (lab result, etc.).
    """
    facility_id = payload.facility_id or current_user.facility_id
    if payload.facility_id:
        enforce_facility_access(current_user, payload.facility_id)

    msg = send_sms(
        db=db,
        to=payload.to,
        body=payload.body,
        category=payload.category,
        priority=payload.priority,
        recipient_id=payload.recipient_id,
        facility_id=facility_id,
        provider_id=payload.provider_id,
    )

    audit_log(
        db=db,
        user=current_user,
        action="sms.send_manual",
        resource_type="sms_message",
        resource_id=msg.id,
        request=request,
        status_code=201,
        payload={"to": payload.to, "category": payload.category, "status": msg.status},
    )
    return SmsMessageRead.model_validate(msg)


@router.post("/messages/{message_id}/retry", response_model=SmsMessageRead)
def retry_message(
    message_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.send")),
):
    """Retente l'envoi d'un SMS échoué. Maximum 3 tentatives cumulées."""
    msg = retry_failed_sms(db, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="SMS introuvable")
    enforce_facility_access(current_user, msg.facility_id)

    audit_log(
        db=db,
        user=current_user,
        action="sms.retry",
        resource_type="sms_message",
        resource_id=msg.id,
        request=request,
        status_code=200,
        payload={"attempts": msg.attempts, "status": msg.status},
    )
    return SmsMessageRead.model_validate(msg)


@router.get("/messages", response_model=SmsMessageListResponse)
def list_messages(
    status: str | None = None,
    provider_code: str | None = None,
    category: str | None = None,
    recipient_phone: str | None = None,
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.read")),
):
    """Historique paginé des SMS envoyés. Filtrage multi-tenant automatique."""
    query = tenant_query(db, SmsMessage, current_user)
    if status:
        query = query.filter(SmsMessage.status == status)
    if provider_code:
        query = query.filter(SmsMessage.provider_code == provider_code)
    if category:
        query = query.filter(SmsMessage.category == category)
    if recipient_phone:
        query = query.filter(SmsMessage.recipient_phone == recipient_phone)
    query = query.order_by(SmsMessage.created_at.desc())

    result = paginate(query, pagination)
    return SmsMessageListResponse(
        data=[SmsMessageRead.model_validate(r) for r in result["data"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/stats", response_model=SmsStatsResponse)
def get_stats(
    days: int = Query(30, ge=1, le=365, description="Période en jours (1-365)"),
    facility_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.read")),
):
    """Statistiques agrégées des SMS sur la période donnée.

    Multi-tenant : SUPER_ADMIN voit tous les établissements, les autres rôles
    ne voient que leur facility.
    """
    if current_user.role != "SUPER_ADMIN":
        facility_id = current_user.facility_id
    elif facility_id:
        enforce_facility_access(current_user, facility_id)

    since = datetime.utcnow() - timedelta(days=days)
    stats = get_sms_stats(db, facility_id=facility_id, since=since)
    return SmsStatsResponse(**stats)
