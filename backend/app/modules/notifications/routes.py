"""Notification endpoints — list, read, dismiss, and admin send."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.tenant import enforce_facility_access, tenant_query
from app.db.session import get_db
from app.modules.audit.service import audit_log
from app.modules.auth.dependencies import get_current_user
from app.modules.notifications.models import Notification
from app.modules.notifications.schemas import (
    NotificationListResponse,
    NotificationRead,
    NotificationSend,
    UnreadCountResponse,
)
from app.modules.notifications.service import dismiss, mark_all_read, mark_read, notify
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _paginated_response(query, page: int, page_size: int, unread_count: int) -> NotificationListResponse:
    total = query.count()
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    rows = (
        query.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return NotificationListResponse(
        data=[NotificationRead.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        unread_count=unread_count,
    )


@router.get("", response_model=NotificationListResponse)
def list_my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    category: str | None = Query(None),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the current user's notifications (paginated, with unread count)."""
    q = db.query(Notification).filter(Notification.recipient_id == current_user.id)
    if unread_only:
        q = q.filter(Notification.read_at.is_(None))
    if category:
        q = q.filter(Notification.category == category)
    # Hide dismissed notifications
    q = q.filter(Notification.dismissed_at.is_(None))

    unread_q = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .filter(Notification.dismissed_at.is_(None))
        .filter(Notification.read_at.is_(None))
    )
    unread_count = unread_q.count()

    return _paginated_response(q, page, page_size, unread_count)


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the count of unread notifications for the current user (for header badge)."""
    count = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id)
        .filter(Notification.dismissed_at.is_(None))
        .filter(Notification.read_at.is_(None))
        .count()
    )
    return UnreadCountResponse(unread_count=count)


@router.post("/mark-all-read", response_model=UnreadCountResponse)
def mark_all_my_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark all of the current user's notifications as read."""
    updated = mark_all_read(db, current_user.id)
    return UnreadCountResponse(unread_count=0)  # all read


@router.patch("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a single notification as read. Only the recipient can do this."""
    notif = mark_read(db, notification_id, current_user.id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    return NotificationRead.model_validate(notif)


@router.delete("/{notification_id}", response_model=NotificationRead)
def dismiss_notification(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Dismiss a notification (soft-delete). Only the recipient can do this."""
    notif = dismiss(db, notification_id, current_user.id)
    if notif is None:
        raise HTTPException(status_code=404, detail="Notification introuvable")
    return NotificationRead.model_validate(notif)


@router.post("/send", response_model=NotificationRead, status_code=201)
def admin_send_notification(
    payload: NotificationSend,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("notification.send")),
):
    """Admin-only: send a notification to a specific user.

    Requires the `notification.send` permission (SUPER_ADMIN/ADMIN bypass).
    SECURITY (A01-003): facility-scoped ADMINs can only send to users in
    their own facility. SUPER_ADMIN can send to anyone.
    """
    recipient = db.query(User).filter(User.id == payload.recipient_id).first()
    if recipient is None:
        raise HTTPException(status_code=404, detail="Destinataire introuvable")

    # Enforce tenant access on the recipient — prevents cross-facility phishing
    enforce_facility_access(current_user, recipient.facility_id)

    notif = notify(
        db=db,
        recipient_id=recipient.id,
        recipient_email=recipient.email,
        recipient_phone=getattr(recipient, "phone", None),
        title=payload.title,
        body=payload.body,
        category=payload.category,
        priority=payload.priority,
        action_url=payload.action_url,
        channels=payload.channels,
        sender_id=current_user.id,
        facility_id=current_user.facility_id or recipient.facility_id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
    )

    audit_log(
        db=db,
        user=current_user,
        action="notification.send",
        resource_type="notification",
        resource_id=notif.id,
        request=request,
        status_code=201,
        payload={"recipient_id": recipient.id, "category": payload.category, "title": payload.title},
    )

    return NotificationRead.model_validate(notif)
