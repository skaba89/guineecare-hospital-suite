"""Health, readiness, and metrics endpoints.

- GET /health        — backward compat: simple "ok" (kept from v0.1)
- GET /health/live   — liveness probe (process is alive, returns 200 immediately)
- GET /health/ready  — readiness probe (DB is reachable, returns 200/503)
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
