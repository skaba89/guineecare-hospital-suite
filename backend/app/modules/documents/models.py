"""Models for the documents module (v1.2.0).

A single table `documents_generated` records every PDF generated server-side
for audit purposes. The actual PDF bytes are NOT persisted — they are
regenerated on demand from the source data. Storing bytes would balloon
the database and raise PII retention concerns; the audit log entry alone
is sufficient to answer "who printed this document and when?".
"""
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, Text

from app.core.datetime import utcnow
from app.db.base import Base


class DocumentGenerated(Base):
    """Audit trail of every PDF generated server-side.

    One row per successful `/api/v1/documents/*/{id}/pdf` call. Failed
    generations (404, 403, validation errors) are NOT logged here — they
    are logged via the standard audit_logs mechanism instead.
    """
    __tablename__ = "documents_generated"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    facility_id = Column(String(36), ForeignKey("facilities.id"), nullable=False, index=True)
    document_type = Column(String(32), nullable=False, index=True)
    # PRESCRIPTION, IMAGING_REPORT, LAB_RESULT, INVOICE
    source_id = Column(String(36), nullable=False, index=True)
    # ID of the source resource (clinical_note.id, imaging_order.id, etc.)
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=True, index=True)
    generated_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    generated_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    file_size_bytes = Column(String(20), nullable=True)
    # Stored as string to avoid integer overflow on weird edge cases.
    checksum_sha256 = Column(String(64), nullable=True)
    # SHA-256 of the PDF bytes — allows duplicate detection without
    # storing the bytes themselves.
    note = Column(Text, nullable=True)
    # Free-form note (e.g. "regenerated after correction").
