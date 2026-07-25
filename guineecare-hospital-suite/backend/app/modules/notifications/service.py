"""Notifications service — sends notifications through pluggable channel providers.

Default provider is ConsoleChannel (logs to stdout) — safe for dev/test.
For production, set env vars to enable SMTP email + Twilio SMS providers.

Usage from any route:
    from app.modules.notifications.service import notify

    notify(
        db=db,
        recipient_id=patient.primary_doctor_id,
        title="Nouveau résultat de laboratoire",
        body=f"Résultat disponible pour {patient.full_name}",
        category="lab_result",
        priority="normal",
        action_url=f"/lab/orders/{order.id}",
        resource_type="lab_order",
        resource_id=order.id,
        sender_id=current_user.id,
        facility_id=current_user.facility_id,
    )
"""
import logging
import os
from datetime import datetime
from typing import Iterable

from sqlalchemy.orm import Session

from app.modules.notifications.models import Notification

logger = logging.getLogger("guineecare.notifications")


# ---------------------------------------------------------------------------
# Channel providers
# ---------------------------------------------------------------------------

class ChannelResult:
    """Outcome of a delivery attempt on one channel."""
    def __init__(self, delivered: bool, error: str | None = None):
        self.delivered = delivered
        self.error = error


class ConsoleChannel:
    """Always-succeeds channel that just logs to stdout. Default for dev/test."""
    name = "in_app"

    def send(self, *, recipient_id: str, title: str, body: str | None, **kwargs) -> ChannelResult:
        logger.info(
            "[notification:in_app] to=%s title=%r body=%r",
            recipient_id, title, (body or "")[:120],
        )
        return ChannelResult(delivered=True)


class EmailChannel:
    """SMTP email channel — enabled when SMTP_HOST is set.

    Uses smtplib directly to avoid extra dependencies. Best-effort: failures are
    recorded on the notification row but never raise to the caller.
    """
    name = "email"

    def __init__(self):
        self.host = os.environ.get("SMTP_HOST")
        self.port = int(os.environ.get("SMTP_PORT", "587"))
        self.user = os.environ.get("SMTP_USER")
        self.password = os.environ.get("SMTP_PASSWORD")
        self.from_addr = os.environ.get("SMTP_FROM", "no-reply@guineecare.gn")
        self.use_tls = os.environ.get("SMTP_USE_TLS", "true").lower() in {"1", "true", "yes"}

    @property
    def enabled(self) -> bool:
        return bool(self.host and self.user and self.password)

    def send(self, *, recipient_email: str | None, title: str, body: str | None, **kwargs) -> ChannelResult:
        if not self.enabled:
            return ChannelResult(delivered=False, error="SMTP not configured")
        if not recipient_email:
            return ChannelResult(delivered=False, error="recipient has no email")

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[GuinéeCare] {title}"
            msg["From"] = self.from_addr
            msg["To"] = recipient_email
            msg.attach(MIMEText(body or "", "plain", "utf-8"))

            with smtplib.SMTP(self.host, self.port, timeout=10) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.sendmail(self.from_addr, [recipient_email], msg.as_string())

            return ChannelResult(delivered=True)
        except Exception as e:
            return ChannelResult(delivered=False, error=f"smtp_error: {e}")


class SmsChannel:
    """SMS channel via Twilio — enabled when TWILIO_ACCOUNT_SID is set.

    Best-effort: failures recorded on the notification row but never raise.
    """
    name = "sms"

    def __init__(self):
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.from_number = os.environ.get("TWILIO_FROM_NUMBER")

    @property
    def enabled(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number)

    def send(self, *, recipient_phone: str | None, title: str, body: str | None, **kwargs) -> ChannelResult:
        if not self.enabled:
            return ChannelResult(delivered=False, error="Twilio not configured")
        if not recipient_phone:
            return ChannelResult(delivered=False, error="recipient has no phone")

        try:
            # Lazy import — Twilio SDK is optional
            from twilio.rest import Client  # type: ignore
            client = Client(self.account_sid, self.auth_token)
            msg = client.messages.create(
                body=f"{title}\n\n{body or ''}"[:480],
                from_=self.from_number,
                to=recipient_phone,
            )
            return ChannelResult(delivered=bool(getattr(msg, "sid", None)))
        except ImportError:
            return ChannelResult(delivered=False, error="twilio package not installed")
        except Exception as e:
            return ChannelResult(delivered=False, error=f"twilio_error: {e}")


