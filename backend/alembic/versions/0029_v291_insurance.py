"""add insurance tables v2.9.1

Revision ID: 0029_v291_insurance
Revises: 0028_v289_perf_indexes
Create Date: 2026-07-11

v2.9.1 — Assurance / tiers payeur :
- Table insurance_providers (fournisseurs d'assurance)
- Table patient_insurances (polices d'assurance des patients)
"""
from alembic import op
import sqlalchemy as sa


revision = "0029_v291_insurance"
down_revision = "0028_v289_perf_indexes"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "insurance_providers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=True, index=True),
        sa.Column("name", sa.String(255), nullable=False, index=True),
        sa.Column("code", sa.String(50), nullable=False, index=True),
        sa.Column("coverage_rate", sa.Float(), nullable=False, server_default="0"),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "patient_insurances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=False, index=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=False, index=True),
        sa.Column("provider_id", sa.String(36), sa.ForeignKey("insurance_providers.id"), nullable=False, index=True),
        sa.Column("policy_number", sa.String(100), nullable=False),
        sa.Column("beneficiary_name", sa.String(255), nullable=True),
        sa.Column("coverage_rate", sa.Float(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("patient_insurances")
    op.drop_table("insurance_providers")
