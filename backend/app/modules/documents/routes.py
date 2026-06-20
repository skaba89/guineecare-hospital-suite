"""HTTP routes for the documents module (v1.2.0).

Four endpoints, one per document type:

- `GET /api/v1/documents/prescriptions/{clinical_note_id}/pdf`
- `GET /api/v1/documents/imaging-reports/{imaging_order_id}/pdf`
- `GET /api/v1/documents/lab-results/{lab_order_id}/pdf`
- `GET /api/v1/documents/invoices/{invoice_id}/pdf`

All endpoints:
- Stream the PDF bytes back as `application/pdf` (inline disposition by
  default — set `?download=1` to force `Content-Disposition: attachment`).
- Verify facility isolation (`tenant_query` + `enforce_facility_access`).
- Write an audit row in `documents_generated` after successful generation.
- Journal the action in the standard `audit_logs` table.
- Require the corresponding `*.read` permission on the source resource.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.tenant import enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.audit.service import audit_log
from app.modules.billing.models import Invoice, Payment
from app.modules.clinical.models import ClinicalNote
from app.modules.documents.models import DocumentGenerated
from app.modules.documents.service import (
    generate_imaging_report_pdf,
    generate_invoice_pdf,
    generate_lab_result_pdf,
    generate_prescription_pdf,
)
from app.modules.facilities.models import Facility
from app.modules.imaging.models import ImagingOrder, ImagingResult
from app.modules.laboratory.models import LabOrder, LabResult, LabTest
from app.modules.patients.models import Patient
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/documents", tags=["documents"])


# ── Helpers ────────────────────────────────────────────────────────────
def _facility_name(db: Session, facility_id: str) -> str:
    fac = db.query(Facility).filter(Facility.id == facility_id).first()
    return fac.name if fac else "Établissement de santé"


def _record_generation(
    db: Session,
    *,
    facility_id: str,
    document_type: str,
    source_id: str,
    patient_id: str | None,
    user: User,
    pdf_bytes: bytes,
    doc_ref: str,
    sha256: str,
):
    """Persist the audit row + journal entries. The audit_log() call
    commits internally; we let it own the commit to avoid double-write."""
    row = DocumentGenerated(
        facility_id=facility_id,
        document_type=document_type,
        source_id=source_id,
        patient_id=patient_id,
        generated_by=user.id,
        file_size_bytes=str(len(pdf_bytes)),
        checksum_sha256=sha256,
        note=doc_ref,
    )
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=user.id,
        action_name=f"document.{document_type.lower()}_generated",
        entity_type="document",
        entity_id=row.id,
        level="IMPORTANT",
    )
    # audit_log commits internally — this also flushes the activity row above.
    audit_log(
        db=db,
        action=f"document.{document_type.lower()}_generated",
        user=user,
        resource_type="document",
        resource_id=row.id,
        facility_id=facility_id,
        status_code=200,
        payload={
            "document_type": document_type,
            "source_id": source_id,
            "patient_id": patient_id,
            "doc_ref": doc_ref,
            "file_size_bytes": len(pdf_bytes),
            "sha256": sha256,
        },
    )


def _build_response(
    pdf_bytes: bytes, doc_ref: str, download: bool
) -> Response:
    filename = f"{doc_ref}.pdf"
    disposition = "attachment" if download else "inline"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{disposition}; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "X-Document-Ref": doc_ref,
        },
    )


# ── 1. Prescription PDF ────────────────────────────────────────────────
@router.get(
    "/prescriptions/{clinical_note_id}/pdf",
    summary="Générer le PDF d'une ordonnance",
    description=(
        "Génère un PDF d'ordonnance médicale à partir d'une `ClinicalNote` "
        "dont le `note_type` est `PRESCRIPTION`. Le PDF est renvoyé en flux "
        "(media type `application/pdf`). Par défaut le PDF s'affiche en "
        "inline dans le navigateur ; passer `?download=1` force le téléchargement."
    ),
    response_class=Response,
)
def generate_prescription(
    clinical_note_id: str,
    download: bool = Query(False, description="Forcer le téléchargement (attachment)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    note = db.query(ClinicalNote).filter(ClinicalNote.id == clinical_note_id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Clinical note not found")
    if (note.note_type or "").upper() != "PRESCRIPTION":
        raise HTTPException(
            status_code=400,
            detail=f"La note {clinical_note_id} n'est pas de type PRESCRIPTION "
                   f"(type actuel : {note.note_type})",
        )
    enforce_facility_access(current_user, note.facility_id)

    patient = db.query(Patient).filter(Patient.id == note.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    prescriber = db.query(User).filter(User.id == note.created_by).first() if note.created_by else None

    pdf_bytes, doc_ref, sha = generate_prescription_pdf(
        facility_name=_facility_name(db, note.facility_id),
        patient=patient,
        prescription=note,
        prescriber=prescriber,
    )
    _record_generation(
        db,
        facility_id=note.facility_id,
        document_type="PRESCRIPTION",
        source_id=note.id,
        patient_id=patient.id,
        user=current_user,
        pdf_bytes=pdf_bytes,
        doc_ref=doc_ref,
        sha256=sha,
    )
    return _build_response(pdf_bytes, doc_ref, download)


# ── 2. Imaging report PDF ──────────────────────────────────────────────
@router.get(
    "/imaging-reports/{imaging_order_id}/pdf",
    summary="Générer le PDF d'un compte rendu d'imagerie",
    description=(
        "Génère un PDF de compte rendu d'imagerie à partir d'une `ImagingOrder` "
        "et de son `ImagingResult` associé. Si aucun résultat n'existe encore, "
        "le PDF est généré avec les informations disponibles (demande seule)."
    ),
    response_class=Response,
)
def generate_imaging_report(
    imaging_order_id: str,
    download: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("imaging.read")),
):
    order = db.query(ImagingOrder).filter(ImagingOrder.id == imaging_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Imaging order not found")
    enforce_facility_access(current_user, order.facility_id)

    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    result = (
        db.query(ImagingResult)
        .filter(ImagingResult.order_id == order.id)
        .order_by(ImagingResult.created_at.desc())
        .first()
    )
    radiologist = (
        db.query(User).filter(User.id == result.radiologist_id).first()
        if result and result.radiologist_id else None
    )

    pdf_bytes, doc_ref, sha = generate_imaging_report_pdf(
        facility_name=_facility_name(db, order.facility_id),
        patient=patient,
        imaging_order=order,
        imaging_result=result,
        radiologist=radiologist,
    )
    _record_generation(
        db,
        facility_id=order.facility_id,
        document_type="IMAGING_REPORT",
        source_id=order.id,
        patient_id=patient.id,
        user=current_user,
        pdf_bytes=pdf_bytes,
        doc_ref=doc_ref,
        sha256=sha,
    )
    return _build_response(pdf_bytes, doc_ref, download)


# ── 3. Lab result PDF ──────────────────────────────────────────────────
@router.get(
    "/lab-results/{lab_order_id}/pdf",
    summary="Générer le PDF d'un résultat de laboratoire",
    description=(
        "Génère un PDF de résultat d'analyse de laboratoire à partir d'une "
        "`LabOrder` et de son `LabResult` associé. Si le résultat n'est pas "
        "encore validé, le PDF mentionne explicitement cette limite "
        "(réservé à la décision clinique)."
    ),
    response_class=Response,
)
def generate_lab_result(
    lab_order_id: str,
    download: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("lab.read")),
):
    order = db.query(LabOrder).filter(LabOrder.id == lab_order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Lab order not found")
    enforce_facility_access(current_user, order.facility_id)

    patient = db.query(Patient).filter(Patient.id == order.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    test = db.query(LabTest).filter(LabTest.id == order.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Lab test not found")
    result = (
        db.query(LabResult)
        .filter(LabResult.order_id == order.id)
        .order_by(LabResult.entered_at.desc())
        .first()
    )
    validator = (
        db.query(User).filter(User.id == result.validated_by).first()
        if result and result.validated_by else None
    )

    pdf_bytes, doc_ref, sha = generate_lab_result_pdf(
        facility_name=_facility_name(db, order.facility_id),
        patient=patient,
        lab_order=order,
        lab_test=test,
        lab_result=result,
        validator=validator,
    )
    _record_generation(
        db,
        facility_id=order.facility_id,
        document_type="LAB_RESULT",
        source_id=order.id,
        patient_id=patient.id,
        user=current_user,
        pdf_bytes=pdf_bytes,
        doc_ref=doc_ref,
        sha256=sha,
    )
    return _build_response(pdf_bytes, doc_ref, download)


# ── 4. Invoice PDF ─────────────────────────────────────────────────────
@router.get(
    "/invoices/{invoice_id}/pdf",
    summary="Générer le PDF d'une facture",
    description=(
        "Génère un PDF de facture patient à partir d'une `Invoice` et de ses "
        "`Payment` associés. Le PDF inclut le détail des montants (net, payé, "
        "reste à charge) et la liste des paiements encaissés."
    ),
    response_class=Response,
)
def generate_invoice(
    invoice_id: str,
    download: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    enforce_facility_access(current_user, invoice.facility_id)

    patient = db.query(Patient).filter(Patient.id == invoice.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    payments = (
        db.query(Payment)
        .filter(Payment.invoice_id == invoice.id)
        .order_by(Payment.received_at.desc())
        .all()
    )

    pdf_bytes, doc_ref, sha = generate_invoice_pdf(
        facility_name=_facility_name(db, invoice.facility_id),
        patient=patient,
        invoice=invoice,
        payments=payments,
    )
    _record_generation(
        db,
        facility_id=invoice.facility_id,
        document_type="INVOICE",
        source_id=invoice.id,
        patient_id=patient.id,
        user=current_user,
        pdf_bytes=pdf_bytes,
        doc_ref=doc_ref,
        sha256=sha,
    )
    return _build_response(pdf_bytes, doc_ref, download)


# ── 5. Audit listing ───────────────────────────────────────────────────
@router.get(
    "/audit",
    summary="Lister les documents générés (audit trail)",
    description=(
        "Renvoie la liste paginée des PDF générés par l'utilisateur courant "
        "(ou par tous les utilisateurs de l'établissement si SUPER_ADMIN/ADMIN). "
        "Utile pour répondre à la question « qui a imprimé ce document et quand ? »."
    ),
)
def list_documents_audit(
    document_type: str | None = Query(None, description="Filtre par type de document"),
    patient_id: str | None = Query(None, description="Filtre par patient"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=5, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical.read")),
):
    q = db.query(DocumentGenerated)
    # SUPER_ADMIN sees all facilities; ADMIN sees their facility only;
    # all other roles see their facility only.
    if current_user.role != "SUPER_ADMIN":
        q = q.filter(DocumentGenerated.facility_id == current_user.facility_id)
    if document_type:
        q = q.filter(DocumentGenerated.document_type == document_type)
    if patient_id:
        q = q.filter(DocumentGenerated.patient_id == patient_id)
    total = q.count()
    rows = (
        q.order_by(DocumentGenerated.generated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "data": rows,
        "total": total,
        "page": page,
        "page_size": page_size,
        "message": "documents audit list",
    }
