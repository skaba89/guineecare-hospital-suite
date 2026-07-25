"""HTTP middleware that records request metrics for Prometheus.

Routed path templates (e.g. /patients/{patient_id}) are preferred over raw URLs
to avoid label cardinality explosion. If FastAPI hasn't populated
`request.scope["route"]`, we fall back to the raw path.

v2.3.0 — Phase 8 : ajoute un X-Request-Id par requête (UUID4) pour
corrélation des logs. L'ID est injecté dans les LogRecord extras et
renvoyé au client via le header X-Request-Id (déjà exposé dans CORS).
"""
import time
import logging
import uuid

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
        # v2.3.0 — Phase 8 : générer ou propager un X-Request-Id pour
        # corrélation des logs. Si le client en fournit un, on le garde
        # (à condition qu'il soit un UUID valide — sinon on en génère un).
        incoming_id = request.headers.get("x-request-id", "")
        try:
            # Valider que c'est un UUID (évite l'injection de logs malveillants)
            uuid.UUID(incoming_id)
            request_id = incoming_id
        except (ValueError, TypeError):
            request_id = str(uuid.uuid4())

        # Stocker dans le scope pour que les handlers downstream puissent le lire
        request.state.request_id = request_id

        # Configurer le logger pour inclure request_id dans tous les logs
        # de cette requête (via LogRecord extras + filter)
        old_extra = getattr(logger, "extra", None)
        logging.LoggerAdapter(logger, {"request_id": request_id})

        # Skip metrics endpoint itself — we don't want to measure the scraper
        if request.url.path in {"/metrics", "/health", "/health/live", "/health/ready"}:
            response = await call_next(request)
            response.headers["X-Request-Id"] = request_id
            return response

        observe_request_start()
        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            # v2.3.0 — Phase 8 : exposer le request_id au client
            response.headers["X-Request-Id"] = request_id
            return response
        except Exception:
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
                logger.warning("metrics observe failed: %s (request_id=%s)", e, request_id)
            # Log structuré de chaque requête (en plus des métriques Prometheus)
            logger.info(
                "%s %s → %d (%.0fms)",
                request.method,
                template,
                status_code,
                duration * 1000,
                extra={"request_id": request_id, "method": request.method,
                       "path": template, "status": status_code,
                       "duration_ms": round(duration * 1000, 1)},
            )
