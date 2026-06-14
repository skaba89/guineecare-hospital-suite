from sqlalchemy.orm import Session

from app.modules.activity.models import ActivityEntry


def record_activity(
    db: Session,
    action_name: str,
    actor_id: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    level: str = "NORMAL",
    notes: str | None = None,
):
    entry = ActivityEntry(
        actor_id=actor_id,
        action_name=action_name,
        entity_type=entity_type,
        entity_id=entity_id,
        level=level,
        notes=notes,
    )
    db.add(entry)
    return entry
