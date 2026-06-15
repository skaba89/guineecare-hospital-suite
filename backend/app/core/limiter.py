from slowapi import Limiter
from slowapi.util import get_remote_address


def get_client_ip(request) -> str:
    """Extract real client IP from X-Forwarded-For / X-Real-IP headers.
    Behind nginx reverse proxy, get_remote_address returns the proxy IP,
    causing all users to share a single rate-limit bucket.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return get_remote_address(request)


# Shared rate-limiter instance used across the application.
limiter = Limiter(key_func=get_client_ip)
