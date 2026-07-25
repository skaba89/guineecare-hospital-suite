"""Audit log service — append-only journal of all mutations.

Usage from any route:
    from app.modules.audit.service import audit_log

    @router.post("/patients")
    def create_patient(..., current_user=Depends(get_current_user), db=Depends(get_db)):
        patient = ...
        db.add(patient); db.commit()
        audit_log(
            db=db,
            user=current_user,
            action="patient.create",
            resource_type="patient",
            resource_id=patient.id,
            request=request,
            status_code=201,
            payload={"after": patient.to_dict()},
        )
        return patient
"""
import json
import logging
from typing import Any
from uuid import uuid4

from fastapi import Request
from sqlalchemy.orm import Session

from app.core.datetime import utcnow
from app.modules.auth.models import AuditLog

logger = logging.getLogger("guineecare.audit")


def _extract_request_meta(request: Request | None) -> tuple[str | None, str | None, str | None, str | None]:
    if request is None:
        return None, None, None, None
    # SECURITY (A05-001 — v0.9.0): only trust X-Forwarded-For when the
    # direct peer is a configured TRUSTED_PROXY. Prevents IP spoofing.
    from app.core.config import is_ip_trusted, settings

    remote_addr = request.client.host if request.client else None
    if is_ip_trusted(remote_addr, settings.trusted_proxies):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = remote_addr
    else:
        ip = remote_addr
    ua = request.headers.get("user-agent")
    if ua and len(ua) > 512:
        ua = ua[:512]
    method = request.method
    path = request.url.path if hasattr(request, "url") else None
    if path and len(path) > 512:
        path = path[:512]
    return ip, ua, method, path


def _serialize_payload(payload: Any) -> str | None:
    if payload is None:
        return None
    try:
        return json.dumps(payload, default=str, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.warning("audit_log payload serialization failed: %s", e)
        return json.dumps({"_error": "serialization_failed", "repr": repr(payload)}, ensure_ascii=False)


def audit_log(
    *,
    db: Session,
    action: str,
    user: Any = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    request: Request | None = None,
    status_code: int | None = None,
    payload: dict | None = None,
    facility_id: str | None = None,
) -> AuditLog:
    """Persist an audit log entry. Never raises — failures are logged but do not
    break the request flow.

    Args:
        db: SQLAlchemy session (the same as the route's session)
        action: short action code, e.g. "patient.create", "auth.login"
        user: User object (or any object with .id and .facility_id)
        resource_type: e.g. "patient", "user", "admission"
        resource_id: UUID of the affected resource
        request: FastAPI Request (for IP/UA/method/path)
        status_code: HTTP status code returned to the client
        payload: dict with before/after diff or other context
        facility_id: optional facility override (defaults to user.facility_id)

    Returns:
        The created AuditLog row (already committed)
    """
    try:
        ip, ua, method, path = _extract_request_meta(request)
        user_id = getattr(user, "id", None) if user else None
        resolved_facility = facility_id or getattr(user, "facility_id", None)

        entry = AuditLog(
            id=str(uuid4()),
            created_at=utcnow(),
            user_id=user_id,
            facility_id=resolved_facility,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            http_method=method,
            http_path=path,
            status_code=status_code,
            ip_address=ip,
            user_agent=ua,
            payload=_serialize_payload(payload),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry
    except Exception as e:
        # Audit log must NEVER break the main request flow
        logger.error("audit_log failed: %s (action=%s, resource=%s/%s)", e, action, resource_type, resource_id)
        try:
            db.rollback()
        except Exception:
            pass
        return None  # type: ignore[return-value]
