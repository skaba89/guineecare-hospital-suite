"""add leave_requests, contracts tables + staff member enhancements

Revision ID: 0010_personnel_multi
Revises: 0009_emergency
Create Date: 2026-06-15
"""

from alembic import op
import sqlalchemy as sa


revision = "0010_personnel_multi"
down_revision = "0009_emergency_care"
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to staff_members
    op.add_column("staff_members", sa.Column("contract_type", sa.String(length=50), nullable=True))
    op.add_column("staff_members", sa.Column("salary_grade", sa.String(length=20), nullable=True))

    # Create leave_requests table
    op.create_table(
        "leave_requests",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("staff_id", sa.String(length=36), nullable=False),
        sa.Column("leave_type", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("approved_by", sa.String(length=36), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_members.id"]),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index("ix_leave_requests_facility_id", "leave_requests", ["facility_id"])
    op.create_index("ix_leave_requests_staff_id", "leave_requests", ["staff_id"])

    # Create contracts table
    op.create_table(
        "contracts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("staff_id", sa.String(length=36), nullable=False),
        sa.Column("contract_type", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("position", sa.String(length=150), nullable=True),
        sa.Column("department_id", sa.String(length=36), nullable=True),
        sa.Column("salary_grade", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ACTIVE"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["facility_id"], ["facilities.id"]),
        sa.ForeignKeyConstraint(["staff_id"], ["staff_members.id"]),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )
    op.create_index("ix_contracts_facility_id", "contracts", ["facility_id"])
    op.create_index("ix_contracts_staff_id", "contracts", ["staff_id"])
    op.create_index("ix_contracts_department_id", "contracts", ["department_id"])


def downgrade():
    op.drop_table("contracts")
    op.drop_table("leave_requests")
    op.drop_column("staff_members", "salary_grade")
    op.drop_column("staff_members", "contract_type")
