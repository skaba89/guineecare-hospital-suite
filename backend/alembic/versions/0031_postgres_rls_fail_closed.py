"""fail-closed PostgreSQL RLS for facility-owned business tables

Revision ID: 0031_postgres_rls_fail_closed
Revises: 0030_national_multicountry_foundation
Create Date: 2026-08-12

Phase P0-B protects every existing table whose ``facility_id`` column is
NOT NULL. This deliberately targets rows that are unambiguously owned by one
facility and avoids breaking authentication/control-plane tables where
``facility_id`` is nullable and may carry global semantics.

The migration is PostgreSQL-specific. SQLite remains supported for local/unit
tests and keeps the existing application-layer tenant filters.
"""
from alembic import op
import sqlalchemy as sa


revision = "0031_postgres_rls_fail_closed"
down_revision = "0030_national_multicountry_foundation"
branch_labels = None
depends_on = None

POLICY_NAME = "guineecare_facility_isolation"

# Explicit control-plane exceptions are documented even though the first phase
# only selects NOT NULL facility_id columns. Keeping the list here prevents a
# future schema tightening from accidentally putting pre-auth tables behind RLS.
CONTROL_PLANE_EXEMPTIONS = {
    "users",
    "refresh_tokens",
    "audit_logs",
    "revoked_jtis",
}


def _required_facility_tables(bind):
    rows = bind.execute(
        sa.text(
            """
            SELECT table_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND column_name = 'facility_id'
              AND is_nullable = 'NO'
            ORDER BY table_name
            """
        )
    ).fetchall()
    return [row[0] for row in rows if row[0] not in CONTROL_PLANE_EXEMPTIONS]


def _quoted(bind, identifier: str) -> str:
    return bind.dialect.identifier_preparer.quote(identifier)


def _policy_expression() -> str:
    # missing_ok=true makes an absent GUC return NULL. NULL comparisons do not
    # evaluate to TRUE, therefore a missing context is fail-closed.
    return """(
        COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
        OR facility_id::text = NULLIF(
            current_setting('app.current_facility_id', true), ''
        )
    )"""


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    expression = _policy_expression()
    for table_name in _required_facility_tables(bind):
        table = _quoted(bind, table_name)
        policy = _quoted(bind, POLICY_NAME)

        # RLS is enabled and forced so the table owner is also subject to the
        # policy. Superusers/BYPASSRLS roles must not be used by the app.
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy} ON {table}"))
        op.execute(
            sa.text(
                f"CREATE POLICY {policy} ON {table} "
                f"FOR ALL TO PUBLIC "
                f"USING {expression} "
                f"WITH CHECK {expression}"
            )
        )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    for table_name in _required_facility_tables(bind):
        table = _quoted(bind, table_name)
        policy = _quoted(bind, POLICY_NAME)
        op.execute(sa.text(f"DROP POLICY IF EXISTS {policy} ON {table}"))
        op.execute(sa.text(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))
