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
from app.modules.user_profile.routes import router as user_profile_router, feedback_router
from app.modules.documents.routes import router as documents_router
from app.modules.search.routes import router as search_router
from app.modules.i18n.routes import router as i18n_router
from app.modules.realtime.routes import router as realtime_router
from app.modules.notifications.sms_routes import router as sms_router
from app.modules.quality.dashboard_routes import router as quality_dashboard_router
from app.modules.personnel.rh_v2_routes import router as rh_v2_router
from app.modules.fhir.routes import router as fhir_router
from app.modules.observability.routes import router as observability_router, metrics_router
from app.modules.observability.middleware import MetricsMiddleware
from app.modules.observability.logging import configure_logging
from app.modules.observability.metrics import set_app_info

logger = logging.getLogger("guineecare")

API_PREFIX = "/api/v1"
APP_VERSION = "1.7.1"

# --- OpenAPI documentation metadata (v0.10.0) ---
API_DESCRIPTION = """\
# GuinéeCare Hospital Suite — REST API

API REST sécurisée pour la **plateforme hospitalière GuinéeCare**, déployée
pour les établissements de santé de Guinée (CHU Donka, CHU Ignace Deen, etc.).

## Conventions

- **Toutes les routes** sont préfixées par `/api/v1` (sauf `/health`, `/metrics`).
- **Authentification** : JWT Bearer (header `Authorization: Bearer <token>`).
  - POST `/api/v1/auth/login` → `access_token` (60 min) + `refresh_token` (30 jours).
  - POST `/api/v1/auth/refresh` pour renouveler l'`access_token`.
  - POST `/api/v1/auth/logout` pour révoquer le `jti` (blacklist côté serveur).
- **Multi-tenant** : isolation par `facility_id` (RLS-like via `tenant_query`).
  - SUPER_ADMIN voit tous les établissements ; les autres rôles ne voient que le leur.
- **RBAC** : 8 rôles (SUPER_ADMIN, ADMIN, DOCTOR, NURSE, MIDWIFE, PHARMACIST, LAB_TECH, CASHIER)
  avec permissions granulaires (`patients.read`, `patients.write`, `billing.validate`, etc.).
- **Pagination** : `?page=1&page_size=20` → réponse `{items, total, page, page_size}`.
- **Rate limiting** : 5 logins/min sur `/auth/login` (prod), 30 refreshs/min sur `/auth/refresh`.
- **Audit log** : toutes les mutations sensibles sont journalisées (table `audit_logs`).

## Codes d'erreur standards

| Code | Signification |
|------|---------------|
| 400  | Requête invalide (validation métier) |
| 401  | Non authentifié — JWT manquant, expiré ou révoqué |
| 403  | Non autorisé — permission RBAC insuffisante ou accès cross-tenant |
| 404  | Ressource introuvable |
| 409  | Conflit (duplicate, état invalide) |
| 422  | Erreur de validation Pydantic |
| 423  | Compte verrouillé (lockout après 5 échecs de login) |
| 429  | Rate limit dépassé |
| 500  | Erreur serveur interne |

## Documentation

- **OpenAPI JSON** : `/api/v1/openapi.json` (spécification machine-lisible).
- **Swagger UI** : `/docs` (interactive, permet de tester les endpoints).
- **ReDoc** : `/redoc` (vue lecture seule, plus adaptée à la documentation).
- **Collection Postman** : `docs/api/guineecare.postman_collection.json` (importable).
"""

