from fastapi import APIRouter

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/tariffs")
def list_tariffs():
    return {"data": [], "message": "tariffs list"}


@router.post("/invoices")
def create_invoice(payload: dict):
    return {"data": payload, "message": "invoice created"}


@router.get("/invoices")
def list_invoices():
    return {"data": [], "message": "invoices list"}


@router.post("/invoices/{invoice_id}/payments")
def create_payment(invoice_id: str, payload: dict):
    return {"data": {"invoice_id": invoice_id, "payment": payload}, "message": "payment created"}


@router.get("/payments/{payment_id}/receipt")
def get_receipt(payment_id: str):
    return {"data": {"payment_id": payment_id}, "message": "receipt placeholder"}
