"""business-specific RLS for nullable facility_id tables

Revision ID: 0032_nullable_facility_rls
Revises: 0031_postgres_rls_fail_closed
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa

revision = "0032_nullable_facility_rls"
down_revision = "0031_postgres_rls_fail_closed"
branch_labels = None
depends_on = None

# Tables whose NULL semantics are handled by bespoke user/facility policies.
SPECIAL_POLICY_TABLES = {"data_breaches", "notifications", "user_feedback"}

# Shared national/reference rows (facility_id IS NULL) are readable by an
# authenticated facility user, but only SUPER_ADMIN may create/update/delete
# those global rows. Facility-specific overrides remain tenant-scoped.
SHARED_REFERENCE_TABLES = {
    "insurance_providers",
    "quality_thresholds",
    "sms_routing_rules",
}

# Operational rows with facility_id NULL are system/national events and must
# never become visible or writable to a facility role.
NATIONAL_NULL_OPERATIONAL_TABLES = {
    "quality_alerts",
    "sms_messages",
}

# Explicit exceptions live outside tenant RLS because they are control-plane
# identity/audit state protected by separate authorization rules.
CONTROL_PLANE_EXEMPTIONS = {"users", "refresh_tokens", "audit_logs"}

POLICY_TABLES = (
    SPECIAL_POLICY_TABLES
    | SHARED_REFERENCE_TABLES
    | NATIONAL_NULL_OPERATIONAL_TABLES
)


def _q(bind, name):
    return bind.dialect.identifier_preparer.quote(name)


def _nullable_facility_tables(bind):
    return {
        row[0]
        for row in bind.execute(sa.text("""
            SELECT table_name
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND column_name = 'facility_id'
              AND is_nullable = 'YES'
        """)).fetchall()
    }


def _enable(bind, table):
    t = _q(bind, table)
    op.execute(sa.text(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text(f"ALTER TABLE {t} FORCE ROW LEVEL SECURITY"))


def _drop_all(bind, table):
    t = _q(bind, table)
    rows = bind.execute(sa.text("""
        SELECT policyname FROM pg_policies
        WHERE schemaname = current_schema() AND tablename = :table
    """), {"table": table}).fetchall()
    for row in rows:
        op.execute(sa.text(f"DROP POLICY IF EXISTS {_q(bind, row[0])} ON {t}"))


def _create(bind, table, name, command, using=None, check=None):
    t = _q(bind, table)
    p = _q(bind, name)
    sql = f"CREATE POLICY {p} ON {t} FOR {command} TO PUBLIC"
    if using:
        sql += f" USING ({using})"
    if check:
        sql += f" WITH CHECK ({check})"
    op.execute(sa.text(sql))


def _create_shared_reference_policies(bind, table, super_admin, facility, has_user):
    """Global rows readable to tenants, global writes reserved to SUPER_ADMIN."""
    _enable(bind, table)
    _drop_all(bind, table)

    read_expr = (
        f"{super_admin} OR ("
        f"{has_user} AND (facility_id IS NULL OR ({facility} AND facility_id IS NOT NULL))"
        f")"
    )
    tenant_write = (
        f"{super_admin} OR ("
        f"{has_user} AND facility_id IS NOT NULL AND {facility}"
        f")"
    )

    _create(bind, table, f"guineecare_{table}_select", "SELECT", read_expr)
    _create(bind, table, f"guineecare_{table}_insert", "INSERT", check=tenant_write)
    _create(bind, table, f"guineecare_{table}_update", "UPDATE", tenant_write, tenant_write)
    _create(bind, table, f"guineecare_{table}_delete", "DELETE", tenant_write)


def _create_national_null_operational_policy(bind, table, super_admin, facility, has_user):
    """Facility users see only owned non-NULL rows; NULL rows are national-only."""
    _enable(bind, table)
    _drop_all(bind, table)
    expr = (
        f"{super_admin} OR ("
        f"{has_user} AND facility_id IS NOT NULL AND {facility}"
        f")"
    )
    _create(bind, table, f"guineecare_{table}_scope", "ALL", expr, expr)


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return

    nullable = _nullable_facility_tables(bind)

    # Fail closed on schema evolution: no nullable facility_id table may enter
    # production without an explicit business classification.
    unknown = nullable - POLICY_TABLES - CONTROL_PLANE_EXEMPTIONS
    if unknown:
        raise RuntimeError(
            "Nullable facility_id tables require explicit RLS classification: "
            + ", ".join(sorted(unknown))
        )

    # Defensive classification invariant: a table must belong to one and only
    # one bucket. This prevents accidental policy weakening during maintenance.
    buckets = [
        SPECIAL_POLICY_TABLES,
        SHARED_REFERENCE_TABLES,
        NATIONAL_NULL_OPERATIONAL_TABLES,
        CONTROL_PLANE_EXEMPTIONS,
    ]
    overlaps = set()
    for index, bucket in enumerate(buckets):
        for other in buckets[index + 1:]:
            overlaps |= bucket & other
    if overlaps:
        raise RuntimeError(
            "Nullable facility_id tables have conflicting RLS classifications: "
            + ", ".join(sorted(overlaps))
        )

    super_admin = "COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'"
    facility = "facility_id::text = NULLIF(current_setting('app.current_facility_id', true), '')"
    user = "user_id::text = NULLIF(current_setting('app.current_user_id', true), '')"
    recipient = "recipient_id::text = NULLIF(current_setting('app.current_user_id', true), '')"
    role_admin = "current_setting('app.current_role', true) = 'ADMIN'"
    sender = "sender_id::text = NULLIF(current_setting('app.current_user_id', true), '')"
    has_user = "NULLIF(current_setting('app.current_user_id', true), '') IS NOT NULL"

    if "data_breaches" in nullable:
        _enable(bind, "data_breaches")
        _drop_all(bind, "data_breaches")
        expr = f"{super_admin} OR ({facility} AND facility_id IS NOT NULL)"
        _create(bind, "data_breaches", "guineecare_breach_scope", "ALL", expr, expr)

    if "user_feedback" in nullable:
        _enable(bind, "user_feedback")
        _drop_all(bind, "user_feedback")
        read_expr = f"{super_admin} OR {user} OR ({role_admin} AND {facility})"
        admin_expr = f"{super_admin} OR ({role_admin} AND {facility})"
        insert_expr = f"{super_admin} OR ({user} AND {facility})"
        _create(bind, "user_feedback", "guineecare_feedback_select", "SELECT", read_expr)
        _create(bind, "user_feedback", "guineecare_feedback_insert", "INSERT", check=insert_expr)
        _create(bind, "user_feedback", "guineecare_feedback_update", "UPDATE", admin_expr, admin_expr)
        _create(bind, "user_feedback", "guineecare_feedback_delete", "DELETE", admin_expr)

    if "notifications" in nullable:
        _enable(bind, "notifications")
        _drop_all(bind, "notifications")
        own = f"{super_admin} OR {recipient}"
        insert_expr = (
            f"{super_admin} OR ("
            f"{has_user} AND (sender_id IS NULL OR {sender}) AND ("
            f"({facility} AND facility_id IS NOT NULL) OR "
            f"(facility_id IS NULL AND {recipient})"
            f"))"
        )
        _create(bind, "notifications", "guineecare_notification_select", "SELECT", own)
        _create(bind, "notifications", "guineecare_notification_insert", "INSERT", check=insert_expr)
        _create(bind, "notifications", "guineecare_notification_update", "UPDATE", own, own)
        _create(bind, "notifications", "guineecare_notification_delete", "DELETE", own)

    for table in sorted(nullable & SHARED_REFERENCE_TABLES):
        _create_shared_reference_policies(bind, table, super_admin, facility, has_user)

    for table in sorted(nullable & NATIONAL_NULL_OPERATIONAL_TABLES):
        _create_national_null_operational_policy(bind, table, super_admin, facility, has_user)


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    nullable = _nullable_facility_tables(bind)
    for table in POLICY_TABLES:
        if table not in nullable:
            continue
        _drop_all(bind, table)
        t = _q(bind, table)
        op.execute(sa.text(f"ALTER TABLE {t} NO FORCE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY"))
