"""activity entries

Revision ID: 0002_activity_entries
Revises: 0001_initial_mvp_schema
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_activity_entries"
down_revision = "0001_initial_mvp_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_entries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_id", sa.String(length=36), nullable=True),
        sa.Column("action_name", sa.String(length=150), nullable=False),
        sa.Column("entity_type", sa.String(length=150), nullable=True),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("level", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_activity_entries_actor_id", "activity_entries", ["actor_id"])
    op.create_index("ix_activity_entries_action_name", "activity_entries", ["action_name"])
    op.create_index("ix_activity_entries_entity_type", "activity_entries", ["entity_type"])
    op.create_index("ix_activity_entries_entity_id", "activity_entries", ["entity_id"])


def downgrade():
    op.drop_table("activity_entries")
