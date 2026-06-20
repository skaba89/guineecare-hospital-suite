import ipaddress
import os
import json
from pydantic import BaseModel


def _parse_trusted_proxies(raw: str) -> list[str]:
    """Parse TRUSTED_PROXIES env var.

    Accepts comma-separated list of IPs or CIDRs, e.g.
    "10.0.0.1,172.16.0.0/12,192.168.0.0/16".
    Empty string → empty list (no proxy trusted).
    """
    if not raw:
        return []
    out: list[str] = []
    for part in raw.split(","):
        part = part.strip()
        if part:
            out.append(part)
    return out


class Settings(BaseModel):
    app_name: str = os.environ.get("APP_NAME", "GuineeCare Hospital Suite")
    environment: str = os.environ.get("ENVIRONMENT", "local")
    api_prefix: str = os.environ.get("API_PREFIX", "/api/v1")
    database_url: str = os.environ.get("DATABASE_URL", "postgresql://guineecare:guineecare@localhost:5432/guineecare")
    auth_secret: str = os.environ.get("AUTH_SECRET", "")
    auth_algorithm: str = os.environ.get("AUTH_ALGORITHM", "HS256")
    token_expire_minutes: int = int(os.environ.get("TOKEN_EXPIRE_MINUTES", "60"))
    cors_origins: list[str] = []
    # Trusted proxy CIDRs — only IPs in these ranges may set X-Forwarded-For.
    # A05-001 hardening: prevents X-Forwarded-For spoofing when backend is
    # directly exposed. Empty list = no proxy trusted (use raw remote_addr).
    trusted_proxies: list[str] = _parse_trusted_proxies(os.environ.get("TRUSTED_PROXIES", ""))
    # Optional bearer token for /metrics endpoint (A05-005 hardening).
    # When set, /metrics requires `Authorization: Bearer <token>`.
    metrics_token: str = os.environ.get("METRICS_TOKEN", "")
    # Bootstrap token (A05-004). When set, POST /users/bootstrap requires
    # `X-Bootstrap-Token: <token>`. If empty, bootstrap endpoint is disabled
    # in non-local envs (use CLI `python -m app.cli create-superuser` instead).
    bootstrap_token: str = os.environ.get("BOOTSTRAP_TOKEN", "")

    def model_post_init(self, __context) -> None:
        if not self.cors_origins:
            cors_env = os.environ.get("CORS_ORIGINS", "")
            if cors_env:
                try:
                    self.cors_origins = json.loads(cors_env)
                except json.JSONDecodeError:
                    self.cors_origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
            else:
                self.cors_origins = ["http://localhost:5173", "http://localhost:3000"]


def is_ip_trusted(remote_addr: str | None, trusted_proxies: list[str]) -> bool:
    """Return True if remote_addr matches one of the trusted proxy CIDRs.

    Empty trusted_proxies → always False (no IP forwarding trust).
    """
    if not remote_addr or not trusted_proxies:
        return False
    try:
        ip = ipaddress.ip_address(remote_addr)
    except ValueError:
        return False
    for entry in trusted_proxies:
        try:
            if "/" in entry:
                network = ipaddress.ip_network(entry, strict=False)
                if ip in network:
                    return True
            else:
                if ip == ipaddress.ip_address(entry):
                    return True
        except ValueError:
            continue
    return False


def validate_settings() -> None:
    """Validate critical settings at startup.

    SECURITY (A05-003): in non-local environments, missing AUTH_SECRET is a
    hard failure that must terminate the process. main.py catches RuntimeError
    but continues, so we sys.exit() directly here for non-local envs.
    """
    if not settings.auth_secret:
        if settings.environment == "local":
            # Dev convenience: allow empty secret in local, but warn loudly
            import warnings
            warnings.warn(
                "AUTH_SECRET is empty in local environment. "
                "JWTs are signed with an empty string and trivially forgeable. "
                "Set AUTH_SECRET for any non-loopback access.",
                RuntimeWarning,
                stacklevel=2,
            )
        else:
            import sys
            print(
                "FATAL: AUTH_SECRET must be set when ENVIRONMENT is not 'local'. "
                "Refusing to start. Set the AUTH_SECRET environment variable.",
                file=sys.stderr,
            )
            sys.exit(1)


settings = Settings()
