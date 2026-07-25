"""Global search service (v1.2.0).

LIKE-based search across patients, lab orders, imaging orders, and
invoices. Returns categorized results capped at `limit_per_category`
rows per resource type.

Performance note: this service relies on the indexes already in place
on `patient_number`, `first_name`, `last_name`, `invoice_number`,
`code`, etc. For >100k rows per table, consider adding a real full-text
search backend (PostgreSQL tsvector + GIN, or Meilisearch).
"""
from __future__ import annotations

import re
from collections import OrderedDict
from typing import Any

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.tenant import tenant_query
from app.modules.billing.models import Invoice
from app.modules.clinical.models import ClinicalNote
from app.modules.imaging.models import ImagingOrder
from app.modules.laboratory.models import LabOrder, LabTest
from app.modules.patients.models import Patient
from app.modules.users.models import User

# Prefix → resource type mapping (for explicit `PAT-xxx` style searches)
PREFIX_MAP: OrderedDict[str, str] = OrderedDict([
    ("PAT-", "patient"),
    ("INV-", "invoice"),
    ("LAB-", "lab_order"),
    ("IMG-", "imaging_order"),
])


def _normalize(s: str) -> str:
    """Lowercase + collapse whitespace + strip accents (basic).

    For full accent folding we'd use `unicodedata.normalize('NFKD', ...)`
    but this is sufficient for the pilote volume and keeps the code simple.
    """
    if not s:
        return ""
    return re.sub(r"\s+", " ", s).strip().lower()


def search_patients(
    db: Session, current_user: User, q: str, limit: int
) -> list[dict[str, Any]]:
    pattern = f"%{q}%"
    rows = (
        tenant_query(db, Patient, current_user)
        .filter(
            or_(
                Patient.first_name.ilike(pattern),
                Patient.last_name.ilike(pattern),
                Patient.patient_number.ilike(pattern),
                Patient.phone.ilike(pattern),
                Patient.national_id.ilike(pattern),
            )
        )
        .order_by(Patient.last_name.asc(), Patient.first_name.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            "resource_type": "patient",
            "id": p.id,
            "label": f"{p.last_name} {p.first_name}".strip(),
            "subtitle": f"N° {p.patient_number}",
            "url": f"/patients/{p.id}",
        }
        for p in rows
    ]


