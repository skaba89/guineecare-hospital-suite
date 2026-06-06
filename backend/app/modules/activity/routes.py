from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.activity.models import ActivityEntry
from app.modules.rbac.dependencies import require_role
from app.modules.users.models import User

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("")
def list_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["SUPER_ADMIN", "ADMIN"])),
):
    rows = db.query(ActivityEntry).order_by(ActivityEntry.created_at.desc()).limit(200).all()
    return {"data": rows, "message": "activity list"}
