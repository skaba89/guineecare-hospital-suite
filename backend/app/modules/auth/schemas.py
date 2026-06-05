from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    secret: str

    @property
    def password(self) -> str:
        return self.secret


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
