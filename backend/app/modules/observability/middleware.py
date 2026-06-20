"""HTTP middleware that records request metrics for Prometheus.

Routed path templates (e.g. /patients/{patient_id}) are preferred over raw URLs
to avoid label cardinality explosion. If FastAPI hasn't populated
`request.scope["route"]`, we fall back to the raw path.
"""
import time
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.modules.observability.metrics import observe_request_end, observe_request_start

logger = logging.getLogger("guineecare.metrics")


def _path_template(request: Request) -> str:
    """Return the route template if known, else the raw path.

    Examples:
        /patients/abc-123  ->  /patients/{patient_id}
        /api/v1/health     ->  /api/v1/health
    """
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself — we don't want to measure the scraper
        if request.url.path in {"/metrics", "/health", "/health/live", "/health/ready"}:
            return await call_next(request)

        observe_request_start()
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            # Re-raise — let FastAPI's exception handlers deal with it
            status_code = 500
            raise
        finally:
            duration = time.perf_counter() - start
            template = _path_template(request)
            try:
                observe_request_end(
                    method=request.method,
                    path_template=template,
                    status=status_code,
                    duration_seconds=duration,
                )
            except Exception as e:
                # Never let metrics recording break a request
                logger.warning("metrics observe failed: %s", e)
