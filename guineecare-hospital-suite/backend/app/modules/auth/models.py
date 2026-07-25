"""Models for refresh tokens, audit logs, and JWT jti blacklist."""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.datetime import utcnow
from app.db.base import Base


class RefreshToken(Base):
    """Long-lived refresh token for JWT rotation.

    The token itself is never stored in clear — only its SHA-256 hash.
    To validate a refresh token presented by the client:
        1. Hash the presented token
        2. Look up by `token_hash`
        3. Check `revoked_at IS NULL` AND `expires_at > now()`
        4. On use: rotate (revoke + issue a new one, set `replaced_by_id`)
    """

    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    token_hash = Column(String(128), nullable=False, unique=True, index=True)
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    created_ip = Column(String(45), nullable=True)
    created_user_agent = Column(String(512), nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    replaced_by_id = Column(
        String(36), ForeignKey("refresh_tokens.id"), nullable=True
    )

    def is_valid(self) -> bool:
        return self.revoked_at is None and self.expires_at > utcnow()


class AuditLog(Base):
    """Append-only journal of every mutation in the system.

    Rows are written by the `audit` decorator/service. They are never updated
    or deleted — only inserted. Read access is restricted to SUPER_ADMIN and
    ADMIN (via the /audit API module).
    """

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=True, index=True)
    resource_id = Column(String(36), nullable=True, index=True)
    http_method = Column(String(10), nullable=True)
    http_path = Column(String(512), nullable=True)
    status_code = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    # JSON-encoded payload (e.g. before/after diff for mutations)
    payload = Column(Text, nullable=True)


class RevokedJti(Base):
    """JWT ID blacklist — tracks access-token jtis that have been explicitly
    revoked before their natural expiry.

    Use cases (OWASP A07 — v0.9.0):
        - User clicks "logout": their current access_token's jti is revoked,
          so even if the token was leaked, it becomes immediately unusable.
        - Admin disables a user: all their jtis can be bulk-revoked.
        - Suspected token theft: admin can revoke a specific jti.

    Rows are pruned automatically — the table only holds entries whose
    associated token has not yet expired (expires_at > now).
    """

    __tablename__ = "revoked_jtis"

    jti = Column(String(64), primary_key=True, nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    reason = Column(String(64), nullable=True)
    revoked_at = Column(DateTime, default=utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


# v2.8.4 — Registre des violations de données (RGPD Article 33)
class DataBreach(Base):
    __tablename__ = "data_breaches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey('facilities.id'), nullable=True, index=True)
    reported_by = Column(String(36), ForeignKey('users.id'), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(30), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(30), default="OPEN", nullable=False)  # OPEN, INVESTIGATING, NOTIFIED, RESOLVED, CLOSED
    affected_patients_count = Column(Integer, default=0, nullable=False)
    notified_authority = Column(Boolean, default=False, nullable=False)
    notified_at = Column(DateTime, nullable=True)
    authority_name = Column(String(255), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=utcnow, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow, nullable=False)
