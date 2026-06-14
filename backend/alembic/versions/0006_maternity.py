"""add maternity module (maternity_records, maternity_consultations, delivery_records)

Revision ID: 0006_maternity
Revises: 0007_personnel
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0006_maternity"
down_revision = "0007_personnel"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "maternity_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("gravidity", sa.String(length=10), nullable=True),
        sa.Column("parity", sa.String(length=10), nullable=True),
        sa.Column("last_menstrual_period", sa.DateTime(), nullable=True),
        sa.Column("expected_due_date", sa.DateTime(), nullable=True),
        sa.Column("blood_type", sa.String(length=10), nullable=True),
        sa.Column("rh_factor", sa.String(length=10), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_maternity_records_facility_id", "maternity_records", ["facility_id"])
    op.create_index("ix_maternity_records_patient_id", "maternity_records", ["patient_id"])

    op.create_table(
        "maternity_consultations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("record_id", sa.String(length=36), nullable=False),
        sa.Column("consultation_type", sa.String(length=50), nullable=False),
        sa.Column("gestational_age_weeks", sa.Float(), nullable=True),
        sa.Column("weight_kg", sa.Float(), nullable=True),
        sa.Column("blood_pressure", sa.String(length=30), nullable=True),
        sa.Column("fetal_heart_rate", sa.Float(), nullable=True),
        sa.Column("fundal_height_cm", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("consulted_by", sa.String(length=36), nullable=True),
        sa.Column("consulted_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_maternity_consultations_facility_id", "maternity_consultations", ["facility_id"])
    op.create_index("ix_maternity_consultations_record_id", "maternity_consultations", ["record_id"])

    op.create_table(
        "delivery_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("record_id", sa.String(length=36), nullable=False),
        sa.Column("delivery_type", sa.String(length=50), nullable=False),
        sa.Column("delivery_date", sa.DateTime(), nullable=False),
        sa.Column("gestational_age_weeks", sa.Float(), nullable=True),
        sa.Column("complications", sa.Text(), nullable=True),
        sa.Column("baby_gender", sa.String(length=10), nullable=True),
        sa.Column("baby_weight_kg", sa.Float(), nullable=True),
        sa.Column("baby_apgar_1", sa.String(length=10), nullable=True),
        sa.Column("baby_apgar_5", sa.String(length=10), nullable=True),
        sa.Column("baby_health_status", sa.String(length=50), nullable=True),
        sa.Column("performed_by", sa.String(length=36), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_delivery_records_facility_id", "delivery_records", ["facility_id"])
    op.create_index("ix_delivery_records_record_id", "delivery_records", ["record_id"])


def downgrade():
    op.drop_table("delivery_records")
    op.drop_table("maternity_consultations")
    op.drop_table("maternity_records")
