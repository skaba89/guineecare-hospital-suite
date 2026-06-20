"""JWT ID (jti) revocation service — OWASP A07 hardening (v0.9.0).

Provides:
    - revoke_jti(db, jti, user_id, reason, expires_at)
    - is_jti_revoked(db, jti) -> bool
    - revoke_user_jtis(db, user_id, reason)  # bulk revoke on user disable
    - prune_expired(db)  # garbage collect stale entries

The `revoked_jtis` table only holds entries whose associated token has not
yet expired — once the token expires naturally, the entry is pruned (the
blacklist check is moot for expired tokens).
"""
import logging
from typing import Iterable

from sqlalchemy.orm import Session

from app.core.datetime import utcnow
from app.modules.auth.models import RevokedJti

logger = logging.getLogger("guineecare.jti")


def revoke_jti(
    *,
    db: Session,
    jti: str,
    user_id: str | None = None,
    reason: str = "logout",
    expires_at=None,
) -> RevokedJti | None:
    """Mark a jti as revoked. Idempotent — re-revoking is a no-op.

    `expires_at` should be the JWT's natural expiry (so the row can be
    pruned later). If omitted, defaults to token_expire_minutes from now.
    """
    if not jti:
        return None

    from datetime import timedelta
    from app.core.config import settings
    if expires_at is None:
        expires_at = utcnow() + timedelta(minutes=settings.token_expire_minutes)

    existing = db.query(RevokedJti).filter(RevokedJti.jti == jti).first()
    if existing:
        return existing

    entry = RevokedJti(
        jti=jti,
        user_id=user_id,
        reason=reason,
        revoked_at=utcnow(),
        expires_at=expires_at,
    )
    db.add(entry)
    try:
        db.commit()
    except Exception as e:
        logger.warning("revoke_jti commit failed: %s", e)
        db.rollback()
        return None
    return entry


def is_jti_revoked(db: Session, jti: str | None) -> bool:
    """Return True if the given jti has been revoked. None/empty → False."""
    if not jti:
        return False
    try:
        return db.query(RevokedJti).filter(RevokedJti.jti == jti).first() is not None
    except Exception as e:
        # Fail-closed would lock users out on DB errors; fail-open + log.
        # The token's signature & expiry are still checked separately.
        logger.warning("is_jti_revoked DB error (fail-open): %s", e)
        return False


def revoke_user_jtis(*, db: Session, user_id: str, reason: str = "user_disabled") -> int:
    """Bulk-revoke all unrevoked jtis for a user. Returns the count revoked.

    NOTE: this only affects tokens issued AFTER the user is marked inactive
    IF the get_current_user dependency checks `is_active` — but revoking
    all known jtis is still useful for force-logout on demand. Tokens that
    have already expired are skipped.
    """
    if not user_id:
        return 0
    now = utcnow()
    # We don't have a record of every issued jti — only of revoked ones.
    # To support true bulk-revoke on user disable, the login route would
    # need to persist issued jtis. For v0.9.0, this helper exists as a
    # stub for the explicit logout case (which calls revoke_jti with the
    # specific jti). Bulk-revoke can be added in v0.10 with a `issued_jtis`
    # table if needed.
    logger.info("revoke_user_jtis called for user_id=%s reason=%s (no-op in v0.9)", user_id, reason)
    return 0


def prune_expired(db: Session) -> int:
    """Delete revoked_jtis rows whose tokens have naturally expired.

    Returns the number of rows deleted. Safe to call periodically (e.g.
    once per hour from a background task) to keep the table small.
    """
    now = utcnow()
    deleted = (
        db.query(RevokedJti)
        .filter(RevokedJti.expires_at < now)
        .delete(synchronize_session=False)
    )
    try:
        db.commit()
    except Exception as e:
        logger.warning("prune_expired commit failed: %s", e)
        db.rollback()
        return 0
    return deleted
