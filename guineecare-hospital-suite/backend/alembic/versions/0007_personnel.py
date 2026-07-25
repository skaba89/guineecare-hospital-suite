"""add personnel module (staff_members, on_call_schedules)

Revision ID: 0007_personnel
Revises: 0005_hospital
Create Date: 2026-06-05
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_personnel"
down_revision = "0005_hospital"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "staff_members",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("employee_number", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=150), nullable=False),
        sa.Column("last_name", sa.String(length=150), nullable=False),
        sa.Column("profession", sa.String(length=100), nullable=True),
        sa.Column("specialty", sa.String(length=100), nullable=True),
        sa.Column("department_id", sa.String(length=36), nullable=True),
        sa.Column("phone", sa.String(length=30), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("hire_date", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_staff_members_facility_id", "staff_members", ["facility_id"])
    op.create_index("ix_staff_members_user_id", "staff_members", ["user_id"])
    op.create_index("ix_staff_members_employee_number", "staff_members", ["employee_number"], unique=True)
    op.create_index("ix_staff_members_department_id", "staff_members", ["department_id"])

    op.create_table(
        "on_call_schedules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("department_id", sa.String(length=36), nullable=True),
        sa.Column("staff_id", sa.String(length=36), nullable=False),
        sa.Column("on_call_date", sa.DateTime(), nullable=False),
        sa.Column("shift_type", sa.String(length=50), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_on_call_schedules_facility_id", "on_call_schedules", ["facility_id"])
    op.create_index("ix_on_call_schedules_department_id", "on_call_schedules", ["department_id"])
    op.create_index("ix_on_call_schedules_staff_id", "on_call_schedules", ["staff_id"])


def downgrade():
    op.drop_table("on_call_schedules")
    op.drop_table("staff_members")
