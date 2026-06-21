from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import PaginationParams, paginate
from app.db.session import get_db
from app.modules.activity.models import ActivityEntry
from app.modules.rbac.dependencies import require_role
from app.modules.users.models import User

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("")
def list_activity(
    pagination: PaginationParams = Depends(),
    actor_id: str | None = None,
    action_name: str | None = None,
    entity_type: str | None = None,
    level: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    db: Session = Depends(get_db),
    # SECURITY (A01-002): ActivityEntry has no facility_id column, so the
    # table is global. We restrict to SUPER_ADMIN only. Facility-scoped
    # ADMINs cannot read cross-tenant activity.
    current_user: User = Depends(require_role("SUPER_ADMIN")),
):
    """Liste paginée des entrées d'activité avec filtres serveur.

    Filtres : `actor_id`, `action_name`, `entity_type`, `level`,
    `date_from`/`date_to` (sur created_at), `search`.
    """
    query = db.query(ActivityEntry).order_by(ActivityEntry.created_at.desc())
    if pagination.search:
        query = query.filter(
            (ActivityEntry.action_name.ilike(f"%{pagination.search}%"))
            | (ActivityEntry.entity_type.ilike(f"%{pagination.search}%"))
        )
    if actor_id:
        query = query.filter(ActivityEntry.actor_id == actor_id)
    if action_name:
        query = query.filter(ActivityEntry.action_name == action_name)
    if entity_type:
        query = query.filter(ActivityEntry.entity_type == entity_type)
    if level:
        query = query.filter(ActivityEntry.level == level.upper())
    if date_from:
        try:
            from datetime import datetime as _dt
            query = query.filter(ActivityEntry.created_at >= _dt.fromisoformat(date_from))
        except ValueError:
            pass
    if date_to:
        try:
            from datetime import datetime as _dt
            query = query.filter(ActivityEntry.created_at <= _dt.fromisoformat(date_to))
        except ValueError:
            pass
    return paginate(query, pagination)
