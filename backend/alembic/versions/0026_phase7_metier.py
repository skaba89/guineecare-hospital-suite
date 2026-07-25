"""add prescriptions + lab_order_tests v2.6.0 — Phase 7 métier

Revision ID: 0026_phase7_metier
Revises: 0025_phase5_national_reporting
Create Date: 2026-07-05

Phase 7 — Améliorations métier (P1 reportés).

Ajoute :
- Table `prescriptions` : prescriptions médicamenteuses structurées
  (medication_name, dosage, frequency, duration, quantity, instructions)
- Table `lab_order_tests` : panel labo (1 commande = N tests)
- Rend `lab_orders.test_id` nullable (pour les panels multi-tests)
"""
from alembic import op
import sqlalchemy as sa


revision = "0026_phase7_metier"
down_revision = "0025_phase5_national_reporting"
branch_labels = None
depends_on = None


def upgrade():
    # ── Table prescriptions ──
    op.create_table(
        "prescriptions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=False, index=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False, index=True),
        sa.Column("admission_id", sa.String(36), sa.ForeignKey("admissions.id"), nullable=True, index=True),
        sa.Column("clinical_note_id", sa.String(36), sa.ForeignKey("clinical_notes.id"), nullable=True, index=True),
        sa.Column("medication_name", sa.String(255), nullable=False),
        sa.Column("dosage", sa.String(100), nullable=False),
        sa.Column("frequency", sa.String(100), nullable=False),
        sa.Column("duration", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("prescribed_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("prescribed_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # ── Table lab_order_tests (panel) ──
    op.create_table(
        "lab_order_tests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("order_id", sa.String(36), sa.ForeignKey("lab_orders.id"), nullable=False, index=True),
        sa.Column("test_id", sa.String(36), sa.ForeignKey("lab_tests.id"), nullable=False, index=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ORDERED"),
        sa.Column("result_value", sa.String(255), nullable=True),
        sa.Column("interpretation", sa.String(255), nullable=True),
        sa.Column("validated_by", sa.String(36), nullable=True),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # ── Rendre lab_orders.test_id nullable (pour les panels multi-tests) ──
    # SQLite ne supporte pas ALTER COLUMN — on utilise batch mode
    with op.batch_alter_table("lab_orders") as batch_op:
        batch_op.alter_column(
            "test_id",
            existing_type=sa.String(36),
            nullable=True,
        )


def downgrade():
    # lab_orders.test_id → NOT NULL (rétro-compat)
    with op.batch_alter_table("lab_orders") as batch_op:
        batch_op.alter_column(
            "test_id",
            existing_type=sa.String(36),
            nullable=False,
        )

    op.drop_table("lab_order_tests")
    op.drop_table("prescriptions")
