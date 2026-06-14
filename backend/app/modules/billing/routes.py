from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.db.session import get_db
from app.modules.activity.service import record_activity
from app.modules.billing.models import Invoice, Payment, TariffItem
from app.modules.billing.schemas import InvoiceCreate, PaymentCreate, TariffItemCreate
from app.modules.rbac.dependencies import require_permission
from app.modules.users.models import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/tariffs")
def list_tariffs(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    query = db.query(TariffItem).order_by(TariffItem.name)
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
    row = TariffItem(**payload.model_dump())
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
    existing = db.query(Invoice).filter(Invoice.invoice_number == payload.invoice_number).first()
    if existing:
        raise HTTPException(status_code=400, detail="Invoice number already exists")
    row = Invoice(**payload.model_dump())
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
    return {"data": row, "message": "invoice created"}


@router.get("/invoices")
def list_invoices(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    query = db.query(Invoice).order_by(Invoice.created_at.desc())
    if pagination.search:
        query = query.filter(
            (Invoice.invoice_number.ilike(f"%{pagination.search}%"))
            | (Invoice.description.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)


@router.post("/invoices/{invoice_id}/payments")
def create_payment(
    invoice_id: str,
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.pay")),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Payment amount must be positive")
    payment = Payment(
        facility_id=payload.facility_id,
        invoice_id=invoice_id,
        amount=payload.amount,
        payment_method=payload.payment_method,
        received_by=current_user.id,
    )
    invoice.paid_amount += payload.amount
    invoice.balance_due = max(invoice.net_amount - invoice.paid_amount, 0)
    invoice.status = "PAID" if invoice.balance_due == 0 else "PARTIALLY_PAID"
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
    db.refresh(invoice)
    return {"data": {"payment": payment, "invoice": invoice}, "message": "payment created"}


@router.get("/payments")
def list_payments(
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("billing.read")),
):
    query = db.query(Payment).order_by(Payment.received_at.desc())
    if pagination.search:
        query = query.filter(
            (Payment.payment_method.ilike(f"%{pagination.search}%"))
            | (Payment.status.ilike(f"%{pagination.search}%"))
        )
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