OPENAPI_TAGS = [
    {"name": "auth", "description": "Authentification JWT (login, refresh, logout, profil)."},
    {"name": "users", "description": "Utilisateurs, rôles, bootstrap super-admin, lockout."},
    {"name": "rbac", "description": "Contrôle d'accès basé sur les rôles (rôles, permissions)."},
    {"name": "facilities", "description": "Établissements de santé (multi-tenant)."},
    {"name": "departments", "description": "Départements / services par établissement."},
    {"name": "patients", "description": "Dossier Patient Informatisé (DPI) : création, recherche, consultation."},
    {"name": "admissions", "description": "Admissions programmées et urgentes."},
    {"name": "emergency", "description": "File d'attente des urgences, triage (niveaux 1-5), orientation."},
    {"name": "hospitalization", "description": "Hospitalisation, lits, séjours, bed-board."},
    {"name": "clinical", "description": "DPI clinique : antécédents, allergies, constantes, diagnostics."},
    {"name": "maternity", "description": "Grossesses, accouchements, CPoN (Consultation Post-Natale)."},
    {"name": "pharmacy", "description": "Pharmacie : stock, dispensation, médicaments."},
    {"name": "laboratory", "description": "Laboratoire : prélèvements, analyses, validation."},
    {"name": "imaging", "description": "Imagerie médicale : demandes, résultats, comptes rendus."},
    {"name": "surgery", "description": "Bloc opératoire : programmation, comptes rendus."},
    {"name": "billing", "description": "Facturation hospitalière, caisse, paiements."},
    {"name": "personnel", "description": "RH hospitalières : effectifs, plannings, gardes."},
    {"name": "quality", "description": "Qualité, indicateurs, événements indésirables."},
    {"name": "reporting", "description": "Reporting national, agrégats multi-établissements."},
    {"name": "audit", "description": "Journal d'audit (consultation, filtres)."},
    {"name": "activity", "description": "Flux d'activité temps réel (timeline)."},
    {"name": "notifications", "description": "Notifications multicanal (console, email, SMS)."},
    {"name": "user-profile", "description": "Profil utilisateur : préférences UI, items récents (v1.1.0)."},
    {"name": "feedback", "description": "Retours utilisateurs : bug, suggestion, question, praise (v1.1.0)."},
    {"name": "documents", "description": "Génération PDF de documents cliniques et administratifs (v1.2.0)."},
    {"name": "search", "description": "Recherche globale multi-ressources (v1.2.0)."},
    {"name": "i18n", "description": "Internationalisation (catalogues de traduction EN/FR) — v1.3.0."},
    {"name": "realtime", "description": "WebSocket temps réel (KPI push, dashboard live) — v1.3.0."},
    {"name": "notifications-sms", "description": "Notifications SMS multicanal (Orange/MTN/Moov/Mock, règles de routage) — v1.4.0."},
    {"name": "quality-dashboard", "description": "Dashboard qualité avancé (KPIs OMS/HAS, seuils, alertes automatiques) — v1.4.0."},
    {"name": "personnel-rh-v2", "description": "RH v2 : plannings, gardes, congés, astreintes, remplacements — v1.5.0."},
    {"name": "fhir-r4", "description": "Interopérabilité HL7 FHIR R4 (Patient, Observation, MedicationRequest, DiagnosticReport, Encounter) — v1.6.0."},
    {"name": "health", "description": "Health checks (/health, /health/live, /health/ready)."},
    {"name": "metrics", "description": "Métriques Prometheus (/metrics, token-gated)."},
    {"name": "system", "description": "Endpoints racine et utilitaires système."},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure structured logging (JSON in prod, pretty in dev)
    configure_logging(environment=os.environ.get("ENVIRONMENT", "local"))

    # Set app_info gauge labels for Prometheus
    set_app_info(version=APP_VERSION, environment=os.environ.get("ENVIRONMENT", "local"))

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


app = FastAPI(
    title="GuinéeCare Hospital Suite API",
    summary="Plateforme hospitalière multi-tenant pour la Guinée — API REST sécurisée.",
    description=API_DESCRIPTION,
    version=APP_VERSION,
    openapi_tags=OPENAPI_TAGS,
    contact={
        "name": "GuinéeCare Tech Team",
        "url": "https://github.com/skaba89/guineecare-hospital-suite",
        "email": "tech@guineecare.gn",
    },
    license_info={
        "name": "Private — Usage réservé CHU Donka / Ministère Santé Guinée",
        "url": "https://github.com/skaba89/guineecare-hospital-suite/blob/main/LICENSE",
    },
    servers=[
        {"url": "/api/v1", "description": "Serveur courant (proxy Vite / nginx / k8s)"},
        {"url": "http://localhost:8000/api/v1", "description": "Développement local (uvicorn)"},
        {"url": "https://api.guineecare.gn/api/v1", "description": "Production — pilote CHU Donka"},
    ],
    openapi_url=f"{API_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

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
app.include_router(user_profile_router, prefix=API_PREFIX)
app.include_router(feedback_router, prefix=API_PREFIX)
app.include_router(documents_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(i18n_router, prefix=API_PREFIX)
app.include_router(realtime_router, prefix=API_PREFIX)
app.include_router(sms_router, prefix=API_PREFIX)
app.include_router(quality_dashboard_router, prefix=API_PREFIX)
app.include_router(rh_v2_router, prefix=API_PREFIX)
app.include_router(fhir_router, prefix=API_PREFIX)

# Observability routes — mounted at root, NOT under /api/v1, so they match
# Prometheus and Kubernetes conventions (/metrics, /health, /health/live, /health/ready).
app.include_router(observability_router)
app.include_router(metrics_router)


@app.get(API_PREFIX, tags=["system"], summary="Racine API — version et modules disponibles")
def api_root():
    return {
        "name": "GuineeCare Hospital Suite",
        "version": APP_VERSION,
        "modules": [
            "auth", "users", "rbac", "facilities", "departments",
            "patients", "admissions", "emergency", "pharmacy", "laboratory",
            "billing", "hospitalization", "activity", "clinical", "maternity",
            "personnel", "imaging", "surgery", "quality", "reporting",
            "audit", "notifications", "user-profile", "feedback",
            "documents", "search", "i18n", "realtime", "observability",
            "notifications-sms", "quality-dashboard",
            "personnel-rh-v2",
            "fhir-r4",
        ],
    }


# --- Custom OpenAPI enrichment (v0.10.0) ---
# Inject standard 401/403/422/500 responses + Bearer security on protected
# operations, so the spec is fully documented without polluting each route.
_PUBLIC_PATHS = frozenset({
    "/api/v1",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/health",
    "/health/live",
    "/health/ready",
    "/metrics",
    "/api/v1/openapi.json",
    "/docs",
    "/redoc",
})


def _is_public(path: str) -> bool:
    """True for endpoints that don't require JWT authentication."""
    return path in _PUBLIC_PATHS

_STANDARD_RESPONSES = {
    "401": {
        "description": "Non authentifié — JWT manquant, expiré ou révoqué (jti blacklisté).",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/HTTPValidationError"},
                "example": {"detail": "Not authenticated"},
            }
        },
    },
    "403": {
        "description": (
            "Non autorisé — permission RBAC insuffisante ou accès cross-tenant "
            "(tentative de lecture d'un établissement non autorisé)."
        ),
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/HTTPValidationError"},
                "example": {"detail": "Permission insuffisante : patients.write requis"},
            }
        },
    },
    "429": {
        "description": "Rate limit dépassé (5 logins/min sur /auth/login, 30 refreshs/min sur /auth/refresh).",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/HTTPValidationError"},
                "example": {"detail": "Too many requests"},
            }
        },
    },
    "500": {
        "description": "Erreur serveur interne (cf. logs structurés JSON).",
        "content": {
            "application/json": {
                "schema": {"$ref": "#/components/schemas/HTTPValidationError"},
                "example": {"detail": "Internal Server Error"},
            }
        },
    },
}


