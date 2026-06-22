"""Pydantic schemas for the audit log API."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    user_id: str | None = None
    facility_id: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    http_method: str | None = None
    http_path: str | None = None
    status_code: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    payload: Any = None
