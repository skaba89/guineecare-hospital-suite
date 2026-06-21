"""add RH v2 module v1.5.0 — shifts, assignments, leave balances, on-call duties, swaps

Revision ID: 0019_rh_v2
Revises: 0018_quality_dashboard
Create Date: 2026-06-21

Adds 5 tables for the advanced HR / planning module (RH v2):

- `shifts` : templates récurrents (DAY/NIGHT/FULL_DAY/ON_CALL) avec
  récurrence DAILY/WEEKDAYS/WEEKEND/CUSTOM.
- `shift_assignments` : affectations concrètes d'un staff à un shift à une
  date donnée. Statut SCHEDULED → CONFIRMED → COMPLETED (ou ABSENT/CANCELLED).
- `leave_balances` : soldes de congés par staff et par année (accumulated,
  used, carried_over, pending — remaining calculé à la volée).
- `on_call_duties` : astreintes (TELEPHONIC/PHYSICAL/MIXED) avec compensation
  en jours de récupération.
- `shift_swaps` : demandes de remplacement entre staffs (workflow REQUESTED →
  ACCEPTED → APPROVED → COMPLETED).

Conventions :
- Multi-tenant via `facility_id` (NULL interdit sauf pour `days_of_week` qui
  est nullable car optionnel).
- Les `staff_id` référencent `staff_members` (table existante du module
  personnel v1).
- Index sur les colonnes fréquemment filtrées : facility_id, department_id,
  staff_id, assignment_date, status.
"""
from alembic import op
import sqlalchemy as sa


revision = "0019_rh_v2"
down_revision = "0018_quality_dashboard"
branch_labels = None
depends_on = None


