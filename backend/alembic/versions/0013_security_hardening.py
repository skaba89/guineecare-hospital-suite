"""add user lockout columns and notifications.audit_log hardening

Revision ID: 0013_security_hardening
Revises: 0012_notifications
Create Date: 2026-06-20

Adds:
- users.failed_login_count (int, default 0)
- users.locked_until (datetime, nullable)

For account lockout after repeated failed logins (OWASP A04-001 fix).
"""

from alembic import op
import sqlalchemy as sa


revision = "0013_security_hardening"
down_revision = "0012_notifications"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("locked_until", sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_count")
