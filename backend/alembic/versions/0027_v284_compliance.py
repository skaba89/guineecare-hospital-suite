"""add data_breaches + patient_measurements.value_numeric + lab_orders sample columns v2.8.4

Revision ID: 0027_v284_compliance
Revises: 0026_phase7_metier
Create Date: 2026-07-11

v2.8.4 — Conformité RGPD + droits patients :
- Table data_breaches (registre des violations Article 33)
- patient_measurements.value_numeric (Float, nullable — pour charts/FHIR)
- lab_orders.sample_id, collected_by, collected_at (prélèvement dédié)
"""
from alembic import op
import sqlalchemy as sa


revision = "0027_v284_compliance"
down_revision = "0026_phase7_metier"
branch_labels = None
depends_on = None


def upgrade():
    # ── Table data_breaches ──
    op.create_table(
        "data_breaches",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=True, index=True),
        sa.Column("reported_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(30), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="OPEN"),
        sa.Column("affected_patients_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notified_authority", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("notified_at", sa.DateTime(), nullable=True),
        sa.Column("authority_name", sa.String(255), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── patient_measurements.value_numeric ──
    op.add_column(
        "patient_measurements",
        sa.Column("value_numeric", sa.Float(), nullable=True),
    )

    # ── lab_orders.sample_id, collected_by, collected_at ──
    op.add_column(
        "lab_orders",
        sa.Column("sample_id", sa.String(100), nullable=True),
    )
    op.add_column(
        "lab_orders",
        sa.Column("collected_by", sa.String(36), nullable=True),
    )
    op.add_column(
        "lab_orders",
        sa.Column("collected_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("lab_orders", "collected_at")
    op.drop_column("lab_orders", "collected_by")
    op.drop_column("lab_orders", "sample_id")
    op.drop_column("patient_measurements", "value_numeric")
    op.drop_table("data_breaches")
