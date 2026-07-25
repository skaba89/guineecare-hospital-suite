from pydantic import BaseModel


class TariffItemCreate(BaseModel):
    facility_id: str | None = None  # auto-inféré depuis l'utilisateur si absent
    code: str
    name: str
    category: str
    unit_price: float


class InvoiceCreate(BaseModel):
    facility_id: str | None = None  # auto-inféré depuis le patient si absent
    patient_id: str
    admission_id: str | None = None
    invoice_number: str | None = None  # auto-généré si absent
    description: str | None = None
    net_amount: float


class PaymentCreate(BaseModel):
    facility_id: str | None = None  # auto-inféré depuis l'invoice si absent
    amount: float
    payment_method: str


# v2.8.1 — P1-6 : Pydantic schema pour annulation facture

class InvoiceCancelCreate(BaseModel):
    reason: str
