"""add hospitalization module (rooms, beds, stays)

Revision ID: 0005_hospitalization
Revises: 0003_enrich_patient, 0004_clinical_dpi
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0005_hospital"
down_revision = ("0003_enrich_patient", "0004_clinical_dpi")
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rooms",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("department_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("room_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_rooms_facility_id", "rooms", ["facility_id"])
    op.create_index("ix_rooms_department_id", "rooms", ["department_id"])
    op.create_index("ix_rooms_code", "rooms", ["code"])

    op.create_table(
        "beds",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("room_id", sa.String(length=36), nullable=False),
        sa.Column("bed_number", sa.String(length=50), nullable=False),
        sa.Column("bed_status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_beds_facility_id", "beds", ["facility_id"])
    op.create_index("ix_beds_room_id", "beds", ["room_id"])

    op.create_table(
        "hospital_stays",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("admission_id", sa.String(length=36), nullable=True),
        sa.Column("bed_id", sa.String(length=36), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("admitted_at", sa.DateTime(), nullable=False),
        sa.Column("discharged_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_hospital_stays_facility_id", "hospital_stays", ["facility_id"])
    op.create_index("ix_hospital_stays_patient_id", "hospital_stays", ["patient_id"])
    op.create_index("ix_hospital_stays_admission_id", "hospital_stays", ["admission_id"])
    op.create_index("ix_hospital_stays_bed_id", "hospital_stays", ["bed_id"])


def downgrade():
    op.drop_table("hospital_stays")
    op.drop_table("beds")
    op.drop_table("rooms")
