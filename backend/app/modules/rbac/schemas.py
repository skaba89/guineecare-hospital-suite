from pydantic import BaseModel


class RoleCreate(BaseModel):
    code: str
    name: str
    description: str | None = None


class PermissionCreate(BaseModel):
    code: str
    name: str
    module: str


class RolePermissionCreate(BaseModel):
    role_code: str
    permission_code: str