def _is_public(path: str) -> bool:
    """True for endpoints that don't require JWT authentication."""
    return path in _PUBLIC_PATHS


def _build_enriched_openapi():
    """Generate the OpenAPI spec, then inject standard responses + security."""
    spec = app.openapi_original() if hasattr(app, "openapi_original") else None
    if spec is None:
        from fastapi.openapi.utils import get_openapi
        spec = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
            openapi_tags=app.openapi_tags,
            servers=app.servers,
            contact=app.contact,
            license_info=app.license_info,
            summary=app.summary,
        )

    for path, ops in spec.get("paths", {}).items():
        for method, op in ops.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            responses = op.setdefault("responses", {})

            # Inject 422 on operations that declare a request body
            if "requestBody" in op and "422" not in responses:
                responses["422"] = {
                    "description": "Erreur de validation Pydantic (champ manquant, type incorrect, etc.).",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/HTTPValidationError"},
                            "example": {
                                "detail": [
                                    {
                                        "loc": ["body", "email"],
                                        "msg": "value is not a valid email address",
                                        "type": "value_error.email",
                                    }
                                ]
                            },
                        }
                    },
                }

            # Inject 401/403/429/500 only on protected operations
            if not _is_public(path):
                for code, resp in _STANDARD_RESPONSES.items():
                    if code not in responses:
                        responses[code] = resp
                # Tag Bearer security
                op.setdefault("security", [{"HTTPBearer": []}])

    # Ensure HTTPValidationError schema exists (it's auto-added by FastAPI when
    # any 422 response is declared). If it doesn't exist (edge case), add it.
    components = spec.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    if "HTTPValidationError" not in schemas:
        schemas["HTTPValidationError"] = {
            "title": "HTTPValidationError",
            "type": "object",
            "properties": {
                "detail": {
                    "title": "Detail",
                    "type": "array",
                    "items": {"$ref": "#/components/schemas/ValidationError"},
                }
            },
        }
        schemas["ValidationError"] = {
            "title": "ValidationError",
            "required": ["loc", "msg", "type"],
            "type": "object",
            "properties": {
                "loc": {
                    "title": "Location",
                    "type": "array",
                    "items": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                },
                "msg": {"title": "Message", "type": "string"},
                "type": {"title": "Error Type", "type": "string"},
            },
        }

    return spec


