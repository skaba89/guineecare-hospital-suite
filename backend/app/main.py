import logging
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
from app.modules.audit.routes import router as audit_router
from app.modules.notifications.routes import router as notifications_router
from app.modules.observability.routes import router as observability_router, metrics_router
from app.modules.observability.middleware import MetricsMiddleware
from app.modules.observability.logging import configure_logging
from app.modules.observability.metrics import set_app_info

logger = logging.getLogger("guineecare")

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure structured logging (JSON in prod, pretty in dev)
    configure_logging(environment=os.environ.get("ENVIRONMENT", "local"))

    # Set app_info gauge labels for Prometheus
    set_app_info(version="0.9.0", environment=os.environ.get("ENVIRONMENT", "local"))

    # Startup: validate configuration, initialize DB, seed demo data
    try:
        validate_settings()
    except RuntimeError as e:
        logger.warning(f"Config validation warning: {e}")

    try:
        init_db()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Database init error: {e}")

    if os.environ.get("SEED_DEMO_DATA", "false").lower() in {"1", "true", "yes"}:
        # SECURITY (A05-002 — v0.9.0): refuse to seed demo data in non-local
        # environments. Demo seeds use predictable passwords (admin123, etc.)
        # and would create trivially-guessable accounts in production.
        if settings.environment not in ("local", "test", "dev"):
            logger.error(
                "SEED_DEMO_DATA=true is forbidden in environment=%s. "
                "Refusing to seed demo data. Set SEED_DEMO_DATA=false or "
                "use ENVIRONMENT=local/dev/test.",
                settings.environment,
            )
        else:
            try:
                from app.db.seed import run_seed
                run_seed()
                logger.info("Seed data loaded successfully")
            except Exception as e:
                logger.error(f"Seed data error (non-fatal): {e}")
                # Continue anyway — the app should still work with empty data

    yield


app = FastAPI(title="GuineeCare API", version="0.9.0", lifespan=lifespan)

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
app.add_middleware(MetricsMiddleware)


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
app.include_router(audit_router, prefix=API_PREFIX)
app.include_router(notifications_router, prefix=API_PREFIX)

# Observability routes — mounted at root, NOT under /api/v1, so they match
# Prometheus and Kubernetes conventions (/metrics, /health, /health/live, /health/ready).
app.include_router(observability_router)
app.include_router(metrics_router)


@app.get(API_PREFIX)
def api_root():
    return {
        "name": "GuineeCare Hospital Suite",
        "version": "0.9.0",
        "modules": [
            "auth", "users", "rbac", "facilities", "departments",
            "patients", "admissions", "emergency", "pharmacy", "laboratory",
            "billing", "hospitalization", "activity", "clinical", "maternity",
            "personnel", "imaging", "surgery", "quality", "reporting",
            "audit", "notifications", "observability",
        ],
    }
