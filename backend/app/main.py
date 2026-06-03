from fastapi import FastAPI

from app.db.init_db import init_db
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.facilities.routes import router as facilities_router
from app.modules.departments.routes import router as departments_router
from app.modules.patients.routes import router as patients_router
from app.modules.admissions.routes import router as admissions_router
from app.modules.emergency.routes import router as emergency_router
from app.modules.pharmacy.routes import router as pharmacy_router
from app.modules.laboratory.routes import router as laboratory_router
from app.modules.billing.routes import router as billing_router

API_PREFIX = "/api/v1"

app = FastAPI(title="GuineeCare API", version="0.1.0")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(facilities_router, prefix=API_PREFIX)
app.include_router(departments_router, prefix=API_PREFIX)
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
        "name": "GuineeCare Hospital Suite",
        "version": "0.1.0",
        "modules": ["auth", "users", "facilities", "departments", "patients", "admissions", "emergency", "pharmacy", "laboratory", "billing"]
    }
