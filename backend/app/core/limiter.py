import logging

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import is_ip_trusted, settings

logger = logging.getLogger("guineecare.limiter")


def _build_limiter() -> Limiter:
    """Construit le Limiter avec Redis storage si configuré, sinon mémoire.

    v2.9.2 — Rate limit partagé multi-instance :
    Quand REDIS_URL est configurée et joignable, on remplace le storage
    in-memory par défaut par un storage Redis. Cela permet à plusieurs
    workers/instances (Render multi-instance, Kubernetes replicas) de
    partager le même compteur de rate limit.

    En dev/test (REDIS_URL vide), on reste en mémoire — pas de dépendance
    Redis requise pour faire tourner les tests.
    """
    # Construction initiale en mémoire (toujours disponible)
    lim = Limiter(key_func=get_client_ip)

    # Tentative de branchement Redis (best-effort, non bloquant)
    try:
        from app.core.redis import get_rate_limit_storage
        storage = get_rate_limit_storage()
        if storage is not None:
            lim._limiter.storage = storage
            logger.info("Rate limiter: storage Redis branché (partagé multi-instance)")
        else:
            logger.debug("Rate limiter: storage mémoire (par worker)")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Rate limiter: Redis init échoué (%s) — fallback mémoire", exc)

    return lim


def get_client_ip(request) -> str:
    """Extract real client IP from X-Forwarded-For / X-Real-IP headers.

    SECURITY (A05-001 — v0.9.0): only trust forwarded headers when the
    request's direct remote address is in `TRUSTED_PROXIES`. If the
    backend is exposed directly (no proxy), an attacker could spoof
    `X-Forwarded-For` to bypass the rate-limiter. By requiring an
    explicit allowlist of proxy CIDRs, we close that vector.

    If `TRUSTED_PROXIES` is empty (default), we fall back to the raw
    remote address — this preserves dev/local behavior.
    """
    remote_addr = request.client.host if request.client else None

    # Only trust forwarded headers when the immediate peer is a known proxy.
    if is_ip_trusted(remote_addr, settings.trusted_proxies):
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For: client, proxy1, proxy2 — left-most is the client.
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

    # No trusted proxy → use the direct peer address.
    return get_remote_address(request)


# Shared rate-limiter instance used across the application.
# v2.9.2 — Initialise avec Redis storage si REDIS_URL est configurée,
# sinon en mémoire (par worker). Voir _build_limiter pour le détail.
limiter = _build_limiter()