def upgrade():
    # shifts
    op.create_table(
        "shifts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=False),
        sa.Column("department_id", sa.String(36), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("shift_type", sa.String(32), nullable=False),
        sa.Column("color", sa.String(16), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("duration_hours", sa.Integer(), nullable=True),
        sa.Column("recurrence", sa.String(32), nullable=False, server_default="DAILY"),
        sa.Column("days_of_week", sa.String(32), nullable=True),
        sa.Column("required_staff_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("required_profession", sa.String(100), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.create_index("ix_shifts_facility_id", "shifts", ["facility_id"])
    op.create_index("ix_shifts_department_id", "shifts", ["department_id"])
    op.create_index("ix_shifts_code", "shifts", ["code"])
    op.create_index("ix_shifts_enabled", "shifts", ["enabled"])

    # shift_assignments
    op.create_table(
        "shift_assignments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=False),
        sa.Column("department_id", sa.String(36), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("shift_id", sa.String(36), sa.ForeignKey("shifts.id"), nullable=False),
        sa.Column("staff_id", sa.String(36), sa.ForeignKey("staff_members.id"), nullable=False),
        sa.Column("assignment_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_shift_assignments_facility_id", "shift_assignments", ["facility_id"])
    op.create_index("ix_shift_assignments_department_id", "shift_assignments", ["department_id"])
    op.create_index("ix_shift_assignments_shift_id", "shift_assignments", ["shift_id"])
    op.create_index("ix_shift_assignments_staff_id", "shift_assignments", ["staff_id"])
    op.create_index("ix_shift_assignments_assignment_date", "shift_assignments", ["assignment_date"])
    op.create_index("ix_shift_assignments_status", "shift_assignments", ["status"])

    # leave_balances
    op.create_table(
        "leave_balances",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=False),
        sa.Column("staff_id", sa.String(36), sa.ForeignKey("staff_members.id"), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("accumulated_days", sa.Integer(), nullable=False, server_default="26"),
        sa.Column("used_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("carried_over_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pending_days", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_leave_balances_facility_id", "leave_balances", ["facility_id"])
    op.create_index("ix_leave_balances_staff_id", "leave_balances", ["staff_id"])
    op.create_index("ix_leave_balances_year", "leave_balances", ["year"])

    # on_call_duties
    op.create_table(
        "on_call_duties",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=False),
        sa.Column("department_id", sa.String(36), sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("staff_id", sa.String(36), sa.ForeignKey("staff_members.id"), nullable=False),
        sa.Column("start_at", sa.DateTime(), nullable=False),
        sa.Column("end_at", sa.DateTime(), nullable=False),
        sa.Column("duty_type", sa.String(32), nullable=False, server_default="TELEPHONIC"),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="SCHEDULED"),
        sa.Column("compensation_days", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
    )
    op.create_index("ix_on_call_duties_facility_id", "on_call_duties", ["facility_id"])
    op.create_index("ix_on_call_duties_department_id", "on_call_duties", ["department_id"])
    op.create_index("ix_on_call_duties_staff_id", "on_call_duties", ["staff_id"])
    op.create_index("ix_on_call_duties_status", "on_call_duties", ["status"])

    # shift_swaps
    op.create_table(
        "shift_swaps",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=False),
        sa.Column("assignment_id", sa.String(36), sa.ForeignKey("shift_assignments.id"), nullable=False),
        sa.Column("requester_id", sa.String(36), sa.ForeignKey("staff_members.id"), nullable=False),
        sa.Column("replacement_id", sa.String(36), sa.ForeignKey("staff_members.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="REQUESTED"),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("approved_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("rejected_by", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("manager_note", sa.Text(), nullable=True),
    )
    op.create_index("ix_shift_swaps_facility_id", "shift_swaps", ["facility_id"])
    op.create_index("ix_shift_swaps_assignment_id", "shift_swaps", ["assignment_id"])
    op.create_index("ix_shift_swaps_requester_id", "shift_swaps", ["requester_id"])
    op.create_index("ix_shift_swaps_replacement_id", "shift_swaps", ["replacement_id"])
    op.create_index("ix_shift_swaps_status", "shift_swaps", ["status"])


def downgrade():
    op.drop_index("ix_shift_swaps_status", table_name="shift_swaps")
    op.drop_index("ix_shift_swaps_replacement_id", table_name="shift_swaps")
    op.drop_index("ix_shift_swaps_requester_id", table_name="shift_swaps")
    op.drop_index("ix_shift_swaps_assignment_id", table_name="shift_swaps")
    op.drop_index("ix_shift_swaps_facility_id", table_name="shift_swaps")
    op.drop_table("shift_swaps")

    op.drop_index("ix_on_call_duties_status", table_name="on_call_duties")
    op.drop_index("ix_on_call_duties_staff_id", table_name="on_call_duties")
    op.drop_index("ix_on_call_duties_department_id", table_name="on_call_duties")
    op.drop_index("ix_on_call_duties_facility_id", table_name="on_call_duties")
    op.drop_table("on_call_duties")

    op.drop_index("ix_leave_balances_year", table_name="leave_balances")
    op.drop_index("ix_leave_balances_staff_id", table_name="leave_balances")
    op.drop_index("ix_leave_balances_facility_id", table_name="leave_balances")
    op.drop_table("leave_balances")

    op.drop_index("ix_shift_assignments_status", table_name="shift_assignments")
    op.drop_index("ix_shift_assignments_assignment_date", table_name="shift_assignments")
    op.drop_index("ix_shift_assignments_staff_id", table_name="shift_assignments")
    op.drop_index("ix_shift_assignments_shift_id", table_name="shift_assignments")
    op.drop_index("ix_shift_assignments_department_id", table_name="shift_assignments")
    op.drop_index("ix_shift_assignments_facility_id", table_name="shift_assignments")
    op.drop_table("shift_assignments")

    op.drop_index("ix_shifts_enabled", table_name="shifts")
    op.drop_index("ix_shifts_code", table_name="shifts")
    op.drop_index("ix_shifts_department_id", table_name="shifts")
    op.drop_index("ix_shifts_facility_id", table_name="shifts")
    op.drop_table("shifts")
