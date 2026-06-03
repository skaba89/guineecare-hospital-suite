from fastapi import FastAPI

from app.modules.patients.routes import router as patients_router
from app.modules.admissions.routes import router as admissions_router
from app.modules.emergency.routes import router as emergency_router
from app.modules.pharmacy.routes import router as pharmacy_router
from app.modules.laboratory.routes import router as laboratory_router
from app.modules.billing.routes import router as billing_router

API_PREFIX = "/api/v1"

app = FastAPI(
    title="GuinéeCare Hospital Suite API",
    version="0.1.0",
    description="API MVP pour la plateforme hospitalière GuinéeCare."
)

app.include_router(patients_router, prefix=API_PREFIX)
app.include_router(admissions_router, prefix=API_PREFIX)
app.include_router(emergency_router, prefix=API_PREFIX)
app.include_router(pharmacy_router, prefix=API_PREFIX)
app.include_router(laboratory_router, prefix=API_PREFIX)
app.include_router(billing_router, prefix=API_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "guineecare-backend"}


@app.get(API_PREFIX)
def api_root():
    return {
        "name": "GuinéeCare Hospital Suite",
        "version": "0.1.0",
        "modules": [
            "auth",
            "facilities",
            "patients",
            "admissions",
            "clinical",
            "emergency",
            "hospitalization",
            "pharmacy",
            "laboratory",
            "billing",
            "reporting"
        ]
    }
