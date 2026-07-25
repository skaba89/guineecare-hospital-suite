"""PDF generation service for the documents module (v1.2.0).

Each generator returns the PDF bytes. The caller (routes.py) is
responsible for streaming the response and writing the audit row.

Design choices:

- **ReportLab** (pure-Python, no system deps) — keeps the deployment
  footprint minimal vs WeasyPrint which needs cairo/pango shared libs.
- **Single-page optimized layout** — documents are short by nature
  (ordonnance ≤ 1 page, facture ≤ 2 pages). Multi-page support is
  handled by SimpleDocTemplate's automatic pagination.
- **Unicode-safe** — uses Helvetica which has decent Latin-1 coverage.
  Patient names with non-Latin characters are transliterated by the
  application layer if needed (out of scope for v1.2).
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from io import BytesIO
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER

# ── Brand palette ──────────────────────────────────────────────────────
# Calm medical palette — primary green (health), accent red (urgency).
NAVY = colors.HexColor("#1a3a5c")
GREEN = colors.HexColor("#2d7a4a")
LIGHT_GREY = colors.HexColor("#f4f4f4")
MID_GREY = colors.HexColor("#888888")
ACCENT_RED = colors.HexColor("#b00020")


# ── Styles ─────────────────────────────────────────────────────────────
def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle", parent=base["Title"],
            fontName="Helvetica-Bold", fontSize=18, leading=22,
            textColor=NAVY, alignment=TA_LEFT, spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "DocSubtitle", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, leading=12,
            textColor=MID_GREY, alignment=TA_LEFT, spaceAfter=8,
        ),
        "section": ParagraphStyle(
            "DocSection", parent=base["Heading2"],
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=GREEN, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "DocBody", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, leading=13,
            textColor=colors.black, alignment=TA_LEFT,
        ),
        "label": ParagraphStyle(
            "DocLabel", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9, leading=11,
            textColor=MID_GREY, alignment=TA_LEFT,
        ),
        "value": ParagraphStyle(
            "DocValue", parent=base["Normal"],
            fontName="Helvetica", fontSize=10, leading=12,
            textColor=colors.black, alignment=TA_LEFT,
        ),
        "footer": ParagraphStyle(
            "DocFooter", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=8, leading=10,
            textColor=MID_GREY, alignment=TA_CENTER,
        ),
        "signature_label": ParagraphStyle(
            "DocSigLabel", parent=base["Normal"],
            fontName="Helvetica-Bold", fontSize=9, leading=11,
            textColor=colors.black, alignment=TA_LEFT,
        ),
        "disclaimer": ParagraphStyle(
            "DocDisclaimer", parent=base["Normal"],
            fontName="Helvetica-Oblique", fontSize=8, leading=10,
            textColor=MID_GREY, alignment=TA_LEFT,
        ),
    }


STYLES = _build_styles()


def _format_date(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d/%m/%Y")


def _format_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%d/%m/%Y à %H:%M")


# ── Header / Footer factory ────────────────────────────────────────────
def _header_footer(canv, doc, facility_name: str, document_title: str, doc_ref: str):
    """Drawn on every page: header bar + footer with page number + doc ref."""
    canv.saveState()
    width, height = A4

    # ── Header bar ──
    canv.setFillColor(NAVY)
    canv.rect(0, height - 1.6 * cm, width, 1.6 * cm, fill=1, stroke=0)
    canv.setFillColor(colors.white)
    canv.setFont("Helvetica-Bold", 11)
    canv.drawString(1.5 * cm, height - 1.0 * cm, facility_name or "Établissement de santé")
    canv.setFont("Helvetica", 9)
    canv.drawRightString(width - 1.5 * cm, height - 1.0 * cm, document_title)

    # ── Footer ──
    canv.setStrokeColor(MID_GREY)
    canv.setLineWidth(0.3)
    canv.line(1.5 * cm, 1.3 * cm, width - 1.5 * cm, 1.3 * cm)
    canv.setFillColor(MID_GREY)
    canv.setFont("Helvetica", 8)
    canv.drawString(1.5 * cm, 0.8 * cm, f"Réf : {doc_ref}")
    canv.drawCentredString(width / 2.0, 0.8 * cm, "GuinéeCare Hospital Suite")
    canv.drawRightString(width - 1.5 * cm, 0.8 * cm, f"Page {doc.page}")
    canv.restoreState()


# ── Patient info block ─────────────────────────────────────────────────
def _patient_block(patient: Any) -> Table:
    """Two-column table with patient identification."""
    full_name = f"{patient.last_name} {patient.first_name}".strip()
    dob = _format_date(getattr(patient, "date_of_birth", None))
    gender = getattr(patient, "gender", None) or "—"
    gender_label = {"M": "Masculin", "F": "Féminin"}.get(gender, gender)
    phone = getattr(patient, "phone", None) or "—"
    address = getattr(patient, "address", None) or "—"

    data = [
        [Paragraph("Patient", STYLES["label"]), Paragraph(full_name, STYLES["value"]),
         Paragraph("N° dossier", STYLES["label"]), Paragraph(patient.patient_number, STYLES["value"])],
        [Paragraph("Date de naissance", STYLES["label"]), Paragraph(dob, STYLES["value"]),
         Paragraph("Sexe", STYLES["label"]), Paragraph(gender_label, STYLES["value"])],
        [Paragraph("Téléphone", STYLES["label"]), Paragraph(phone, STYLES["value"]),
         Paragraph("Adresse", STYLES["label"]), Paragraph(address, STYLES["value"])],
    ]
    t = Table(data, colWidths=[3.2 * cm, 5.5 * cm, 2.8 * cm, 5.0 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.2, colors.white),
    ]))
    return t


# ── Public generators ──────────────────────────────────────────────────
def generate_prescription_pdf(
    *,
    facility_name: str,
    patient: Any,
    prescription: Any,
    prescriber: Any,
) -> tuple[bytes, str, str]:
    """Generate an ordonnance PDF from a ClinicalNote (note_type=PRESCRIPTION).

    Returns (pdf_bytes, doc_ref, sha256_hex).
    """
    buf = BytesIO()
    doc_ref = f"ORD-{prescription.id[:8].upper()}"
    document_title = "Ordonnance médicale"

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=2.2 * cm, bottomMargin=1.8 * cm,
        title=f"Ordonnance — {patient.last_name} {patient.first_name}",
        author=facility_name,
    )

    story: list = []
    story.append(Paragraph("ORDONNANCE MÉDICALE", STYLES["title"]))
    story.append(Paragraph(
        f"Émise le {_format_datetime(prescription.created_at)}",
        STYLES["subtitle"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_patient_block(patient))
    story.append(Spacer(1, 6 * mm))

    # ── Prescriptions content ──
    story.append(Paragraph("Prescription", STYLES["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
    story.append(Spacer(1, 3 * mm))
    # The ClinicalNote.content is free-text; we render it line by line.
    for line in (prescription.content or "").splitlines():
        line = line.strip()
        if line:
            story.append(Paragraph(line, STYLES["body"]))
            story.append(Spacer(1, 2 * mm))

    story.append(Spacer(1, 10 * mm))

    # ── Signature block ──
    prescriber_name = "—"
    if prescriber is not None:
        prescriber_name = f"{prescriber.last_name} {prescriber.first_name}".strip()
    sig_data = [
        [Paragraph("Médecin prescripteur", STYLES["signature_label"]), ""],
        [Paragraph(prescriber_name, STYLES["value"]), ""],
        [Paragraph("Signature et cachet", STYLES["label"]), ""],
        [Spacer(1, 18 * mm), ""],
    ]
    sig_table = Table(sig_data, colWidths=[10 * cm, 6 * cm])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        "Document généré électroniquement par GuinéeCare. "
        "Conforme aux exigences réglementaires du Ministère de la Santé de Guinée. "
        "À présenter au pharmacien pour délivrance.",
        STYLES["disclaimer"],
    ))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
        onLaterPages=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
    )

    pdf_bytes = buf.getvalue()
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    return pdf_bytes, doc_ref, sha


def generate_imaging_report_pdf(
    *,
    facility_name: str,
    patient: Any,
    imaging_order: Any,
    imaging_result: Any,
    radiologist: Any,
) -> tuple[bytes, str, str]:
    """Generate a compte rendu d'imagerie PDF."""
    buf = BytesIO()
    doc_ref = f"IMG-{imaging_order.id[:8].upper()}"
    document_title = "Compte rendu d'imagerie"

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=2.2 * cm, bottomMargin=1.8 * cm,
        title=f"Compte rendu — {patient.last_name} {patient.first_name}",
        author=facility_name,
    )

    story: list = []
    story.append(Paragraph("COMPTE RENDU D'IMAGERIE", STYLES["title"]))
    story.append(Paragraph(
        f"Examen : {imaging_order.exam_type} — {imaging_order.body_region}",
        STYLES["subtitle"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_patient_block(patient))
    story.append(Spacer(1, 6 * mm))

    # ── Clinical context ──
    story.append(Paragraph("Information clinique", STYLES["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(imaging_order.clinical_info or "—", STYLES["body"]))
    story.append(Spacer(1, 5 * mm))

    # ── Findings ──
    if imaging_result is not None:
        story.append(Paragraph("Résultats / Constatations", STYLES["section"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(imaging_result.findings or "—", STYLES["body"]))
        story.append(Spacer(1, 5 * mm))

        story.append(Paragraph("Conclusion", STYLES["section"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(imaging_result.conclusion or "—", STYLES["body"]))
        story.append(Spacer(1, 5 * mm))

        if imaging_result.recommendation:
            story.append(Paragraph("Recommandations", STYLES["section"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(imaging_result.recommendation, STYLES["body"]))
            story.append(Spacer(1, 5 * mm))

    # ── Dates ──
    story.append(Paragraph("Dates clés", STYLES["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
    dates_data = [
        [Paragraph("Demande", STYLES["label"]), Paragraph(_format_datetime(imaging_order.ordered_at), STYLES["value"])],
        [Paragraph("Réalisation", STYLES["label"]), Paragraph(_format_datetime(imaging_order.performed_at), STYLES["value"])],
        [Paragraph("Validation", STYLES["label"]),
         Paragraph(_format_datetime(getattr(imaging_result, "validated_at", None) if imaging_result else None), STYLES["value"])],
    ]
    dates_table = Table(dates_data, colWidths=[4 * cm, 10 * cm])
    dates_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(dates_table)
    story.append(Spacer(1, 8 * mm))

    # ── Signature ──
    radio_name = "—"
    if radiologist is not None:
        radio_name = f"{radiologist.last_name} {radiologist.first_name}".strip()
    sig_data = [
        [Paragraph("Radiologue", STYLES["signature_label"])],
        [Paragraph(radio_name, STYLES["value"])],
        [Paragraph("Signature et cachet", STYLES["label"])],
        [Spacer(1, 18 * mm)],
    ]
    sig_table = Table(sig_data, colWidths=[10 * cm])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Document généré électroniquement par GuinéeCare. "
        "Le présent compte rendu ne peut être modifié qu'après signature d'un avenant.",
        STYLES["disclaimer"],
    ))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
        onLaterPages=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
    )

    pdf_bytes = buf.getvalue()
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    return pdf_bytes, doc_ref, sha


def generate_lab_result_pdf(
    *,
    facility_name: str,
    patient: Any,
    lab_order: Any,
    lab_test: Any,
    lab_result: Any,
    validator: Any,
) -> tuple[bytes, str, str]:
    """Generate a résultat de laboratoire PDF."""
    buf = BytesIO()
    doc_ref = f"LAB-{lab_order.id[:8].upper()}"
    document_title = "Résultat d'analyse de laboratoire"

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=2.2 * cm, bottomMargin=1.8 * cm,
        title=f"Résultat labo — {patient.last_name} {patient.first_name}",
        author=facility_name,
    )

    story: list = []
    story.append(Paragraph("RÉSULTAT D'ANALYSE DE LABORATOIRE", STYLES["title"]))
    story.append(Paragraph(
        f"Analyse : {lab_test.name} ({lab_test.code})",
        STYLES["subtitle"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_patient_block(patient))
    story.append(Spacer(1, 6 * mm))

    # ── Order info ──
    story.append(Paragraph("Information de la demande", STYLES["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
    info_data = [
        [Paragraph("Priorité", STYLES["label"]), Paragraph(lab_order.priority, STYLES["value"])],
        [Paragraph("Date de demande", STYLES["label"]),
         Paragraph(_format_datetime(lab_order.ordered_at), STYLES["value"])],
        [Paragraph("Type d'échantillon", STYLES["label"]),
         Paragraph(lab_test.sample_type or "—", STYLES["value"])],
        [Paragraph("Catégorie", STYLES["label"]),
         Paragraph(lab_test.category or "—", STYLES["value"])],
    ]
    info_table = Table(info_data, colWidths=[5 * cm, 9 * cm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 6 * mm))

    # ── Result ──
    if lab_result is not None:
        story.append(Paragraph("Résultat", STYLES["section"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
        result_data = [
            [Paragraph("Valeur", STYLES["label"]),
             Paragraph(lab_result.result_value, STYLES["value"])],
            [Paragraph("Interprétation", STYLES["label"]),
             Paragraph(lab_result.interpretation or "—", STYLES["value"])],
            [Paragraph("Statut", STYLES["label"]),
             Paragraph(lab_result.status, STYLES["value"])],
            [Paragraph("Saisi le", STYLES["label"]),
             Paragraph(_format_datetime(lab_result.entered_at), STYLES["value"])],
            [Paragraph("Validé le", STYLES["label"]),
             Paragraph(_format_datetime(lab_result.validated_at), STYLES["value"])],
        ]
        result_table = Table(result_data, colWidths=[5 * cm, 9 * cm])
        result_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
        ]))
        story.append(result_table)
        story.append(Spacer(1, 5 * mm))

        # Critical value warning
        if lab_result.interpretation and "CRITIQUE" in lab_result.interpretation.upper():
            story.append(Spacer(1, 3 * mm))
            warning = Table(
                [[Paragraph(
                    "⚠ VALEUR CRITIQUE — Notifier immédiatement le médecin prescripteur.",
                    ParagraphStyle("Warn", parent=STYLES["body"],
                                   textColor=ACCENT_RED, fontName="Helvetica-Bold"),
                )]],
                colWidths=[14 * cm],
            )
            warning.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#ffe0e0")),
                ("BOX", (0, 0), (-1, -1), 0.5, ACCENT_RED),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(warning)
            story.append(Spacer(1, 5 * mm))

    # ── Validator signature ──
    val_name = "—"
    if validator is not None:
        val_name = f"{validator.last_name} {validator.first_name}".strip()
    sig_data = [
        [Paragraph("Validé par", STYLES["signature_label"])],
        [Paragraph(val_name, STYLES["value"])],
        [Paragraph("Signature", STYLES["label"])],
        [Spacer(1, 15 * mm)],
    ]
    sig_table = Table(sig_data, colWidths=[10 * cm])
    sig_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(sig_table)

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        "Document généré électroniquement par GuinéeCare. "
        "Les résultats non validés ne doivent pas servir de base à une décision clinique.",
        STYLES["disclaimer"],
    ))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
        onLaterPages=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
    )

    pdf_bytes = buf.getvalue()
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    return pdf_bytes, doc_ref, sha


def generate_invoice_pdf(
    *,
    facility_name: str,
    patient: Any,
    invoice: Any,
    payments: list,
) -> tuple[bytes, str, str]:
    """Generate a facture PDF."""
    buf = BytesIO()
    doc_ref = invoice.invoice_number or f"INV-{invoice.id[:8].upper()}"
    document_title = "Facture patient"

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=2.2 * cm, bottomMargin=1.8 * cm,
        title=f"Facture — {patient.last_name} {patient.first_name}",
        author=facility_name,
    )

    story: list = []
    story.append(Paragraph("FACTURE PATIENT", STYLES["title"]))
    story.append(Paragraph(
        f"N° {doc_ref} — Émise le {_format_datetime(invoice.created_at)}",
        STYLES["subtitle"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_patient_block(patient))
    story.append(Spacer(1, 6 * mm))

    # ── Description ──
    if invoice.description:
        story.append(Paragraph("Description", STYLES["section"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(invoice.description, STYLES["body"]))
        story.append(Spacer(1, 5 * mm))

    # ── Amounts summary ──
    story.append(Paragraph("Récapitulatif des montants", STYLES["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
    story.append(Spacer(1, 2 * mm))

    def _fmt(x: float) -> str:
        return f"{x:,.0f} GNF".replace(",", " ")

    amounts_data = [
        [Paragraph("Montant net", STYLES["label"]), Paragraph(_fmt(invoice.net_amount), STYLES["value"])],
        [Paragraph("Déjà payé", STYLES["label"]), Paragraph(_fmt(invoice.paid_amount), STYLES["value"])],
        [Paragraph("Reste à charge", STYLES["label"]),
         Paragraph(_fmt(invoice.balance_due), ParagraphStyle(
             "BalanceDue", parent=STYLES["value"],
             fontName="Helvetica-Bold",
             textColor=ACCENT_RED if invoice.balance_due > 0 else GREEN,
         ))],
        [Paragraph("Statut", STYLES["label"]), Paragraph(invoice.status, STYLES["value"])],
    ]
    amounts_table = Table(amounts_data, colWidths=[5 * cm, 9 * cm])
    amounts_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
    ]))
    story.append(amounts_table)
    story.append(Spacer(1, 6 * mm))

    # ── Payments detail ──
    if payments:
        story.append(Paragraph("Détail des paiements", STYLES["section"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
        story.append(Spacer(1, 2 * mm))
        pay_data = [[
            Paragraph("Date", STYLES["label"]),
            Paragraph("Mode", STYLES["label"]),
            Paragraph("Montant", STYLES["label"]),
            Paragraph("Statut", STYLES["label"]),
        ]]
        for p in payments:
            pay_data.append([
                Paragraph(_format_datetime(p.received_at), STYLES["value"]),
                Paragraph(p.payment_method, STYLES["value"]),
                Paragraph(_fmt(p.amount), STYLES["value"]),
                Paragraph(p.status, STYLES["value"]),
            ])
        pay_table = Table(pay_data, colWidths=[4.5 * cm, 3.5 * cm, 3.5 * cm, 2.5 * cm])
        pay_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, -1), 0.2, MID_GREY),
        ]))
        story.append(pay_table)
        story.append(Spacer(1, 8 * mm))

    # ── Footer / mention ──
    story.append(Paragraph(
        "Document généré électroniquement par GuinéeCare. "
        "Conforme aux exigences fiscales OHADA. "
        "Cette facture doit être conservée pendant 10 ans.",
        STYLES["disclaimer"],
    ))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
        onLaterPages=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
    )

    pdf_bytes = buf.getvalue()
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    return pdf_bytes, doc_ref, sha


# ============================================================================
# v2.4.0 — Phase 4 : Reçu de paiement PDF
# ============================================================================

def generate_payment_receipt_pdf(
    *,
    facility_name: str,
    patient: Any,
    payment: Any,
    invoice: Any,
) -> tuple[bytes, str, str]:
    """Génère un PDF de reçu de paiement.

    Retourne (pdf_bytes, doc_ref, sha256).
    doc_ref = "REC-{payment.id[:8].upper()}"
    """
    buf = BytesIO()
    doc_ref = f"REC-{payment.id[:8].upper()}"
    document_title = "Reçu de paiement"

    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=2.2 * cm, bottomMargin=1.8 * cm,
        title=f"Reçu — {patient.last_name} {patient.first_name}",
        author=facility_name,
    )

    story: list = []
    story.append(Paragraph("REÇU DE PAIEMENT", STYLES["title"]))
    story.append(Paragraph(
        f"N° {doc_ref} — Émis le {_format_datetime(payment.received_at)}",
        STYLES["subtitle"],
    ))
    story.append(Spacer(1, 4 * mm))
    story.append(_patient_block(patient))
    story.append(Spacer(1, 6 * mm))

    # ── Payment details ──
    def _fmt(x: float) -> str:
        return f"{x:,.0f} GNF".replace(",", " ")

    story.append(Paragraph("Détails du paiement", STYLES["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
    story.append(Spacer(1, 2 * mm))

    details_data = [
        [Paragraph("Reçu N°", STYLES["label"]), Paragraph(doc_ref, STYLES["value"])],
        [Paragraph("Facture N°", STYLES["label"]),
         Paragraph(invoice.invoice_number if invoice else "—", STYLES["value"])],
        [Paragraph("Date paiement", STYLES["label"]),
         Paragraph(_format_datetime(payment.received_at), STYLES["value"])],
        [Paragraph("Mode de paiement", STYLES["label"]),
         Paragraph(payment.payment_method, STYLES["value"])],
        [Paragraph("Statut", STYLES["label"]),
         Paragraph(payment.status, STYLES["value"])],
    ]
    details_table = Table(details_data, colWidths=[5 * cm, 9 * cm])
    details_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.2, MID_GREY),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 8 * mm))

    # ── Montant payé (encadré) ──
    story.append(Paragraph("Montant payé", STYLES["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
    story.append(Spacer(1, 2 * mm))
    amount_data = [[
        Paragraph("Montant reçu", STYLES["label"]),
        Paragraph(_fmt(payment.amount), ParagraphStyle(
            "AmountPaid", parent=STYLES["value"],
            fontName="Helvetica-Bold", fontSize=16,
            textColor=GREEN,
        )),
    ]]
    amount_table = Table(amount_data, colWidths=[5 * cm, 9 * cm])
    amount_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GREY),
        ("BOX", (0, 0), (-1, -1), 1, GREEN),
    ]))
    story.append(amount_table)
    story.append(Spacer(1, 8 * mm))

    # ── Solde restant sur la facture ──
    if invoice:
        balance_data = [
            [Paragraph("Montant facture", STYLES["label"]),
             Paragraph(_fmt(invoice.net_amount), STYLES["value"])],
            [Paragraph("Total payé", STYLES["label"]),
             Paragraph(_fmt(invoice.paid_amount), STYLES["value"])],
            [Paragraph("Reste à charge", STYLES["label"]),
             Paragraph(_fmt(invoice.balance_due),
                       ParagraphStyle("BalanceDue", parent=STYLES["value"],
                                      fontName="Helvetica-Bold",
                                      textColor=ACCENT_RED if invoice.balance_due > 0 else GREEN))],
        ]
        balance_table = Table(balance_data, colWidths=[5 * cm, 9 * cm])
        balance_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LINEBELOW", (0, 0), (-1, -1), 0.2, MID_GREY),
        ]))
        story.append(balance_table)
        story.append(Spacer(1, 8 * mm))

    # ── Footer ──
    story.append(Paragraph(
        "Ce reçu atteste du paiement effectué. "
        "Conservez-le pour vos enregistrements. "
        "Document généré électroniquement par GuinéeCare.",
        STYLES["disclaimer"],
    ))

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
        onLaterPages=lambda c, d: _header_footer(c, d, facility_name, document_title, doc_ref),
    )

    pdf_bytes = buf.getvalue()
    sha = hashlib.sha256(pdf_bytes).hexdigest()
    return pdf_bytes, doc_ref, sha
