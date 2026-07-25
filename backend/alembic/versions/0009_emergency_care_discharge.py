"""enrich emergency visit with care and discharge fields

Revision ID: 0009_emerg_discharge
Revises: 0008_img_surg_qual_rpt
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0009_emerg_discharge"
down_revision = "0008_img_surg_qual_rpt"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("emergency_visits", sa.Column("attending_doctor_id", sa.String(length=36), nullable=True))
    op.add_column("emergency_visits", sa.Column("vital_signs", sa.Text(), nullable=True))
    op.add_column("emergency_visits", sa.Column("treatment_notes", sa.Text(), nullable=True))
    op.add_column("emergency_visits", sa.Column("discharge_summary", sa.Text(), nullable=True))
    op.add_column("emergency_visits", sa.Column("discharge_destination", sa.String(length=100), nullable=True))
    op.add_column("emergency_visits", sa.Column("seen_at", sa.DateTime(), nullable=True))
    op.add_column("emergency_visits", sa.Column("discharged_at", sa.DateTime(), nullable=True))
    op.create_index("ix_emergency_visits_attending_doctor_id", "emergency_visits", ["attending_doctor_id"])


def downgrade():
    op.drop_index("ix_emergency_visits_attending_doctor_id", "emergency_visits")
    op.drop_column("emergency_visits", "discharged_at")
    op.drop_column("emergency_visits", "seen_at")
    op.drop_column("emergency_visits", "discharge_destination")
    op.drop_column("emergency_visits", "discharge_summary")
    op.drop_column("emergency_visits", "treatment_notes")
    op.drop_column("emergency_visits", "vital_signs")
    op.drop_column("emergency_visits", "attending_doctor_id")
