"""add refresh_tokens and audit_logs tables

Revision ID: 0011_refresh_audit
Revises: 0010_personnel_multi
Create Date: 2026-06-20

Adds:
- refresh_tokens table for JWT refresh token rotation + revocation
- audit_logs table for compliance-grade activity tracking
"""

from alembic import op
import sqlalchemy as sa


revision = "0011_refresh_audit"
down_revision = "0010_personnel_multi"
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # refresh_tokens — long-lived tokens used to obtain new access tokens
    # ------------------------------------------------------------------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(length=128), nullable=False, index=True, unique=True),
        sa.Column("facility_id", sa.String(length=36), sa.ForeignKey("facilities.id"), nullable=True, index=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False, index=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("created_ip", sa.String(length=45), nullable=True),
        sa.Column("created_user_agent", sa.String(length=512), nullable=True),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("replaced_by_id", sa.String(length=36), sa.ForeignKey("refresh_tokens.id"), nullable=True),
    )
    op.create_index("ix_refresh_tokens_user_active", "refresh_tokens", ["user_id", "revoked_at"])

    # ------------------------------------------------------------------
    # audit_logs — append-only journal of all mutations
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True, index=True),
        sa.Column("facility_id", sa.String(length=36), sa.ForeignKey("facilities.id"), nullable=True, index=True),
        sa.Column("action", sa.String(length=64), nullable=False, index=True),
        # e.g. "patient.create", "user.update", "auth.login", "pharmacy.dispense"
        sa.Column("resource_type", sa.String(length=64), nullable=True, index=True),
        # e.g. "patient", "user", "admission", "lab_order"
        sa.Column("resource_id", sa.String(length=36), nullable=True, index=True),
        sa.Column("http_method", sa.String(length=10), nullable=True),
        sa.Column("http_path", sa.String(length=512), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        # JSON payload with before/after diff (for mutations)
        sa.Column("payload", sa.Text(), nullable=True),
    )
    op.create_index("ix_audit_logs_facility_created", "audit_logs", ["facility_id", "created_at"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])


def downgrade():
    op.drop_index("ix_audit_logs_resource", table_name="audit_logs")
    op.drop_index("ix_audit_logs_facility_created", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_refresh_tokens_user_active", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