def search_lab_orders(
    db: Session, current_user: User, q: str, limit: int
) -> list[dict[str, Any]]:
    pattern = f"%{q}%"
    # Join LabTest to allow searching by test name/code
    rows = (
        tenant_query(db, LabOrder, current_user)
        .join(LabTest, LabTest.id == LabOrder.test_id, isouter=True)
        .filter(
            or_(
                LabOrder.id.ilike(pattern),
                LabTest.name.ilike(pattern),
                LabTest.code.ilike(pattern),
            )
        )
        .order_by(LabOrder.ordered_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for o in rows:
        test = db.query(LabTest).filter(LabTest.id == o.test_id).first()
        label = test.name if test else "Analyse"
        out.append({
            "resource_type": "lab_order",
            "id": o.id,
            "label": f"Labo — {label}",
            "subtitle": f"{o.priority} · {o.status} · {o.ordered_at.strftime('%d/%m/%Y') if o.ordered_at else '—'}",
            "url": f"/laboratory?order={o.id}",
            "patient_id": o.patient_id,
        })
    return out


def search_imaging_orders(
    db: Session, current_user: User, q: str, limit: int
) -> list[dict[str, Any]]:
    pattern = f"%{q}%"
    rows = (
        tenant_query(db, ImagingOrder, current_user)
        .filter(
            or_(
                ImagingOrder.id.ilike(pattern),
                ImagingOrder.exam_type.ilike(pattern),
                ImagingOrder.body_region.ilike(pattern),
                ImagingOrder.clinical_info.ilike(pattern),
            )
        )
        .order_by(ImagingOrder.ordered_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "resource_type": "imaging_order",
            "id": o.id,
            "label": f"Imagerie — {o.exam_type} {o.body_region}",
            "subtitle": f"{o.urgency} · {o.status} · {o.ordered_at.strftime('%d/%m/%Y') if o.ordered_at else '—'}",
            "url": f"/imaging?order={o.id}",
            "patient_id": o.patient_id,
        }
        for o in rows
    ]


def search_invoices(
    db: Session, current_user: User, q: str, limit: int
) -> list[dict[str, Any]]:
    pattern = f"%{q}%"
    rows = (
        tenant_query(db, Invoice, current_user)
        .filter(
            or_(
                Invoice.invoice_number.ilike(pattern),
                Invoice.description.ilike(pattern),
            )
        )
        .order_by(Invoice.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "resource_type": "invoice",
            "id": i.id,
            "label": f"Facture {i.invoice_number}",
            "subtitle": f"{i.net_amount:,.0f} GNF · {i.status}".replace(",", " "),
            "url": f"/finance?invoice={i.id}",
            "patient_id": i.patient_id,
        }
        for i in rows
    ]


def search_clinical_notes(
    db: Session, current_user: User, q: str, limit: int
) -> list[dict[str, Any]]:
    """Search across clinical notes by content. Useful for finding
    a past consultation by keyword."""
    pattern = f"%{q}%"
    rows = (
        tenant_query(db, ClinicalNote, current_user)
        .filter(ClinicalNote.content.ilike(pattern))
        .order_by(ClinicalNote.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "resource_type": "clinical_note",
            "id": n.id,
            "label": f"{n.note_type} — {n.content[:80]}{'…' if len(n.content) > 80 else ''}",
            "subtitle": n.created_at.strftime("%d/%m/%Y") if n.created_at else "—",
            "url": f"/patients/{n.patient_id}",
            "patient_id": n.patient_id,
        }
        for n in rows
    ]


def global_search(
    db: Session,
    current_user: User,
    query: str,
    limit_per_category: int = 10,
    max_total: int = 50,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    """Run the global search across all resource types.

    Args:
        db: SQLAlchemy session
        current_user: authenticated user (for tenant filtering)
        query: search string (will be normalized)
        limit_per_category: max results per resource type
        max_total: hard cap on total results returned
        categories: optional list of categories to search (default: all)

    Returns:
        Dict with `categories` (grouped results), `total`, and `query`.
    """
    q = _normalize(query)
    if len(q) < 2:
        return {"query": query, "categories": {}, "total": 0}

    # Detect prefix-style search like "PAT-1234"
    explicit_category = None
    for prefix, cat in PREFIX_MAP.items():
        if q.startswith(prefix.lower()):
            explicit_category = cat
            # Strip the prefix from the query for LIKE matching
            q = q[len(prefix):]
            if len(q) < 1:
                return {"query": query, "categories": {}, "total": 0}
            break

    if explicit_category:
        categories_to_run = [explicit_category]
    else:
        categories_to_run = categories or [
            "patient", "invoice", "lab_order", "imaging_order", "clinical_note"
        ]

    # Cap limit per category so we never exceed max_total
    limit = min(limit_per_category, max_total)

    all_categories: dict[str, list[dict[str, Any]]] = {}
    runners = {
        "patient": search_patients,
        "invoice": search_invoices,
        "lab_order": search_lab_orders,
        "imaging_order": search_imaging_orders,
        "clinical_note": search_clinical_notes,
    }
    for cat in categories_to_run:
        runner = runners.get(cat)
        if not runner:
            continue
        try:
            results = runner(db, current_user, q, limit)
            if results:
                all_categories[cat] = results
        except Exception:
            # Be resilient — one failing category shouldn't break the whole search
            continue

    # Apply max_total cap
    total_returned = 0
    capped: dict[str, list[dict[str, Any]]] = {}
    for cat, items in all_categories.items():
        remaining = max_total - total_returned
        if remaining <= 0:
            break
        slice_items = items[:remaining]
        capped[cat] = slice_items
        total_returned += len(slice_items)

    return {
        "query": query,
        "categories": capped,
        "total": total_returned,
    }
