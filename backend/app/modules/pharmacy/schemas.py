from pydantic import BaseModel


class PharmacyProductCreate(BaseModel):
    facility_id: str
    code: str
    name: str
    category: str | None = None
    form: str | None = None
    dosage: str | None = None


class StockMovementCreate(BaseModel):
    facility_id: str
    product_id: str
    movement_type: str
    quantity: float
    reason: str | None = None
    min_threshold: float = 0
