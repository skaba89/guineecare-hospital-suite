from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validate_password_complexity(password: str) -> str:
    """Enforce strong password policy:
    - At least 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character (!@#$%^&*()-_=+[]{}|;:,.<>?)

    Raises ValueError on failure. Returns the password unchanged on success.
    """
    if len(password) < 12:
        raise ValueError("Le mot de passe doit contenir au moins 12 caractères")
    if not any(c.isupper() for c in password):
        raise ValueError("Le mot de passe doit contenir au moins une majuscule")
    if not any(c.islower() for c in password):
        raise ValueError("Le mot de passe doit contenir au moins une minuscule")
    if not any(c.isdigit() for c in password):
        raise ValueError("Le mot de passe doit contenir au moins un chiffre")
    special = "!@#$%^&*()-_=+[]{}|;:,.<>?"
    if not any(c in special for c in password):
        raise ValueError("Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*()-_=+[]{}|;:,.<>?)")
    return password


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    facility_id: str | None = None
    role: str = "USER"

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        return _validate_password_complexity(v)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=12)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    facility_id: str | None = None
    role: str | None = None
    is_active: bool | None = None

    @field_validator("password")
    @classmethod
    def _strong_password(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return _validate_password_complexity(v)


class UserRead(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    facility_id: str | None = None
    role: str
    is_active: bool
    created_at: str | None = None  # ISO format string

    model_config = ConfigDict(from_attributes=True)
