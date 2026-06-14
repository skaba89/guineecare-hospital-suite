"""initial MVP schema

Revision ID: 0001_initial_mvp_schema
Revises: None
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_mvp_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "facilities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("region", sa.String(length=150), nullable=True),
        sa.Column("prefecture", sa.String(length=150), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_facilities_code", "facilities", ["code"], unique=True)
    op.create_index("ix_facilities_name", "facilities", ["name"])

    op.create_table(
        "departments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_departments_facility_id", "departments", ["facility_id"])
    op.create_index("ix_departments_code", "departments", ["code"])
    op.create_index("ix_departments_name", "departments", ["name"])

    op.create_table(
        "patients",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_number", sa.String(length=50), nullable=False),
        sa.Column("first_name", sa.String(length=150), nullable=False),
        sa.Column("last_name", sa.String(length=150), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_patients_facility_id", "patients", ["facility_id"])
    op.create_index("ix_patients_patient_number", "patients", ["patient_number"], unique=True)

    op.create_table(
        "admissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("department_id", sa.String(length=36), nullable=True),
        sa.Column("admission_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("admitted_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_admissions_facility_id", "admissions", ["facility_id"])
    op.create_index("ix_admissions_patient_id", "admissions", ["patient_id"])
    op.create_index("ix_admissions_department_id", "admissions", ["department_id"])

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("first_name", sa.String(length=150), nullable=False),
        sa.Column("last_name", sa.String(length=150), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_facility_id", "users", ["facility_id"])

    op.create_table(
        "roles",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_roles_code", "roles", ["code"], unique=True)

    op.create_table(
        "permissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=150), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("module", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"], unique=True)

    op.create_table(
        "role_permissions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("role_code", sa.String(length=100), nullable=False),
        sa.Column("permission_code", sa.String(length=150), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("role_code", "permission_code", name="uq_role_permission"),
    )
    op.create_index("ix_role_permissions_role_code", "role_permissions", ["role_code"])
    op.create_index("ix_role_permissions_permission_code", "role_permissions", ["permission_code"])


def downgrade():
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
    op.drop_table("admissions")
    op.drop_table("patients")
    op.drop_table("departments")
    op.drop_table("facilities")