def custom_openapi():
    """Cached enriched OpenAPI spec (401/403/422/429/500 + Bearer security)."""
    cached = getattr(app, "openapi_schema_cache", None)
    if cached is not None:
        return cached
    spec = _build_enriched_openapi()
    app.openapi_schema_cache = spec
    return spec


# Preserve the original openapi() for reference, then override.
if not hasattr(app, "openapi_original"):
    app.openapi_original = app.openapi
app.openapi = custom_openapi


# --- Serve frontend static files (for Render all-in-one deployment) ---
# When deployed on Render, the frontend build (dist/) is copied into
# backend/static/ during the build phase. FastAPI serves these files
# so that a single URL serves both the API and the frontend.
#
# In dev mode (localhost), the frontend runs on Vite (port 5173) and
# this block is skipped because static/ doesn't exist.
import os as _os
from fastapi.staticfiles import StaticFiles as _StaticFiles
from fastapi.responses import FileResponse as _FileResponse

_STATIC_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "static")

if _os.path.isdir(_STATIC_DIR):
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", _StaticFiles(directory=_os.path.join(_STATIC_DIR, "assets")), name="assets")

    # SPA fallback : toutes les routes non-API servent index.html
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Ne pas intercepter les routes API, health, metrics, docs
        if (full_path.startswith("api/") or
            full_path in ("health", "health/live", "health/ready", "metrics", "docs", "redoc")):
            raise HTTPException(status_code=404)
        # Servir le fichier s'il existe, sinon index.html (SPA routing)
        file_path = _os.path.join(_STATIC_DIR, full_path)
        if _os.path.isfile(file_path):
            return _FileResponse(file_path)
        return _FileResponse(_os.path.join(_STATIC_DIR, "index.html"))

    logger.info("Frontend static files served from %s", _STATIC_DIR)
