import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = os.environ.get("APP_NAME", "GuineeCare Hospital Suite")
    environment: str = os.environ.get("ENVIRONMENT", "local")
    api_prefix: str = os.environ.get("API_PREFIX", "/api/v1")
    database_url: str = os.environ.get("DATABASE_URL", "postgresql://guineecare:guineecare@localhost:5432/guineecare")


settings = Settings()
