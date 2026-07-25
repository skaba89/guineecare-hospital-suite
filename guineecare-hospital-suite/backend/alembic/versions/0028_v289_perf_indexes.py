"""add performance indexes v2.8.9

Revision ID: 0028_v289_perf_indexes
Revises: 0027_v284_compliance
Create Date: 2026-07-11

v2.8.9 — Index de performance pour les colonnes fréquemment filtrées :
- admissions.status, admissions.admitted_at
- emergency_visits.status, emergency_visits.arrived_at
- lab_orders.status, lab_orders.ordered_at
- invoices.status, invoices.created_at
- patients.status, patients.created_at
- clinical_notes.created_at
"""
from alembic import op
import sqlalchemy as sa


revision = "0028_v289_perf_indexes"
down_revision = "0027_v284_compliance"
branch_labels = None
depends_on = None


def upgrade():
    # Admissions
    op.create_index("ix_admissions_status", "admissions", ["status"])
    op.create_index("ix_admissions_admitted_at", "admissions", ["admitted_at"])

    # Emergency visits
    op.create_index("ix_emergency_visits_status", "emergency_visits", ["status"])
    op.create_index("ix_emergency_visits_arrived_at", "emergency_visits", ["arrived_at"])

    # Lab orders
    op.create_index("ix_lab_orders_status", "lab_orders", ["status"])
    op.create_index("ix_lab_orders_ordered_at", "lab_orders", ["ordered_at"])

    # Invoices
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_created_at", "invoices", ["created_at"])

    # Patients
    op.create_index("ix_patients_status", "patients", ["status"])
    op.create_index("ix_patients_created_at", "patients", ["created_at"])

    # Clinical notes
    op.create_index("ix_clinical_notes_created_at", "clinical_notes", ["created_at"])


def downgrade():
    op.drop_index("ix_clinical_notes_created_at", table_name="clinical_notes")
    op.drop_index("ix_patients_created_at", table_name="patients")
    op.drop_index("ix_patients_status", table_name="patients")
    op.drop_index("ix_invoices_created_at", table_name="invoices")
    op.drop_index("ix_invoices_status", table_name="invoices")
    op.drop_index("ix_lab_orders_ordered_at", table_name="lab_orders")
    op.drop_index("ix_lab_orders_status", table_name="lab_orders")
    op.drop_index("ix_emergency_visits_arrived_at", table_name="emergency_visits")
    op.drop_index("ix_emergency_visits_status", table_name="emergency_visits")
    op.drop_index("ix_admissions_admitted_at", table_name="admissions")
    op.drop_index("ix_admissions_status", table_name="admissions")
