from pydantic import BaseModel


class TariffItemCreate(BaseModel):
    facility_id: str
    code: str
    name: str
    category: str
    unit_price: float


class InvoiceCreate(BaseModel):
    facility_id: str
    patient_id: str
    admission_id: str | None = None
    invoice_number: str
    description: str | None = None
    net_amount: float


class PaymentCreate(BaseModel):
    facility_id: str
    amount: float
    payment_method: str
