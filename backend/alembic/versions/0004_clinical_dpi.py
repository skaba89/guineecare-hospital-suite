"""add clinical DPI module

Revision ID: 0004_clinical_dpi
Revises: 0002_biz_modules
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0004_clinical_dpi"
down_revision = "0003_enrich_patient"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "clinical_notes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("admission_id", sa.String(length=36), nullable=True),
        sa.Column("note_type", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["admission_id"], ["admissions.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index("ix_clinical_notes_facility_id", "clinical_notes", ["facility_id"])
    op.create_index("ix_clinical_notes_patient_id", "clinical_notes", ["patient_id"])
    op.create_index("ix_clinical_notes_admission_id", "clinical_notes", ["admission_id"])

    op.create_table(
        "patient_measurements",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("admission_id", sa.String(length=36), nullable=True),
        sa.Column("measurement_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.String(length=100), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=True),
        sa.Column("recorded_by", sa.String(length=36), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["admission_id"], ["admissions.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
    )
    op.create_index("ix_patient_measurements_facility_id", "patient_measurements", ["facility_id"])
    op.create_index("ix_patient_measurements_patient_id", "patient_measurements", ["patient_id"])
    op.create_index("ix_patient_measurements_admission_id", "patient_measurements", ["admission_id"])

    op.create_table(
        "diagnoses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("admission_id", sa.String(length=36), nullable=True),
        sa.Column("diagnosis_code", sa.String(length=50), nullable=True),
        sa.Column("diagnosis_label", sa.String(length=255), nullable=False),
        sa.Column("diagnosis_type", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"]),
        sa.ForeignKeyConstraint(["admission_id"], ["admissions.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index("ix_diagnoses_facility_id", "diagnoses", ["facility_id"])
    op.create_index("ix_diagnoses_patient_id", "diagnoses", ["patient_id"])
    op.create_index("ix_diagnoses_admission_id", "diagnoses", ["admission_id"])


def downgrade():
    op.drop_table("diagnoses")
    op.drop_table("patient_measurements")
    op.drop_table("clinical_notes")
