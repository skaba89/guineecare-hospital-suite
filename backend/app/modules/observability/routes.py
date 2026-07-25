"""Health, readiness, and metrics endpoints.

- GET /health        — backward compat: simple "ok" (kept from v0.1)
- GET /health/live   — liveness probe (process is alive, returns 200 immediately)
- GET /health/ready  — readiness probe (DB is reachable, returns 200/503)
- GET /livez         — alias Kubernetes de /health/live (v2.3.0)
- GET /readyz        — alias Kubernetes de /health/ready (v2.3.0)
- GET /metrics       — Prometheus text exposition
                       SECURITY (A05-005 — v0.9.0): when METRICS_TOKEN is set,
                       requires `Authorization: Bearer <token>`. When unset
                       (default), /metrics is open — useful for dev/local but
                       NOT recommended for production deployments.
"""
import hmac
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.modules.observability.metrics import render_prometheus

router = APIRouter(prefix="/health", tags=["health"])

# v2.3.0 — Phase 8 : router séparé pour /livez et /readyz (convention Kubernetes)
k8s_router = APIRouter(tags=["health-k8s"])


@router.get("")
@router.get("/live")
def health_live():
    """Liveness — process is up. Kubernetes liveness probe target."""
    return {
        "status": "ok",
        "service": "guineecare-backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
def health_ready(response: Response, db: Session = Depends(get_db)):
    """Readiness — DB is reachable. Kubernetes readiness probe target.

    Returns 200 if DB ping succeeds, 503 otherwise. We do NOT raise —
    Kubernetes interprets non-2xx as not-ready and will keep the old pod
    serving traffic until this endpoint recovers.
    """
    checks: dict[str, str] = {}
    overall_ok = True

    # DB check
    try:
        start = time.perf_counter()
        db.execute(text("SELECT 1"))
        db_latency_ms = (time.perf_counter() - start) * 1000.0
        checks["database"] = f"ok ({db_latency_ms:.1f} ms)"
    except Exception as e:
        checks["database"] = f"fail: {e}"
        overall_ok = False

    if not overall_ok:
        response.status_code = 503

    return {
        "status": "ok" if overall_ok else "degraded",
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# v2.3.0 — Phase 8 : alias Kubernetes (convention /livez et /readyz)
@k8s_router.get("/livez")
def k8s_livez():
    """Alias Kubernetes pour /health/live."""
    return health_live()


@k8s_router.get("/readyz")
def k8s_readyz(response: Response, db: Session = Depends(get_db)):
    """Alias Kubernetes pour /health/ready."""
    return health_ready(response, db)


@router.get("/schema")
def health_schema():
    """Debug — vérifier que les colonnes critiques existent en DB.

    v2.7.1 — Endpoint temporaire pour diagnostiquer les 500 sur login.
    Vérifie les colonnes ajoutées par les migrations récentes (0023-0026).
    """
    from sqlalchemy import inspect as sqla_inspect
    from app.db.session import engine

    inspector = sqla_inspect(engine)
    result = {"tables": {}, "issues": []}

    # Colonnes critiques à vérifier
    checks = {
        "users": ["last_disabled_at"],
        "facilities": ["commune"],
        "pharmacy_products": ["unit_price"],
        "pharmacy_stock": ["batch_number", "expiry_date"],
        "stock_movements": ["patient_id", "prescription_id", "admission_id"],
        "invoices": ["cancellation_reason", "cancelled_at", "cancelled_by"],
    }

    for table, columns in checks.items():
        if table not in inspector.get_table_names():
            result["tables"][table] = {"exists": False, "missing_columns": columns}
            result["issues"].append(f"Table {table} manquante")
            continue
        existing = [c["name"] for c in inspector.get_columns(table)]
        missing = [c for c in columns if c not in existing]
        result["tables"][table] = {
            "exists": True,
            "columns_present": [c for c in columns if c in existing],
            "columns_missing": missing,
        }
        if missing:
            result["issues"].append(f"Table {table} — colonnes manquantes: {missing}")

    # Vérifier les nouvelles tables
    new_tables = ["prescriptions", "lab_order_tests"]
    for t in new_tables:
        result["tables"][t] = {"exists": t in inspector.get_table_names()}
        if t not in inspector.get_table_names():
            result["issues"].append(f"Table {t} manquante")

    engine.dispose()
    return result


# ---------------------------------------------------------------------------
# Metrics — auth optional via METRICS_TOKEN (A05-005 — v0.9.0).
# In production, set METRICS_TOKEN env var. /metrics then requires:
#     Authorization: Bearer <METRICS_TOKEN>
# If METRICS_TOKEN is empty, /metrics is open (dev/local convenience).
# In addition to bearer auth, you can still restrict /metrics at the ingress
# level (e.g. allow only Prometheus' IP) for defense-in-depth.
# ---------------------------------------------------------------------------
metrics_router = APIRouter(tags=["metrics"])


def _verify_metrics_token(authorization: str | None) -> None:
    """Reject the request if METRICS_TOKEN is set and the bearer token does not match.

    Uses `hmac.compare_digest` for constant-time comparison.
    """
    expected = settings.metrics_token
    if not expected:
        # No token configured → open access (dev/local mode).
        return

    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required for /metrics")

    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token required for /metrics")

    if not hmac.compare_digest(parts[1], expected):
        raise HTTPException(status_code=403, detail="Invalid metrics token")


@metrics_router.get("/metrics")
def metrics(authorization: str | None = Header(default=None)):
    """Prometheus text exposition format.

    When METRICS_TOKEN is configured, requires `Authorization: Bearer <token>`.
    """
    _verify_metrics_token(authorization)
    body = render_prometheus()
    from starlette.responses import PlainTextResponse
    return PlainTextResponse(body, media_type="text/plain; version=0.0.4; charset=utf-8")
