"""add documents_generated audit table (v1.2.0)

Revision ID: 0016_documents
Revises: 0015_user_profile
Create Date: 2026-06-21

Adds the `documents_generated` table — audit trail of every PDF
generated server-side via the new `/api/v1/documents/*/{id}/pdf`
endpoints (v1.2.0).

Design choices:

- We persist metadata only (who, when, what, sha256), not the PDF bytes
  themselves. Storing bytes would bloat the database and raise PII
  retention concerns; the SHA-256 is enough to prove that two
  generations produced identical bytes.
- Indexes on `facility_id`, `document_type`, `source_id`, `patient_id`,
  `generated_at` cover the common audit-listing queries.
"""
from alembic import op
import sqlalchemy as sa


revision = "0016_documents"
down_revision = "0015_user_profile"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "documents_generated",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("facility_id", sa.String(36), sa.ForeignKey("facilities.id"), nullable=False),
        sa.Column("document_type", sa.String(32), nullable=False),
        sa.Column("source_id", sa.String(36), nullable=False),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patients.id"), nullable=True),
        sa.Column("generated_by", sa.String(36), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("file_size_bytes", sa.String(20), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
    )
    op.create_index("ix_documents_generated_facility_id", "documents_generated", ["facility_id"])
    op.create_index("ix_documents_generated_document_type", "documents_generated", ["document_type"])
    op.create_index("ix_documents_generated_source_id", "documents_generated", ["source_id"])
    op.create_index("ix_documents_generated_patient_id", "documents_generated", ["patient_id"])
    op.create_index("ix_documents_generated_generated_at", "documents_generated", ["generated_at"])


def downgrade():
    op.drop_index("ix_documents_generated_generated_at", table_name="documents_generated")
    op.drop_index("ix_documents_generated_patient_id", table_name="documents_generated")
    op.drop_index("ix_documents_generated_source_id", table_name="documents_generated")
    op.drop_index("ix_documents_generated_document_type", table_name="documents_generated")
    op.drop_index("ix_documents_generated_facility_id", table_name="documents_generated")
    op.drop_table("documents_generated")
