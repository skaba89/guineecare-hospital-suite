"""add MVP business modules

Revision ID: 0002_mvp_business_modules
Revises: 0001_initial_mvp_schema
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_mvp_business_modules"
down_revision = "0001_initial_mvp_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "activity_entries",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=True),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("action", sa.String(length=150), nullable=False),
        sa.Column("resource_type", sa.String(length=150), nullable=True),
        sa.Column("resource_id", sa.String(length=36), nullable=True),
        sa.Column("message", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_activity_entries_facility_id", "activity_entries", ["facility_id"])
    op.create_index("ix_activity_entries_user_id", "activity_entries", ["user_id"])

    op.create_table(
        "emergency_visits",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("admission_id", sa.String(length=36), nullable=True),
        sa.Column("priority_level", sa.String(length=50), nullable=False),
        sa.Column("chief_complaint", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("orientation", sa.String(length=100), nullable=True),
        sa.Column("arrived_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_emergency_visits_facility_id", "emergency_visits", ["facility_id"])
    op.create_index("ix_emergency_visits_patient_id", "emergency_visits", ["patient_id"])
    op.create_index("ix_emergency_visits_admission_id", "emergency_visits", ["admission_id"])

    op.create_table(
        "pharmacy_products",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("form", sa.String(length=100), nullable=True),
        sa.Column("dosage", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_pharmacy_products_facility_id", "pharmacy_products", ["facility_id"])
    op.create_index("ix_pharmacy_products_code", "pharmacy_products", ["code"])
    op.create_index("ix_pharmacy_products_name", "pharmacy_products", ["name"])

    op.create_table(
        "pharmacy_stock",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("quantity_available", sa.Float(), nullable=False),
        sa.Column("min_threshold", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_pharmacy_stock_facility_id", "pharmacy_stock", ["facility_id"])
    op.create_index("ix_pharmacy_stock_product_id", "pharmacy_stock", ["product_id"])

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("product_id", sa.String(length=36), nullable=False),
        sa.Column("movement_type", sa.String(length=50), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("performed_by", sa.String(length=36), nullable=True),
        sa.Column("performed_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_stock_movements_facility_id", "stock_movements", ["facility_id"])
    op.create_index("ix_stock_movements_product_id", "stock_movements", ["product_id"])

    op.create_table(
        "lab_tests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("sample_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_lab_tests_facility_id", "lab_tests", ["facility_id"])
    op.create_index("ix_lab_tests_code", "lab_tests", ["code"])
    op.create_index("ix_lab_tests_name", "lab_tests", ["name"])

    op.create_table(
        "lab_orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("admission_id", sa.String(length=36), nullable=True),
        sa.Column("test_id", sa.String(length=36), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("ordered_by", sa.String(length=36), nullable=True),
        sa.Column("ordered_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_lab_orders_facility_id", "lab_orders", ["facility_id"])
    op.create_index("ix_lab_orders_patient_id", "lab_orders", ["patient_id"])
    op.create_index("ix_lab_orders_admission_id", "lab_orders", ["admission_id"])
    op.create_index("ix_lab_orders_test_id", "lab_orders", ["test_id"])

    op.create_table(
        "lab_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("result_value", sa.String(length=255), nullable=False),
        sa.Column("interpretation", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("entered_by", sa.String(length=36), nullable=True),
        sa.Column("validated_by", sa.String(length=36), nullable=True),
        sa.Column("entered_at", sa.DateTime(), nullable=False),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_lab_results_facility_id", "lab_results", ["facility_id"])
    op.create_index("ix_lab_results_order_id", "lab_results", ["order_id"])

    op.create_table(
        "tariff_items",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("unit_price", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_tariff_items_facility_id", "tariff_items", ["facility_id"])
    op.create_index("ix_tariff_items_code", "tariff_items", ["code"])

    op.create_table(
        "invoices",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("admission_id", sa.String(length=36), nullable=True),
        sa.Column("invoice_number", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("net_amount", sa.Float(), nullable=False),
        sa.Column("paid_amount", sa.Float(), nullable=False),
        sa.Column("balance_due", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_invoices_facility_id", "invoices", ["facility_id"])
    op.create_index("ix_invoices_patient_id", "invoices", ["patient_id"])
    op.create_index("ix_invoices_admission_id", "invoices", ["admission_id"])
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"], unique=True)

    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("invoice_id", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("payment_method", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("received_by", sa.String(length=36), nullable=True),
        sa.Column("received_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_payments_facility_id", "payments", ["facility_id"])
    op.create_index("ix_payments_invoice_id", "payments", ["invoice_id"])


def downgrade():
    op.drop_table("payments")
    op.drop_table("invoices")
    op.drop_table("tariff_items")
    op.drop_table("lab_results")
    op.drop_table("lab_orders")
    op.drop_table("lab_tests")
    op.drop_table("stock_movements")
    op.drop_table("pharmacy_stock")
    op.drop_table("pharmacy_products")
    op.drop_table("emergency_visits")
    op.drop_table("activity_entries")
