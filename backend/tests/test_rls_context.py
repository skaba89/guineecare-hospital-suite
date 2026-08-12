"""Unit tests for the database tenant context.

The normal backend suite uses SQLite, so these tests validate the trusted
Session.info state and keep the PostgreSQL-specific SQL as a no-op locally.
Real PostgreSQL policy enforcement is covered by scripts/test_postgres_rls.py
in the dedicated CI workflow.
"""
from types import SimpleNamespace

from app.core.tenant import bind_tenant_context, clear_tenant_context


FACILITY_KEY = "guineecare_rls_facility_id"
SUPER_KEY = "guineecare_rls_is_super_admin"


def test_bind_facility_context_uses_database_user_values(db):
    user = SimpleNamespace(role="DOCTOR", facility_id="facility-a")

    bind_tenant_context(db, user)

    assert db.info[FACILITY_KEY] == "facility-a"
    assert db.info[SUPER_KEY] is False


def test_bind_super_admin_context_is_explicit_cross_tenant(db):
    user = SimpleNamespace(role="SUPER_ADMIN", facility_id="facility-a")

    bind_tenant_context(db, user)

    assert db.info[FACILITY_KEY] is None
    assert db.info[SUPER_KEY] is True


def test_clear_tenant_context_fails_closed_for_session_reuse(db):
    user = SimpleNamespace(role="ADMIN", facility_id="facility-a")
    bind_tenant_context(db, user)

    clear_tenant_context(db)

    assert FACILITY_KEY not in db.info
    assert SUPER_KEY not in db.info
