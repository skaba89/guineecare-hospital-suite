"""Health, readiness, and metrics endpoints.

- GET /health        — backward compat: simple "ok" (kept from v0.1)
- GET /health/live   — liveness probe (process is alive, returns 200 immediately)
- GET /health/ready  — readiness probe (DB is reachable, returns 200/503)
- GET /metrics       — Prometheus text exposition (no auth — protect at ingress level)
"""
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.observability.metrics import render_prometheus

router = APIRouter(prefix="/health", tags=["health"])


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


# ---------------------------------------------------------------------------
# Metrics — exposed WITHOUT authentication, on purpose.
# In production, restrict /metrics to internal traffic at the ingress level
# (e.g. allow only Prometheus' IP). Putting it behind auth breaks Prometheus
# scraping unless you configure bearer auth in prometheus.yml.
# ---------------------------------------------------------------------------
metrics_router = APIRouter(tags=["metrics"])


@metrics_router.get("/metrics")
def metrics():
    """Prometheus text exposition format. Protect at ingress level in prod."""
    from fastapi import Response as FastResponse
    body = render_prometheus()
    # Build a plain-text response with the right content type
    from starlette.responses import PlainTextResponse
    return PlainTextResponse(body, media_type="text/plain; version=0.0.4; charset=utf-8")
