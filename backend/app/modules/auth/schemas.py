from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    secret: str = Field(alias="password")

    @property
    def password(self) -> str:
        return self.secret


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
