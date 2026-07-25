"""add notifications table

Revision ID: 0012_notifications
Revises: 0011_refresh_audit
Create Date: 2026-06-20

Adds:
- notifications table for in-app user notifications (with pluggable provider hook for email/SMS)
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_notifications"
down_revision = "0011_refresh_audit"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        # Recipient (required) — the user who will see this notification
        sa.Column("recipient_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("facility_id", sa.String(length=36), sa.ForeignKey("facilities.id"), nullable=True, index=True),
        # Sender (optional — null for system-generated notifications)
        sa.Column("sender_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        # Classification
        sa.Column("category", sa.String(length=32), nullable=False, index=True),
        # e.g. "system", "lab_result", "appointment", "pharmacy", "billing", "emergency"
        sa.Column("priority", sa.String(length=16), nullable=False, server_default="normal"),
        # "low" | "normal" | "high" | "urgent"
        # Content
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("action_url", sa.String(length=500), nullable=True),
        # Optional deep-link (e.g. "/patients/abc-123" or "/lab/orders/xyz")
        # Channel delivery state
        sa.Column("channels", sa.String(length=64), nullable=False, server_default="in_app"),
        # comma-separated: "in_app,email,sms" — what was attempted
        sa.Column("in_app_delivered", sa.Boolean(), nullable=False, server_default=sa.sql.true()),
        sa.Column("email_delivered", sa.Boolean(), nullable=False, server_default=sa.sql.false()),
        sa.Column("sms_delivered", sa.Boolean(), nullable=False, server_default=sa.sql.false()),
        sa.Column("delivery_error", sa.Text(), nullable=True),
        # Read state
        sa.Column("read_at", sa.DateTime(), nullable=True, index=True),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        # Optional reference to a domain object (resource_type + resource_id)
        sa.Column("resource_type", sa.String(length=64), nullable=True),
        sa.Column("resource_id", sa.String(length=36), nullable=True),
    )
    op.create_index(
        "ix_notifications_recipient_unread",
        "notifications",
        ["recipient_id", "read_at"],
    )
    op.create_index(
        "ix_notifications_facility_created",
        "notifications",
        ["facility_id", "created_at"],
    )


def downgrade():
    op.drop_index("ix_notifications_facility_created", table_name="notifications")
    op.drop_index("ix_notifications_recipient_unread", table_name="notifications")
    op.drop_table("notifications")
