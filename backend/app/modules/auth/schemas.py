from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    email: str
    password: str


class UserInfo(BaseModel):
    """Subset of User returned in login/refresh responses."""
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    facility_id: str | None = None
    is_active: bool = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None  # seconds until access_token expires
    user: UserInfo | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class MessageResponse(BaseModel):
    message: str
