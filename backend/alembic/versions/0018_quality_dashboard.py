"""add quality dashboard v1.4.0 — thresholds + alerts

Revision ID: 0018_quality_dashboard
Revises: 0017_sms_v14
Create Date: 2026-06-21

Adds two tables for the advanced quality dashboard:
- `quality_thresholds` : per-indicator alert thresholds (comparator + value +
  severity + cooldown). Supports LT/LE/GT/GE/EQ comparators for numeric and
  qualitative indicators.
- `quality_alerts` : concrete alerts raised when a measurement crosses a
  threshold. Lifecycle: OPEN → ACKNOWLEDGED → RESOLVED → CLOSED.

Design choices:
- `enabled` is stored as String(8) with "true"/"false" for SQLite compatibility
  (the rest of the codebase uses Boolean, but this table is new and we want
  consistent behavior across SQLite dev and PostgreSQL prod).
- `cooldown_hours` prevents alert storms when an indicator repeatedly crosses
  a threshold within a short window.
- `notify_roles` and `channels` are CSV strings to keep the schema simple
  (consistent with `notifications.channels` already in the codebase).
"""
from alembic import op
import sqlalchemy as sa


revision = "0018_quality_dashboard"
down_revision = "0017_sms_v14"
branch_labels = None
depends_on = None


def upgrade():
    # quality_thresholds
    op.create_table(
        "quality_thresholds",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=True),
        sa.Column("department_id", sa.String(36), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("indicator_id", sa.String(36), sa.ForeignKey("quality_indicators.id"), nullable=False),
        sa.Column("comparator", sa.String(8), nullable=False, server_default="GT"),
        sa.Column("threshold_value", sa.String(100), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="HIGH"),
        sa.Column("alert_message", sa.Text(), nullable=True),
        sa.Column("notify_roles", sa.String(128), nullable=True, server_default="ADMIN"),
        sa.Column("channels", sa.String(64), nullable=False, server_default="in_app"),
        sa.Column("enabled", sa.String(8), nullable=False, server_default="true"),
        sa.Column("cooldown_hours", sa.String(8), nullable=True, server_default="24"),
    )
    op.create_index("ix_quality_thresholds_facility_id", "quality_thresholds", ["facility_id"])
    op.create_index("ix_quality_thresholds_department_id", "quality_thresholds", ["department_id"])
    op.create_index("ix_quality_thresholds_indicator_id", "quality_thresholds", ["indicator_id"])

    # quality_alerts
    op.create_table(
        "quality_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=True),
        sa.Column("department_id", sa.String(36), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("threshold_id", sa.String(36), sa.ForeignKey("quality_thresholds.id"), nullable=True),
        sa.Column("measurement_id", sa.String(36), sa.ForeignKey("quality_measurements.id"), nullable=True),
        sa.Column("notification_id", sa.String(36), sa.ForeignKey("notifications.id"), nullable=True),
        sa.Column("indicator_id", sa.String(36), sa.ForeignKey("quality_indicators.id"), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="OPEN"),
        sa.Column("severity", sa.String(16), nullable=False, server_default="HIGH"),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("observed_value", sa.String(100), nullable=True),
        sa.Column("threshold_value", sa.String(100), nullable=True),
        sa.Column("comparator", sa.String(8), nullable=True),
        sa.Column("assigned_to", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("acknowledged_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_quality_alerts_created_at", "quality_alerts", ["created_at"])
    op.create_index("ix_quality_alerts_facility_id", "quality_alerts", ["facility_id"])
    op.create_index("ix_quality_alerts_department_id", "quality_alerts", ["department_id"])
    op.create_index("ix_quality_alerts_threshold_id", "quality_alerts", ["threshold_id"])
    op.create_index("ix_quality_alerts_measurement_id", "quality_alerts", ["measurement_id"])
    op.create_index("ix_quality_alerts_indicator_id", "quality_alerts", ["indicator_id"])
    op.create_index("ix_quality_alerts_status", "quality_alerts", ["status"])
    op.create_index("ix_quality_alerts_severity", "quality_alerts", ["severity"])
    op.create_index("ix_quality_alerts_assigned_to", "quality_alerts", ["assigned_to"])


def downgrade():
    op.drop_index("ix_quality_alerts_assigned_to", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_severity", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_status", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_indicator_id", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_measurement_id", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_threshold_id", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_department_id", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_facility_id", table_name="quality_alerts")
    op.drop_index("ix_quality_alerts_created_at", table_name="quality_alerts")
    op.drop_table("quality_alerts")

    op.drop_index("ix_quality_thresholds_indicator_id", table_name="quality_thresholds")
    op.drop_index("ix_quality_thresholds_department_id", table_name="quality_thresholds")
    op.drop_index("ix_quality_thresholds_facility_id", table_name="quality_thresholds")
    op.drop_table("quality_thresholds")
