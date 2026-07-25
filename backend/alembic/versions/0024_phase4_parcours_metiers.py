"""add pharmacy + billing + emergency fields v2.4.0 — Phase 4 parcours métiers

Revision ID: 0024_phase4_parcours_metiers
Revises: 0023_user_last_disabled_at
Create Date: 2026-07-05

Phase 4 — Renforcement métier hospitalier.

Ajoute les colonnes nécessaires pour :
- Pharmacie : valorisation stock (unit_price sur products),
  traçabilité lot/péremption (batch_number, expiry_date sur stock),
  dispensation liée patient (patient_id, prescription_id, admission_id
  sur stock_movements).
- Facturation : annulation contrôlée (cancellation_reason, cancelled_at,
  cancelled_by sur invoices).
"""
from alembic import op
import sqlalchemy as sa


revision = "0024_phase4_parcours_metiers"
down_revision = "0023_user_last_disabled_at"
branch_labels = None
depends_on = None


def upgrade():
    # ── Pharmacy products : unit_price ──
    op.add_column(
        "pharmacy_products",
        sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"),
    )

    # ── Pharmacy stock : batch_number + expiry_date ──
    op.add_column(
        "pharmacy_stock",
        sa.Column("batch_number", sa.String(100), nullable=True),
    )
    op.add_column(
        "pharmacy_stock",
        sa.Column("expiry_date", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_pharmacy_stock_expiry_date",
        "pharmacy_stock",
        ["expiry_date"],
    )

    # ── Stock movements : patient_id, prescription_id, admission_id ──
    # NOTE : SQLite ne supporte pas ADD FOREIGN KEY via ALTER. On ajoute la
    # colonne sans contrainte FK — le modèle SQLAlchemy déclare la FK
    # (pour PostgreSQL en prod), mais la migration reste portable SQLite.
    op.add_column(
        "stock_movements",
        sa.Column("patient_id", sa.String(36), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("prescription_id", sa.String(36), nullable=True),
    )
    op.add_column(
        "stock_movements",
        sa.Column("admission_id", sa.String(36), nullable=True),
    )
    op.create_index(
        "ix_stock_movements_patient_id",
        "stock_movements",
        ["patient_id"],
    )
    op.create_index(
        "ix_stock_movements_prescription_id",
        "stock_movements",
        ["prescription_id"],
    )
    op.create_index(
        "ix_stock_movements_admission_id",
        "stock_movements",
        ["admission_id"],
    )

    # ── Invoices : cancellation fields ──
    op.add_column(
        "invoices",
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
    )
    op.add_column(
        "invoices",
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "invoices",
        sa.Column("cancelled_by", sa.String(36), nullable=True),
    )


def downgrade():
    # Invoices
    op.drop_column("invoices", "cancelled_by")
    op.drop_column("invoices", "cancelled_at")
    op.drop_column("invoices", "cancellation_reason")

    # Stock movements
    op.drop_index("ix_stock_movements_admission_id", table_name="stock_movements")
    op.drop_index("ix_stock_movements_prescription_id", table_name="stock_movements")
    op.drop_index("ix_stock_movements_patient_id", table_name="stock_movements")
    op.drop_column("stock_movements", "admission_id")
    op.drop_column("stock_movements", "prescription_id")
    op.drop_column("stock_movements", "patient_id")

    # Pharmacy stock
    op.drop_index("ix_pharmacy_stock_expiry_date", table_name="pharmacy_stock")
    op.drop_column("pharmacy_stock", "expiry_date")
    op.drop_column("pharmacy_stock", "batch_number")

    # Pharmacy products
    op.drop_column("pharmacy_products", "unit_price")
