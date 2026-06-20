from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import is_ip_trusted, settings


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
limiter = Limiter(key_func=get_client_ip)
