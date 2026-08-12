"""add 2FA table v1.8.0

Revision ID: 0022_two_factor
Revises: 0021_patient_medical
Create Date: 2026-06-22

Adds the `user_two_factors` table for TOTP-based two-factor authentication.
"""
from alembic import op
import sqlalchemy as sa


revision = "0022_two_factor"
down_revision = "0021_patient_medical"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_two_factors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("totp_secret", sa.String(64), nullable=False),
        sa.Column("backup_codes_hash", sa.Text(), nullable=True),
        sa.Column("backup_codes_used", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("enabled_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_user_two_factors_user_id", "user_two_factors", ["user_id"])


def downgrade():
    op.drop_index("ix_user_two_factors_user_id", table_name="user_two_factors")
    op.drop_table("user_two_factors")
