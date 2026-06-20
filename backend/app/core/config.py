import os
import json
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = os.environ.get("APP_NAME", "GuineeCare Hospital Suite")
    environment: str = os.environ.get("ENVIRONMENT", "local")
    api_prefix: str = os.environ.get("API_PREFIX", "/api/v1")
    database_url: str = os.environ.get("DATABASE_URL", "postgresql://guineecare:guineecare@localhost:5432/guineecare")
    auth_secret: str = os.environ.get("AUTH_SECRET", "")
    auth_algorithm: str = os.environ.get("AUTH_ALGORITHM", "HS256")
    token_expire_minutes: int = int(os.environ.get("TOKEN_EXPIRE_MINUTES", "60"))
    cors_origins: list[str] = []

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
