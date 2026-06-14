import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings, validate_settings
from app.core.limiter import limiter
from app.db.init_db import init_db
from app.db.seed import run_seed
from app.modules.auth.routes import router as auth_router
from app.modules.users.routes import router as users_router
from app.modules.rbac.routes import router as rbac_router
from app.modules.facilities.routes import router as facilities_router
from app.modules.departments.routes import router as departments_router
from app.modules.patients.routes import router as patients_router
from app.modules.admissions.routes import router as admissions_router
from app.modules.emergency.routes import router as emergency_router
from app.modules.pharmacy.routes import router as pharmacy_router
from app.modules.laboratory.routes import router as laboratory_router
from app.modules.billing.routes import router as billing_router
from app.modules.hospitalization.routes import router as hospitalization_router
from app.modules.activity.routes import router as activity_router
from app.modules.clinical.routes import router as clinical_router
from app.modules.maternity.routes import router as maternity_router
from app.modules.personnel.routes import router as personnel_router
from app.modules.imaging.routes import router as imaging_router
from app.modules.surgery.routes import router as surgery_router
from app.modules.quality.routes import router as quality_router
from app.modules.reporting.routes import router as reporting_router

API_PREFIX = "/api/v1"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: validate configuration, initialize DB, seed demo data
    validate_settings()
    init_db()
    if os.environ.get("SEED_DEMO_DATA", "false").lower() in {"1", "true", "yes"}:
        run_seed()
    yield


app = FastAPI(title="GuineeCare API", version="0.1.0", lifespan=lifespan)

# --- SlowAPI rate-limiting state & handler ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS: read allowed origins from settings (env var or sensible dev defaults) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Security headers middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)


app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(rbac_router, prefix=API_PREFIX)
app.include_router(facilities_router, prefix=API_PREFIX)
app.include_router(departments_router, prefix=API_PREFIX)
app.include_router(patients_router, prefix=API_PREFIX)
app.include_router(admissions_router, prefix=API_PREFIX)
app.include_router(emergency_router, prefix=API_PREFIX)
app.include_router(pharmacy_router, prefix=API_PREFIX)
app.include_router(laboratory_router, prefix=API_PREFIX)
app.include_router(billing_router, prefix=API_PREFIX)
app.include_router(hospitalization_router, prefix=API_PREFIX)
app.include_router(activity_router, prefix=API_PREFIX)
app.include_router(clinical_router, prefix=API_PREFIX)
app.include_router(maternity_router, prefix=API_PREFIX)
app.include_router(personnel_router, prefix=API_PREFIX)
app.include_router(imaging_router, prefix=API_PREFIX)
app.include_router(surgery_router, prefix=API_PREFIX)
app.include_router(quality_router, prefix=API_PREFIX)
app.include_router(reporting_router, prefix=API_PREFIX)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "guineecare-backend"}


@app.get(API_PREFIX)
def api_root():
    return {
        "name": "GuineeCare Hospital Suite",
        "version": "0.1.0",
        "modules": ["auth", "users", "rbac", "facilities", "departments", "patients", "admissions", "emergency", "pharmacy", "laboratory", "billing", "hospitalization", "activity", "clinical", "maternity", "personnel", "imaging", "surgery", "quality", "reporting"],
    }
