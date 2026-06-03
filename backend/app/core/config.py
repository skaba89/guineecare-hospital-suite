from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "GuinéeCare Hospital Suite"
    environment: str = "local"
    api_prefix: str = "/api/v1"
    database_url: str = "postgresql://guineecare:guineecare@localhost:5432/guineecare"


settings = Settings()
