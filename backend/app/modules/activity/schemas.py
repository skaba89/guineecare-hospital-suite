from pydantic import BaseModel


class ActivityRead(BaseModel):
    id: str
    actor_id: str | None = None
    action_name: str
    entity_type: str | None = None
    entity_id: str | None = None
    level: str
    notes: str | None = None

    class Config:
        from_attributes = True
