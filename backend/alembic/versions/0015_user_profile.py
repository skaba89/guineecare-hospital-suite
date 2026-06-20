"""add user_profile module: preferences, feedback, recent items

Revision ID: 0015_user_profile
Revises: 0014_jti_blacklist
Create Date: 2026-06-21

Adds three tables for v1.1.0:

- `user_preferences` — one row per user (locale, theme, page size,
  dashboard refresh interval, free-form JSON `extra` column).
- `user_feedback` — append-only feedback entries (bug, suggestion,
  question, praise) collected via the in-app feedback widget. Drives
  the change-management loop opened by v1.1.
- `user_recent_items` — sliding-window history of recently viewed
  resources per user (capped at 50 rows by the application).
"""
from alembic import op
import sqlalchemy as sa


revision = "0015_user_profile"
down_revision = "0014_jti_blacklist"
branch_labels = None
depends_on = None


def upgrade():
    # --- user_preferences ---
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("locale", sa.String(8), nullable=False, server_default="fr"),
        sa.Column("theme", sa.String(16), nullable=False, server_default="light"),
        sa.Column("default_page_size", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("dashboard_refresh_seconds", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("extra", sa.Text(), nullable=True),
    )
    op.create_index("ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True)

    # --- user_feedback ---
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("subject", sa.String(200), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("page_url", sa.String(500), nullable=True),
        sa.Column("user_agent", sa.String(512), nullable=True),
        sa.Column("admin_response", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_user_feedback_created_at", "user_feedback", ["created_at"])
    op.create_index("ix_user_feedback_user_id", "user_feedback", ["user_id"])
    op.create_index("ix_user_feedback_facility_id", "user_feedback", ["facility_id"])
    op.create_index("ix_user_feedback_category", "user_feedback", ["category"])
    op.create_index("ix_user_feedback_status", "user_feedback", ["status"])

    # --- user_recent_items ---
    op.create_table(
        "user_recent_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("resource_id", sa.String(36), nullable=False),
        sa.Column("resource_label", sa.String(200), nullable=True),
        sa.Column("viewed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "user_id", "resource_type", "resource_id",
            name="uq_user_recent_user_resource",
        ),
    )
    op.create_index("ix_user_recent_items_user_id", "user_recent_items", ["user_id"])
    op.create_index("ix_user_recent_items_viewed_at", "user_recent_items", ["viewed_at"])


def downgrade():
    op.drop_index("ix_user_recent_items_viewed_at", table_name="user_recent_items")
    op.drop_index("ix_user_recent_items_user_id", table_name="user_recent_items")
    op.drop_table("user_recent_items")

    op.drop_index("ix_user_feedback_status", table_name="user_feedback")
    op.drop_index("ix_user_feedback_category", table_name="user_feedback")
    op.drop_index("ix_user_feedback_facility_id", table_name="user_feedback")
    op.drop_index("ix_user_feedback_user_id", table_name="user_feedback")
    op.drop_index("ix_user_feedback_created_at", table_name="user_feedback")
    op.drop_table("user_feedback")

    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_table("user_preferences")
