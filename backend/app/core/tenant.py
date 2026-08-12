"""
Multi-tenant isolation for GuinéeCare.

This module keeps the existing SQLAlchemy facility filters as defence in depth
and also manages the PostgreSQL transaction-local context consumed by database
Row-Level Security (RLS) policies.

RLS context keys:
- app.current_facility_id: facility UUID for a facility-scoped user
- app.is_super_admin: explicit cross-tenant flag ("true" / "false")

The database policies are fail-closed: when these settings are absent or empty,
protected rows are not visible and cannot be written.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Query, Session

from app.modules.users.models import User


# Roles that have cross-tenant visibility (can see ALL facilities).
CROSS_TENANT_ROLES = {"SUPER_ADMIN"}

# Session.info keys are intentionally private to the backend and are never
# populated directly from request parameters.
_RLS_FACILITY_INFO_KEY = "guineecare_rls_facility_id"
_RLS_SUPER_ADMIN_INFO_KEY = "guineecare_rls_is_super_admin"


def _is_postgresql(bind: Any) -> bool:
    """Return True when a SQLAlchemy Engine/Connection uses PostgreSQL."""
    dialect = getattr(bind, "dialect", None)
    return getattr(dialect, "name", None) == "postgresql"


def _apply_postgres_rls_context(
    connection: Connection,
    facility_id: str | None,
    is_super_admin: bool,
) -> None:
    """Apply the RLS context to the current PostgreSQL transaction.

    `set_config(..., true)` makes both settings transaction-local. This is
    important with pooled connections: tenant state must never leak from one
    request/transaction to another.
    """
    if not _is_postgresql(connection):
        return

    connection.execute(
        text("SELECT set_config('app.current_facility_id', :facility_id, true)"),
        {"facility_id": str(facility_id) if facility_id else ""},
    )
    connection.execute(
        text("SELECT set_config('app.is_super_admin', :is_super_admin, true)"),
        {"is_super_admin": "true" if is_super_admin else "false"},
    )


def apply_tenant_context_after_begin(
    session: Session,
    transaction: Any,
    connection: Connection,
) -> None:
    """SQLAlchemy ``after_begin`` listener used by ``SessionLocal``.

    A commit ends PostgreSQL transaction-local settings. Reapplying the values
    on every new transaction keeps RLS effective even for routes/services that
    call ``db.commit()`` multiple times in one request.
    """
    if not _is_postgresql(connection):
        return

    _apply_postgres_rls_context(
        connection,
        session.info.get(_RLS_FACILITY_INFO_KEY),
        bool(session.info.get(_RLS_SUPER_ADMIN_INFO_KEY, False)),
    )


def bind_tenant_context(db: Session, current_user: User) -> None:
    """Bind the authenticated user's trusted database identity to the session.

    The context is derived from the freshly loaded ``User`` row, not from
    arbitrary request input. If the session already has an active transaction
    (which is normally the case after loading the user), the settings are
    applied immediately; subsequent transactions are handled by the
    ``after_begin`` listener.
    """
    is_super_admin = current_user.role in CROSS_TENANT_ROLES
    facility_id = None if is_super_admin else current_user.facility_id

    db.info[_RLS_FACILITY_INFO_KEY] = facility_id
    db.info[_RLS_SUPER_ADMIN_INFO_KEY] = is_super_admin

    bind = db.get_bind()
    if not _is_postgresql(bind):
        return

    # get_current_user() has normally already issued a SELECT, therefore an
    # active transaction exists. Apply immediately so the remainder of the
    # request is protected without waiting for the next transaction boundary.
    if db.in_transaction():
        _apply_postgres_rls_context(db.connection(), facility_id, is_super_admin)


def clear_tenant_context(db: Session) -> None:
    """Remove in-memory tenant state from a Session before it is reused."""
    db.info.pop(_RLS_FACILITY_INFO_KEY, None)
    db.info.pop(_RLS_SUPER_ADMIN_INFO_KEY, None)


def tenant_query(
    db: Session,
    model,
    current_user: User,
    base_query: Query | None = None,
) -> Query:
    """Apply application-layer tenant filtering to a SQLAlchemy query.

    PostgreSQL RLS is the database enforcement layer; this filter remains in
    place as defence in depth and for SQLite/local tests where PostgreSQL RLS is
    unavailable.
    """
    query = base_query or db.query(model)

    if current_user.role in CROSS_TENANT_ROLES:
        return query

    facility_id = current_user.facility_id
    if facility_id is None:
        # Fail closed for facility-scoped roles with no facility assignment.
        if hasattr(model, "facility_id"):
            return query.filter(model.facility_id == "__NO_FACILITY__")
        return query.filter(text("1 = 0"))

    if hasattr(model, "facility_id"):
        return query.filter(model.facility_id == facility_id)

    # Models without facility_id are global/control-plane resources.
    return query


def enforce_facility_access(current_user: User, target_facility_id: str | None) -> None:
    """Verify that the current user can access a target facility."""
    from fastapi import HTTPException

    if current_user.role in CROSS_TENANT_ROLES:
        return

    if target_facility_id and target_facility_id != current_user.facility_id:
        raise HTTPException(
            status_code=403,
            detail="Accès interdit : vous ne pouvez accéder qu'aux données de votre établissement",
        )


def get_user_facility_id(current_user: User) -> str | None:
    """Get the facility_id for the current user, or None for cross-tenant users."""
    if current_user.role in CROSS_TENANT_ROLES:
        return None
    return current_user.facility_id
