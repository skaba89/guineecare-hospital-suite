"""enrich patient model with demographics and emergency contacts

Revision ID: 0003_enrich_patient
Revises: 0002_biz_modules
Create Date: 2026-06-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_enrich_patient"
down_revision = "0002_biz_modules"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("patients", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("patients", sa.Column("gender", sa.String(length=10), nullable=True))
    op.add_column("patients", sa.Column("phone", sa.String(length=30), nullable=True))
    op.add_column("patients", sa.Column("address", sa.Text(), nullable=True))
    op.add_column("patients", sa.Column("national_id", sa.String(length=50), nullable=True))
    op.add_column("patients", sa.Column("insurance_number", sa.String(length=100), nullable=True))
    op.add_column("patients", sa.Column("emergency_contact_name", sa.String(length=150), nullable=True))
    op.add_column("patients", sa.Column("emergency_contact_phone", sa.String(length=30), nullable=True))
    op.create_index("ix_patients_national_id", "patients", ["national_id"], unique=True)


def downgrade():
    op.drop_index("ix_patients_national_id", table_name="patients")
    op.drop_column("patients", "emergency_contact_phone")
    op.drop_column("patients", "emergency_contact_name")
    op.drop_column("patients", "insurance_number")
    op.drop_column("patients", "national_id")
    op.drop_column("patients", "address")
    op.drop_column("patients", "phone")
    op.drop_column("patients", "gender")
    op.drop_column("patients", "date_of_birth")
