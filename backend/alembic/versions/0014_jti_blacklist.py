"""add jwt jti blacklist table

Revision ID: 0014_jti_blacklist
Revises: 0013_security_hardening
Create Date: 2026-06-21

Adds the `revoked_jtis` table for JWT ID (jti) revocation tracking.
This implements OWASP A07 hardening: even though access tokens are
short-lived (60 min), explicit logout or admin-driven user disable
can now revoke a specific jti before its natural expiry.

Rows are pruned automatically — the table only holds entries whose
associated token has not yet expired.
"""
from alembic import op
import sqlalchemy as sa


revision = "0014_jti_blacklist"
down_revision = "0013_security_hardening"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "revoked_jtis",
        sa.Column("jti", sa.String(64), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("reason", sa.String(64), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False, index=True),
    )
    op.create_index("ix_revoked_jtis_expires_at", "revoked_jtis", ["expires_at"])


def downgrade():
    op.drop_index("ix_revoked_jtis_expires_at", table_name="revoked_jtis")
    op.drop_table("revoked_jtis")
