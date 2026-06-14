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
    """Validate critical settings at startup."""
    if not settings.auth_secret and settings.environment != "local":
        raise RuntimeError(
            "AUTH_SECRET must be set when ENVIRONMENT is not 'local'. "
            "Refusing to start without a proper secret in production/staging."
        )


settings = Settings()
