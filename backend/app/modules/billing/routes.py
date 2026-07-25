from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.datetime import utcnow
from app.core.pagination import PaginationParams, paginate
from app.core.tenant import tenant_query, enforce_facility_access
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.audit.service import audit_log
from app.modules.billing.models import Invoice, Payment, TariffItem
from app.modules.billing.schemas import InvoiceCancelCreate, InvoiceCreate, PaymentCreate, TariffItemCreate
from app.modules.rbac.dependencies import require_permission
from app.modules.realtime import publish_kpi_update
from app.modules.users.models import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/tariffs")
def list_tariffs(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    query = tenant_query(db, TariffItem, current_user).order_by(TariffItem.name)
    if pagination.search:
        query = query.filter(
            (TariffItem.name.ilike(f"%{pagination.search}%"))
            | (TariffItem.code.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/tariffs")
def create_tariff(
    payload: TariffItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.manage")),
):
    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = current_user.facility_id
    enforce_facility_access(current_user, data.get("facility_id"))
    row = TariffItem(**data)
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="tariff.created",
        entity_type="tariff_item",
        entity_id=row.id,
        level="NORMAL",
    )
    db.commit()
    db.refresh(row)
    return {"data": row, "message": "tariff created"}


@router.post("/invoices")
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.manage")),
):
    # Inférer facility_id depuis le patient si non fourni
    from app.modules.patients.models import Patient
    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    enforce_facility_access(current_user, patient.facility_id)

    data = payload.model_dump(exclude_none=True)
    if not data.get("facility_id"):
        data["facility_id"] = patient.facility_id

    # Auto-générer invoice_number si non fourni
    if not data.get("invoice_number"):
        from uuid import uuid4
        data["invoice_number"] = f"INV-{uuid4().hex[:8].upper()}"

    existing = db.query(Invoice).filter(Invoice.invoice_number == data["invoice_number"]).first()
    if existing:
        raise HTTPException(status_code=400, detail="Invoice number already exists")
    row = Invoice(**data)
    row.balance_due = row.net_amount
    row.status = "ISSUED"
    db.add(row)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="invoice.created",
        entity_type="invoice",
        entity_id=row.id,
        level="IMPORTANT",
        notes=f"amount={row.net_amount}",
    )
    db.commit()
    db.refresh(row)
    # v2.8.0 — Audit log pour traçabilité médico-légale
    audit_log(
        db=db,
        action="billing.invoice.create",
        user=current_user,
        resource_type="invoice",
        resource_id=str(row.id),
        request=None,  # pas de Request dans cette fonction
        status_code=200,
    )
    return {"data": row, "message": "invoice created"}


