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
    db: Session = Depends(get_db),
    # SECURITY (A01-002): ActivityEntry has no facility_id column, so the
    # table is global. We restrict to SUPER_ADMIN only. Facility-scoped
    # ADMINs cannot read cross-tenant activity.
    current_user: User = Depends(require_role("SUPER_ADMIN")),
):
    query = db.query(ActivityEntry).order_by(ActivityEntry.created_at.desc())
    if pagination.search:
        query = query.filter(
            (ActivityEntry.action_name.ilike(f"%{pagination.search}%"))
            | (ActivityEntry.entity_type.ilike(f"%{pagination.search}%"))
        )
    return paginate(query, pagination)
