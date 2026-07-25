"""add user.last_disabled_at v2.2.0 — Phase 6 session hardening

Revision ID: 0023_user_last_disabled_at
Revises: 0022_two_factor
Create Date: 2026-07-05

Adds the `last_disabled_at` column to the `users` table. This column is
set whenever a user is disabled (is_active=False) and is checked by the
JWT authentication middleware to invalidate tokens issued before the
disable event — providing strong session invalidation without requiring
an `issued_jtis` table.

This is a Phase 6 (security, compliance, medical confidentiality) fix
that closes the gap where a disabled user's existing access tokens
remained valid for up to 60 minutes (the natural JWT expiry).
"""
from alembic import op
import sqlalchemy as sa


revision = "0023_user_last_disabled_at"
down_revision = "0022_two_factor"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("last_disabled_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("users", "last_disabled_at")
