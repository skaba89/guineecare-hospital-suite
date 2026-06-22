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
    # Note: index=True on the column already creates ix_revoked_jtis_expires_at
    # automatically in SQLite. The explicit op.create_index would fail with
    # "index already exists" — so we skip it.


def downgrade():
    op.drop_table("revoked_jtis")
