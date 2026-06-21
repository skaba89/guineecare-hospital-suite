"""add SMS module v1.4.0 — providers, messages, routing rules

Revision ID: 0017_sms_v14
Revises: 0016_documents
Create Date: 2026-06-21

Adds three tables for real SMS support:
- `sms_providers` : Orange / MTN / Moov / Mock provider configurations.
- `sms_messages`  : journal of every SMS sent (status, cost, operator_message_id).
- `sms_routing_rules` : per-category routing (e.g. lab_critical → sms+in_app, urgent).

Design choices:
- Credentials are stored encrypted (see sms_provider.encrypt_credential).
  In dev/test (no FERNET_KEY env var), they fall back to plaintext.
- `provider_code` is duplicated on `sms_messages` so historical rows remain
  readable even if the provider is later deleted (provider_id becomes NULL).
- `cost_per_sms_gnf` is in Franc Guinéen (GNF) — local currency convention.
- Routing rules are global by default (facility_id NULL) but can be overridden
  per facility.
"""
from alembic import op
import sqlalchemy as sa


revision = "0017_sms_v14"
down_revision = "0016_documents"
branch_labels = None
depends_on = None


def upgrade():
    # sms_providers
    op.create_table(
        "sms_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("code", sa.String(32), unique=True, nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("api_url", sa.String(512), nullable=True),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("api_secret_encrypted", sa.Text(), nullable=True),
        sa.Column("sender_id", sa.String(32), nullable=True),
        sa.Column("cost_per_sms_gnf", sa.Integer(), nullable=True),
        sa.Column("rate_per_second", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("daily_quota", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sms_providers_code", "sms_providers", ["code"])
    op.create_index("ix_sms_providers_enabled", "sms_providers", ["enabled"])

    # sms_messages
    op.create_table(
        "sms_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("sms_providers.id"), nullable=True),
        sa.Column("provider_code", sa.String(32), nullable=False),
        sa.Column("recipient_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("recipient_phone", sa.String(32), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("notification_id", sa.String(36), sa.ForeignKey("notifications.id"), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="PENDING"),
        sa.Column("operator_message_id", sa.String(128), nullable=True),
        sa.Column("error_code", sa.String(32), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("cost_gnf", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_sms_messages_created_at", "sms_messages", ["created_at"])
    op.create_index("ix_sms_messages_facility_id", "sms_messages", ["facility_id"])
    op.create_index("ix_sms_messages_provider_id", "sms_messages", ["provider_id"])
    op.create_index("ix_sms_messages_recipient_id", "sms_messages", ["recipient_id"])
    op.create_index("ix_sms_messages_recipient_phone", "sms_messages", ["recipient_phone"])
    op.create_index("ix_sms_messages_category", "sms_messages", ["category"])
    op.create_index("ix_sms_messages_status", "sms_messages", ["status"])
    op.create_index("ix_sms_messages_notification_id", "sms_messages", ["notification_id"])

    # sms_routing_rules
    op.create_table(
        "sms_routing_rules",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=True),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("channels", sa.String(64), nullable=False, server_default="in_app"),
        sa.Column("min_priority", sa.String(16), nullable=False, server_default="normal"),
        sa.Column("preferred_provider_id", sa.String(36), sa.ForeignKey("sms_providers.id"), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_sms_routing_rules_facility_id", "sms_routing_rules", ["facility_id"])
    op.create_index("ix_sms_routing_rules_category", "sms_routing_rules", ["category"])
    op.create_index("ix_sms_routing_rules_enabled", "sms_routing_rules", ["enabled"])


def downgrade():
    op.drop_index("ix_sms_routing_rules_enabled", table_name="sms_routing_rules")
    op.drop_index("ix_sms_routing_rules_category", table_name="sms_routing_rules")
    op.drop_index("ix_sms_routing_rules_facility_id", table_name="sms_routing_rules")
    op.drop_table("sms_routing_rules")

    op.drop_index("ix_sms_messages_notification_id", table_name="sms_messages")
    op.drop_index("ix_sms_messages_status", table_name="sms_messages")
    op.drop_index("ix_sms_messages_category", table_name="sms_messages")
    op.drop_index("ix_sms_messages_recipient_phone", table_name="sms_messages")
    op.drop_index("ix_sms_messages_recipient_id", table_name="sms_messages")
    op.drop_index("ix_sms_messages_provider_id", table_name="sms_messages")
    op.drop_index("ix_sms_messages_facility_id", table_name="sms_messages")
    op.drop_index("ix_sms_messages_created_at", table_name="sms_messages")
    op.drop_table("sms_messages")

    op.drop_index("ix_sms_providers_enabled", table_name="sms_providers")
    op.drop_index("ix_sms_providers_code", table_name="sms_providers")
    op.drop_table("sms_providers")
