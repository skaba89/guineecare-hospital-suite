"""add imaging, surgery, quality, and reporting modules

Revision ID: 0008_imaging_surgery_quality_reporting
Revises: 0006_maternity
Create Date: 2026-06-14
"""

from alembic import op
import sqlalchemy as sa


revision = "0008_imaging_surgery_quality_reporting"
down_revision = "0006_maternity"
branch_labels = None
depends_on = None


def upgrade():
    # ── Imaging Orders ────────────────────────────────────────────────
    op.create_table(
        "imaging_orders",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("requesting_doctor_id", sa.String(length=36), nullable=True),
        sa.Column("exam_type", sa.String(length=100), nullable=False),
        sa.Column("body_region", sa.String(length=255), nullable=False),
        sa.Column("clinical_info", sa.Text(), nullable=True),
        sa.Column("urgency", sa.String(length=50), nullable=False, server_default="ROUTINE"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="PENDING"),
        sa.Column("ordered_at", sa.DateTime(), nullable=False),
        sa.Column("performed_at", sa.DateTime(), nullable=True),
        sa.Column("reported_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_imaging_orders_facility_id", "imaging_orders", ["facility_id"])
    op.create_index("ix_imaging_orders_patient_id", "imaging_orders", ["patient_id"])
    op.create_index("ix_imaging_orders_requesting_doctor_id", "imaging_orders", ["requesting_doctor_id"])

    # ── Imaging Results ───────────────────────────────────────────────
    op.create_table(
        "imaging_results",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("radiologist_id", sa.String(length=36), nullable=True),
        sa.Column("findings", sa.Text(), nullable=True),
        sa.Column("conclusion", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_imaging_results_facility_id", "imaging_results", ["facility_id"])
    op.create_index("ix_imaging_results_order_id", "imaging_results", ["order_id"])
    op.create_index("ix_imaging_results_patient_id", "imaging_results", ["patient_id"])

    # ── Operating Rooms ───────────────────────────────────────────────
    op.create_table(
        "operating_rooms",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("room_type", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="AVAILABLE"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_operating_rooms_facility_id", "operating_rooms", ["facility_id"])
    op.create_index("ix_operating_rooms_code", "operating_rooms", ["code"])

    # ── Surgery Schedules ─────────────────────────────────────────────
    op.create_table(
        "surgery_schedules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("operating_room_id", sa.String(length=36), nullable=True),
        sa.Column("surgeon_id", sa.String(length=36), nullable=True),
        sa.Column("anesthesiologist_id", sa.String(length=36), nullable=True),
        sa.Column("procedure_name", sa.String(length=255), nullable=False),
        sa.Column("procedure_code", sa.String(length=50), nullable=True),
        sa.Column("laterality", sa.String(length=20), nullable=True),
        sa.Column("urgency", sa.String(length=50), nullable=False, server_default="PLANNED"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="SCHEDULED"),
        sa.Column("scheduled_date", sa.DateTime(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_surgery_schedules_facility_id", "surgery_schedules", ["facility_id"])
    op.create_index("ix_surgery_schedules_patient_id", "surgery_schedules", ["patient_id"])
    op.create_index("ix_surgery_schedules_operating_room_id", "surgery_schedules", ["operating_room_id"])
    op.create_index("ix_surgery_schedules_surgeon_id", "surgery_schedules", ["surgeon_id"])

    # ── Surgery Team Members ──────────────────────────────────────────
    op.create_table(
        "surgery_team_members",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("schedule_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("role", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_surgery_team_members_schedule_id", "surgery_team_members", ["schedule_id"])
    op.create_index("ix_surgery_team_members_user_id", "surgery_team_members", ["user_id"])

    # ── Surgery Reports ───────────────────────────────────────────────
    op.create_table(
        "surgery_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("schedule_id", sa.String(length=36), nullable=False),
        sa.Column("patient_id", sa.String(length=36), nullable=False),
        sa.Column("surgeon_id", sa.String(length=36), nullable=True),
        sa.Column("operative_findings", sa.Text(), nullable=True),
        sa.Column("procedure_performed", sa.Text(), nullable=True),
        sa.Column("complications", sa.Text(), nullable=True),
        sa.Column("specimens", sa.Text(), nullable=True),
        sa.Column("blood_loss", sa.String(length=100), nullable=True),
        sa.Column("anesthesia_type", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_surgery_reports_facility_id", "surgery_reports", ["facility_id"])
    op.create_index("ix_surgery_reports_schedule_id", "surgery_reports", ["schedule_id"])
    op.create_index("ix_surgery_reports_patient_id", "surgery_reports", ["patient_id"])

    # ── Quality Indicators ────────────────────────────────────────────
    op.create_table(
        "quality_indicators",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("target_value", sa.String(length=50), nullable=True),
        sa.Column("frequency", sa.String(length=50), nullable=False, server_default="MONTHLY"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_quality_indicators_facility_id", "quality_indicators", ["facility_id"])
    op.create_index("ix_quality_indicators_code", "quality_indicators", ["code"])

    # ── Quality Measurements ──────────────────────────────────────────
    op.create_table(
        "quality_measurements",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("indicator_id", sa.String(length=36), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("value", sa.String(length=100), nullable=False),
        sa.Column("numerator", sa.String(length=100), nullable=True),
        sa.Column("denominator", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_quality_measurements_facility_id", "quality_measurements", ["facility_id"])
    op.create_index("ix_quality_measurements_indicator_id", "quality_measurements", ["indicator_id"])

    # ── Incident Reports ──────────────────────────────────────────────
    op.create_table(
        "incident_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("reported_by", sa.String(length=36), nullable=True),
        sa.Column("patient_id", sa.String(length=36), nullable=True),
        sa.Column("incident_date", sa.DateTime(), nullable=False),
        sa.Column("incident_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False, server_default="MINOR"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("immediate_actions", sa.Text(), nullable=True),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column("corrective_actions", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="REPORTED"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_incident_reports_facility_id", "incident_reports", ["facility_id"])
    op.create_index("ix_incident_reports_patient_id", "incident_reports", ["patient_id"])

    # ── National Reports ──────────────────────────────────────────────
    op.create_table(
        "national_reports",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("report_type", sa.String(length=100), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("total_admissions", sa.String(length=20), nullable=True),
        sa.Column("total_discharges", sa.String(length=20), nullable=True),
        sa.Column("total_deaths", sa.String(length=20), nullable=True),
        sa.Column("total_births", sa.String(length=20), nullable=True),
        sa.Column("total_surgeries", sa.String(length=20), nullable=True),
        sa.Column("total_emergency_visits", sa.String(length=20), nullable=True),
        sa.Column("bed_occupancy_rate", sa.String(length=20), nullable=True),
        sa.Column("average_stay_days", sa.String(length=20), nullable=True),
        sa.Column("disease_distribution", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="DRAFT"),
        sa.Column("submitted_by", sa.String(length=36), nullable=True),
        sa.Column("submitted_at", sa.DateTime(), nullable=True),
        sa.Column("validated_by", sa.String(length=36), nullable=True),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_national_reports_facility_id", "national_reports", ["facility_id"])

    # ── Epidemic Alerts ───────────────────────────────────────────────
    op.create_table(
        "epidemic_alerts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("disease_name", sa.String(length=255), nullable=False),
        sa.Column("case_count", sa.String(length=20), nullable=False),
        sa.Column("threshold_exceeded", sa.String(length=10), nullable=False, server_default="YES"),
        sa.Column("alert_level", sa.String(length=50), nullable=False, server_default="WARNING"),
        sa.Column("region", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("measures_taken", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="ACTIVE"),
        sa.Column("reported_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_epidemic_alerts_facility_id", "epidemic_alerts", ["facility_id"])

    # ── Health Statistics ─────────────────────────────────────────────
    op.create_table(
        "health_statistics",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("facility_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=False),
        sa.Column("metric_name", sa.String(length=255), nullable=False),
        sa.Column("metric_value", sa.String(length=100), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_health_statistics_facility_id", "health_statistics", ["facility_id"])


def downgrade():
    op.drop_table("health_statistics")
    op.drop_table("epidemic_alerts")
    op.drop_table("national_reports")
    op.drop_table("incident_reports")
    op.drop_table("quality_measurements")
    op.drop_table("quality_indicators")
    op.drop_table("surgery_reports")
    op.drop_table("surgery_team_members")
    op.drop_table("surgery_schedules")
    op.drop_table("operating_rooms")
    op.drop_table("imaging_results")
    op.drop_table("imaging_orders")