@router.get("/invoices")
def list_invoices(
    pagination: PaginationParams = Depends(),
    status: str | None = None,
    patient_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    """Liste paginée des factures avec filtres serveur.

    Filtres supportés :
    - `status` : PENDING | PARTIALLY_PAID | PAID | CANCELLED
    - `patient_id` : scoping par patient
    - `date_from` / `date_to` : plage de created_at (ISO 8601)
    - `search` : recherche sur invoice_number et description
    """
    query = tenant_query(db, Invoice, current_user).order_by(Invoice.created_at.desc())
    if pagination.search:
        query = query.filter(
            (Invoice.invoice_number.ilike(f"%{pagination.search}%"))
            | (Invoice.description.ilike(f"%{pagination.search}%"))
        )
    if status:
        query = query.filter(Invoice.status == status.upper())
    if patient_id:
        query = query.filter(Invoice.patient_id == patient_id)
    if date_from:
        try:
            from datetime import datetime as _dt
            query = query.filter(Invoice.created_at >= _dt.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime as _dt
            query = query.filter(Invoice.created_at <= _dt.fromisoformat(date_to))
        except ValueError:
            pass
    return paginate(query, pagination)


@router.post("/invoices/{invoice_id}/payments")
def create_payment(
    invoice_id: str,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.pay")),
):
    # v2.8.0 — P0-3 fix : row lock SELECT FOR UPDATE pour éviter race condition
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).with_for_update().first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    enforce_facility_access(current_user, invoice.facility_id)
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")
    # Inférer facility_id depuis l'invoice si non fourni
    facility_id = payload.facility_id or invoice.facility_id
    payment = Payment(
        facility_id=facility_id,
        invoice_id=invoice_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        received_by=current_user.id,
    )
    invoice.paid_amount += payload.amount
    invoice.balance_due = max(invoice.net_amount - invoice.paid_amount, 0)
    # v2.8.2 — P1 fix : éviter float == 0 (imprécision), utiliser <= 0.005
    invoice.status = "PAID" if invoice.balance_due <= 0.005 else "PARTIALLY_PAID"
    db.add(payment)
    db.flush()
    record_activity(
        db=db,
        actor_id=current_user.id,
        action_name="payment.created",
        entity_type="payment",
        entity_id=payment.id,
        level="CRITICAL",
        notes=f"invoice_id={invoice.id}; amount={payment.amount}; method={payment.payment_method}",
    )
    db.commit()
    db.refresh(payment)
    # v2.8.0 — Audit log pour traçabilité médico-légale
    audit_log(
        db=db,
        action="billing.payment.create",
        user=current_user,
        resource_type="payment",
        resource_id=str(payment.id),
        request=None,  # pas de Request dans cette fonction
        status_code=200,
    )
    db.refresh(invoice)
    # v1.3.0 — push realtime KPI update so the finance dashboard live-counts revenue
    publish_kpi_update(
        facility_id=invoice.facility_id,
        kpi="billing.payments.today.amount",
        value=float(payload.amount),
        delta=float(payload.amount),
        extra={"payment_id": payment.id, "invoice_id": invoice.id, "method": payload.payment_method},
    )
    return {"data": {"payment": payment, "invoice": invoice}, "message": "payment created"}


@router.get("/payments")
def list_payments(
    pagination: PaginationParams = Depends(),
    status: str | None = None,
    invoice_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    """Liste paginée des paiements avec filtres serveur.

    Filtres : `status`, `invoice_id`, `date_from`/`date_to` (sur received_at), `search`.
    """
    query = tenant_query(db, Payment, current_user).order_by(Payment.received_at.desc())
    if pagination.search:
        query = query.filter(
            (Payment.payment_method.ilike(f"%{pagination.search}%"))
            | (Payment.status.ilike(f"%{pagination.search}%"))
        )
    if status:
        query = query.filter(Payment.status == status.upper())
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    if date_from:
        try:
            from datetime import datetime as _dt
            query = query.filter(Payment.received_at >= _dt.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime as _dt
            query = query.filter(Payment.received_at <= _dt.fromisoformat(date_to))
        except ValueError:
            pass
    return paginate(query, pagination)


@router.get("/payments/{payment_id}/receipt")
def get_receipt(
    payment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    enforce_facility_access(current_user, payment.facility_id)
    invoice = db.query(Invoice).filter(Invoice.id == payment.invoice_id).first()
    return {
        "data": {
            "payment_id": payment.id,
            "receipt_number": payment.id,
            "invoice_number": invoice.invoice_number if invoice else None,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "status": payment.status,
            "received_at": payment.received_at,
        },
        "message": "receipt generated",
    }


# ============================================================================
# v2.4.0 — Phase 4 : Tableau de bord caisse + Annulation facture
# ============================================================================

@router.get("/dashboard")
def cashier_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    """Tableau de bord caisse — vue caissier.

    Retourne :
    - revenue_today : total encaissé aujourd'hui
    - revenue_month : total encaissé ce mois
    - outstanding_total : total des soldes dus (factures PARTIALLY_PAID)
    - invoices_count_by_status : {DRAFT, ISSUED, PARTIALLY_PAID, PAID, CANCELLED}
    - payments_today : liste des paiements du jour
    - payments_count_today : nombre de paiements
    """
    from datetime import datetime, timezone
    from sqlalchemy import func

    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Revenus (paiements COMPLETED aujourd'hui / ce mois)
    payments_today_q = (
        tenant_query(db, Payment, current_user)
        .filter(Payment.status == "COMPLETED")
        .filter(Payment.received_at >= today_start)
    )
    payments_today = payments_today_q.all()
    revenue_today = sum(p.amount for p in payments_today)

    payments_month_q = (
        tenant_query(db, Payment, current_user)
        .filter(Payment.status == "COMPLETED")
        .filter(Payment.received_at >= month_start)
    )
    revenue_month = sum(p.amount for p in payments_month_q.all())

    # Créances (soldes dus)
    outstanding_q = (
        tenant_query(db, Invoice, current_user)
        .filter(Invoice.balance_due > 0)
        .filter(Invoice.status.in_(["ISSUED", "PARTIALLY_PAID"]))
    )
    outstanding_total = sum(inv.balance_due for inv in outstanding_q.all())

    # Comptage par statut
    status_counts_raw = (
        tenant_query(db, Invoice, current_user)
        .with_entities(Invoice.status, func.count(Invoice.id))
        .group_by(Invoice.status)
        .all()
    )
    invoices_count_by_status = {status: count for status, count in status_counts_raw}

    return {
        "data": {
            "revenue_today": round(revenue_today, 2),
            "revenue_month": round(revenue_month, 2),
            "outstanding_total": round(outstanding_total, 2),
            "currency": "GNF",
            "invoices_count_by_status": invoices_count_by_status,
            "payments_count_today": len(payments_today),
            "payments_today": [
                {
                    "id": str(p.id),
                    "invoice_id": p.invoice_id,
                    "amount": p.amount,
                    "payment_method": p.payment_method,
                    "received_by": p.received_by,
                    "received_at": p.received_at.isoformat() if p.received_at else None,
                }
                for p in payments_today[:20]  # Top 20 pour perf
            ],
        },
        "message": "cashier dashboard",
    }


@router.post("/invoices/{invoice_id}/cancel")
def cancel_invoice(
    invoice_id: str,
    payload: InvoiceCancelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.validate")),
):
    """Annulation contrôlée d'une facture.

    Body JSON:
    {"reason": "Erreur de saisie — facture dupliquée"}

    Règles :
    - permission billing.validate requise (ADMIN ou SUPER_ADMIN typiquement)
    - la facture ne doit PAS avoir de paiements COMPLETED (sinon il faut
      d'abord rembourser)
    - enregistre cancellation_reason + cancelled_at + cancelled_by
    - status passe à CANCELLED
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    enforce_facility_access(current_user, invoice.facility_id)

    if invoice.status == "CANCELLED":
        raise HTTPException(status_code=409, detail="Facture déjà annulée")
    if invoice.status == "PAID":
        raise HTTPException(
            status_code=409,
            detail="Impossible d'annuler une facture payée — effectuer un remboursement",
        )

    reason = payload.reason.strip()
    if not reason or len(reason) < 5:
        raise HTTPException(
            status_code=422,
            detail="reason obligatoire (minimum 5 caractères)",
        )

    # Vérifier qu'aucun paiement COMPLETED n'existe
    payments = (
        db.query(Payment)
        .filter(Payment.invoice_id == invoice_id)
        .filter(Payment.status == "COMPLETED")
        .all()
    )
    if payments:
        raise HTTPException(
            status_code=409,
            detail=f"Impossible d'annuler — {len(payments)} paiement(s) COMPLETED lié(s). "
                   "Rembourser avant annulation.",
        )

    # Annuler
    invoice.status = "CANCELLED"
    invoice.cancellation_reason = reason[:500]
    invoice.cancelled_at = utcnow()
    invoice.cancelled_by = str(current_user.id)
    db.commit()
    db.refresh(invoice)
    # v2.8.0 — Audit log pour traçabilité médico-légale
    audit_log(
        db=db,
        action="billing.invoice.cancel",
        user=current_user,
        resource_type="invoice",
        resource_id=str(invoice.id),
        request=None,  # pas de Request dans cette fonction
        status_code=200,
    )

    return {
        "data": {
            "id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "status": invoice.status,
            "cancellation_reason": invoice.cancellation_reason,
            "cancelled_at": invoice.cancelled_at.isoformat() if invoice.cancelled_at else None,
            "cancelled_by": invoice.cancelled_by,
        },
        "message": "Facture annulée",
    }


# ============================================================================
# v2.9.1 — Insurance / Tiers payeur
# ============================================================================

from app.modules.billing.insurance_models import InsuranceProvider, PatientInsurance


@router.get("/insurance/providers")
def list_insurance_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    """Lister les fournisseurs d'assurance."""
    query = db.query(InsuranceProvider)
    if current_user.role != "SUPER_ADMIN":
        query = query.filter(
            (InsuranceProvider.facility_id == current_user.facility_id) |
            (InsuranceProvider.facility_id.is_(None))
        )
    rows = query.order_by(InsuranceProvider.name).all()
    return {
        "data": [
            {
                "id": str(p.id),
                "name": p.name,
                "code": p.code,
                "coverage_rate": p.coverage_rate,
                "contact_phone": p.contact_phone,
                "status": p.status,
            }
            for p in rows
        ],
        "total": len(rows),
    }


@router.post("/insurance/providers")
def create_insurance_provider(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.validate")),
):
    """Créer un fournisseur d'assurance."""
    name = (payload or {}).get("name", "").strip()
    code = (payload or {}).get("code", "").strip()
    if not name or not code:
        raise HTTPException(status_code=422, detail="name et code obligatoires")
    provider = InsuranceProvider(
        facility_id=current_user.facility_id if current_user.role != "SUPER_ADMIN" else (payload or {}).get("facility_id"),
        name=name,
        code=code,
        coverage_rate=float((payload or {}).get("coverage_rate", 0)),
        contact_phone=(payload or {}).get("contact_phone"),
        contact_email=(payload or {}).get("contact_email"),
        address=(payload or {}).get("address"),
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return {"data": {"id": str(provider.id), "name": provider.name, "code": provider.code}, "message": "Fournisseur créé"}


@router.get("/patients/{patient_id}/insurance")
def list_patient_insurance(
    patient_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    """Lister les polices d'assurance d'un patient."""
    from app.modules.patients.models import Patient
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    enforce_facility_access(current_user, patient.facility_id)

    rows = (
        db.query(PatientInsurance)
        .filter(PatientInsurance.patient_id == patient_id)
        .filter(PatientInsurance.is_active == True)
        .all()
    )
    return {
        "data": [
            {
                "id": str(r.id),
                "provider_id": str(r.provider_id),
                "policy_number": r.policy_number,
                "beneficiary_name": r.beneficiary_name,
                "coverage_rate": r.coverage_rate,
                "valid_until": r.valid_until.isoformat() if r.valid_until else None,
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/patients/{patient_id}/insurance")
def add_patient_insurance(
    patient_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.write")),
):
    """Ajouter une police d'assurance à un patient."""
    from app.modules.patients.models import Patient
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient introuvable")
    enforce_facility_access(current_user, patient.facility_id)

    provider_id = (payload or {}).get("provider_id")
    policy_number = (payload or {}).get("policy_number", "").strip()
    if not provider_id or not policy_number:
        raise HTTPException(status_code=422, detail="provider_id et policy_number obligatoires")

    insurance = PatientInsurance(
        facility_id=patient.facility_id,
        patient_id=patient_id,
        provider_id=provider_id,
        policy_number=policy_number,
        beneficiary_name=(payload or {}).get("beneficiary_name"),
        coverage_rate=(payload or {}).get("coverage_rate"),
    )
    db.add(insurance)
    db.commit()
    db.refresh(insurance)
    return {"data": {"id": str(insurance.id), "policy_number": insurance.policy_number}, "message": "Assurance ajoutée"}


@router.post("/invoices/{invoice_id}/insurance")
def apply_insurance_to_invoice(
    invoice_id: str,
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.validate")),
):
    """Appliquer une assurance à une facture (split patient/assureur).

    Body JSON:
    {"insurance_id": "...", "coverage_rate": 80}

    Calcule :
    - patient_share = net_amount × (1 - coverage_rate/100)
    - insurer_share = net_amount × (coverage_rate/100)
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    enforce_facility_access(current_user, invoice.facility_id)

    insurance_id = (payload or {}).get("insurance_id")
    coverage_rate = float((payload or {}).get("coverage_rate", 0))

    if not insurance_id:
        raise HTTPException(status_code=422, detail="insurance_id obligatoire")
    if coverage_rate < 0 or coverage_rate > 100:
        raise HTTPException(status_code=422, detail="coverage_rate doit être entre 0 et 100")

    insurance = db.query(PatientInsurance).filter(PatientInsurance.id == insurance_id).first()
    if not insurance:
        raise HTTPException(status_code=404, detail="Assurance introuvable")

    patient_share = round(invoice.net_amount * (1 - coverage_rate / 100), 2)
    insurer_share = round(invoice.net_amount * (coverage_rate / 100), 2)

    return {
        "data": {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "net_amount": invoice.net_amount,
            "insurance_id": str(insurance.id),
            "policy_number": insurance.policy_number,
            "coverage_rate": coverage_rate,
            "patient_share": patient_share,
            "insurer_share": insurer_share,
            "balance_due": invoice.balance_due,
        },
        "message": "Assurance appliquée — part patient et part assureur calculées",
    }