# Singleton channel instances (constructed once at module load)
_console = ConsoleChannel()
_email = EmailChannel()
_sms = SmsChannel()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def notify(
    db: Session,
    *,
    recipient_id: str,
    title: str,
    category: str,
    body: str | None = None,
    action_url: str | None = None,
    priority: str = "normal",
    channels: Iterable[str] = ("in_app",),
    sender_id: str | None = None,
    facility_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    recipient_email: str | None = None,
    recipient_phone: str | None = None,
) -> Notification:
    """Create and persist a notification, then attempt delivery on requested channels.

    This function NEVER raises — failures are logged and recorded on the row.
    The in-app channel is always attempted even if not in `channels`, so the
    notification is always visible in the user's notification center.
    """
    # Ensure 'in_app' is always in the channels list
    channels_list = list(dict.fromkeys(["in_app", *channels]))
    channels_csv = ",".join(channels_list)

    notification = Notification(
        recipient_id=recipient_id,
        facility_id=facility_id,
        sender_id=sender_id,
        category=category,
        priority=priority,
        title=title,
        body=body,
        action_url=action_url,
        channels=channels_csv,
        in_app_delivered=False,
        email_delivered=False,
        sms_delivered=False,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    errors: list[str] = []

    # in_app — always delivered (the row itself IS the in-app notification)
    if "in_app" in channels_list:
        try:
            r = _console.send(
                recipient_id=recipient_id,
                title=title,
                body=body,
            )
            notification.in_app_delivered = r.delivered
            if not r.delivered and r.error:
                errors.append(f"in_app: {r.error}")
        except Exception as e:
            errors.append(f"in_app: {e}")
        else:
            notification.in_app_delivered = True

    if "email" in channels_list:
        try:
            r = _email.send(
                recipient_email=recipient_email,
                title=title,
                body=body,
            )
            notification.email_delivered = r.delivered
            if not r.delivered and r.error:
                errors.append(f"email: {r.error}")
        except Exception as e:
            errors.append(f"email: {e}")

    if "sms" in channels_list:
        try:
            r = _sms.send(
                recipient_phone=recipient_phone,
                title=title,
                body=body,
            )
            notification.sms_delivered = r.delivered
            if not r.delivered and r.error:
                errors.append(f"sms: {r.error}")
        except Exception as e:
            errors.append(f"sms: {e}")

    if errors:
        notification.delivery_error = "; ".join(errors)
        logger.warning("notification %s partial delivery: %s", notification.id, notification.delivery_error)

    db.commit()
    db.refresh(notification)
    return notification


def mark_read(db: Session, notification_id: str, recipient_id: str) -> Notification | None:
    """Mark a notification as read. Only the recipient can do this."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .filter(Notification.recipient_id == recipient_id)
        .first()
    )
    if notif is None:
        return None
    if notif.read_at is None:
        notif.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_read(db: Session, recipient_id: str) -> int:
    """Mark all of a user's notifications as read. Returns the count updated."""
    rows = (
        db.query(Notification)
        .filter(Notification.recipient_id == recipient_id)
        .filter(Notification.read_at.is_(None))
        .all()
    )
    now = datetime.utcnow()
    for r in rows:
        r.read_at = now
    db.commit()
    return len(rows)


def dismiss(db: Session, notification_id: str, recipient_id: str) -> Notification | None:
    """Dismiss (soft-delete) a notification. Only the recipient can do this."""
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id)
        .filter(Notification.recipient_id == recipient_id)
        .first()
    )
    if notif is None:
        return None
    if notif.dismissed_at is None:
        notif.dismissed_at = datetime.utcnow()
        db.commit()
        db.refresh(notif)
    return notif
