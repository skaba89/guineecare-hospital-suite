"""Routes for the user_profile module — preferences, feedback, recent items.

All endpoints are JWT-protected (no public paths). Endpoints under
`/me/*` are scoped to the current user. The `/feedback` collection
endpoint allows ADMIN+ to list all feedback in their facility (or all
facilities for SUPER_ADMIN) and to triage / resolve entries.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.tenant import enforce_facility_access
from app.db.session import get_db
from app.modules.audit.service import audit_log
from app.modules.auth.dependencies import get_current_user
from app.modules.rbac.dependencies import require_permission
from app.modules.user_profile.models import (
    MAX_RECENT_ITEMS,
    UserFeedback,
    UserPreference,
    UserRecentItem,
)
from app.modules.user_profile.schemas import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackRead,
    FeedbackResolve,
    RecentItemCreate,
    RecentItemListResponse,
    RecentItemRead,
    UserPreferencesRead,
    UserPreferencesUpdate,
)
from app.modules.users.models import User

router = APIRouter(prefix="/me", tags=["user-profile"])
feedback_router = APIRouter(prefix="/feedback", tags=["feedback"])


# ---------------------------------------------------------------------------
# Preferences — GET / PUT /me/preferences
# ---------------------------------------------------------------------------

def _get_or_create_preferences(db: Session, user_id: str) -> UserPreference:
    row = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
    if row is None:
        row = UserPreference(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


@router.get("/preferences", response_model=UserPreferencesRead)
def get_my_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's UI preferences.

    Returns defaults (locale=fr, theme=light, page_size=20, refresh=30s)
    if the user has never customized their preferences.
    """
    row = _get_or_create_preferences(db, current_user.id)
    return UserPreferencesRead.model_validate(row.to_dict())


@router.put("/preferences", response_model=UserPreferencesRead)
def update_my_preferences(
    payload: UserPreferencesUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's UI preferences (partial update)."""
    row = _get_or_create_preferences(db, current_user.id)
    before = row.to_dict()

    data = payload.model_dump(exclude_unset=True)
    extra = data.pop("extra", None)
    for key, value in data.items():
        setattr(row, key, value)
    if extra is not None:
        row.set_extra(extra)

    db.commit()
    db.refresh(row)

    audit_log(
        db=db,
        user=current_user,
        action="user.preferences.update",
        resource_type="user_preferences",
        resource_id=current_user.id,
        request=request,
        status_code=200,
        payload={"before": before, "after": row.to_dict()},
    )
    return UserPreferencesRead.model_validate(row.to_dict())


# ---------------------------------------------------------------------------
# Feedback — POST /feedback, GET /feedback, PATCH /feedback/{id}
# ---------------------------------------------------------------------------

@feedback_router.post("", response_model=FeedbackRead, status_code=201)
def submit_feedback(
    payload: FeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a feedback entry (bug, suggestion, question, praise).

    Any authenticated user can submit. The user_agent and IP are captured
    automatically from the request for diagnostic purposes (the IP is
    stored in the audit log, not in the feedback row).
    """
    ua = request.headers.get("user-agent")
    if ua and len(ua) > 512:
        ua = ua[:512]

    entry = UserFeedback(
        user_id=current_user.id,
        facility_id=current_user.facility_id,
        category=payload.category,
        priority=payload.priority,
        subject=payload.subject,
        message=payload.message,
        page_url=payload.page_url,
        user_agent=ua,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    audit_log(
        db=db,
        user=current_user,
        action="feedback.create",
        resource_type="user_feedback",
        resource_id=entry.id,
        request=request,
        status_code=201,
        payload={"category": entry.category, "priority": entry.priority, "subject": entry.subject},
    )
    return FeedbackRead.model_validate(entry.to_dict())


@feedback_router.get("", response_model=FeedbackListResponse)
def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    category: str | None = Query(None),
    status: str | None = Query(None),
    facility_id: str | None = Query(None),
    mine: bool = Query(False, description="Limit to feedback submitted by the current user"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List feedback entries.

    - `mine=true` — any authenticated user can list their own feedback.
    - Otherwise — requires `feedback.read` permission (SUPER_ADMIN / ADMIN bypass).
      ADMIN is restricted to their facility; SUPER_ADMIN sees all.
    """
    q = db.query(UserFeedback)

    if mine:
        q = q.filter(UserFeedback.user_id == current_user.id)
    else:
        # RBAC: only roles with feedback.read can list others' feedback
        if current_user.role not in ("SUPER_ADMIN", "ADMIN"):
            # Check explicit permission — but to keep this simple and avoid
            # pulling require_permission into a GET, we enforce that non-admin
            # roles can only see their own (mine=true fallback).
            q = q.filter(UserFeedback.user_id == current_user.id)
        elif current_user.role == "ADMIN":
            # ADMIN scoped to their facility
            q = q.filter(UserFeedback.facility_id == current_user.facility_id)
        # SUPER_ADMIN: no filter

    if category:
        q = q.filter(UserFeedback.category == category)
    if status:
        q = q.filter(UserFeedback.status == status)
    if facility_id:
        # Only SUPER_ADMIN can filter by arbitrary facility_id
        if current_user.role != "SUPER_ADMIN":
            enforce_facility_access(current_user, facility_id)
        q = q.filter(UserFeedback.facility_id == facility_id)

    total = q.count()
    rows = (
        q.order_by(UserFeedback.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return FeedbackListResponse(
        data=[FeedbackRead.model_validate(r.to_dict()) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@feedback_router.patch("/{feedback_id}", response_model=FeedbackRead)
def resolve_feedback(
    feedback_id: str,
    payload: FeedbackResolve,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("feedback.resolve")),
):
    """Triage / resolve a feedback entry (ADMIN+ only).

    Requires the `feedback.resolve` permission. ADMIN is scoped to their
    facility; SUPER_ADMIN can resolve any entry.
    """
    entry = db.query(UserFeedback).filter(UserFeedback.id == feedback_id).first()
    if entry is None:
        raise HTTPException(status_code=404, detail="Feedback introuvable")

    # Enforce tenant access
    if entry.facility_id and current_user.role != "SUPER_ADMIN":
        enforce_facility_access(current_user, entry.facility_id)

    before_status = entry.status
    entry.status = payload.status
    entry.admin_response = payload.admin_response
    if payload.status in ("resolved", "wontfix") and entry.resolved_at is None:
        entry.resolved_at = datetime.utcnow()
        entry.resolved_by = current_user.id
    elif payload.status == "open":
        entry.resolved_at = None
        entry.resolved_by = None

    db.commit()
    db.refresh(entry)

    audit_log(
        db=db,
        user=current_user,
        action="feedback.resolve",
        resource_type="user_feedback",
        resource_id=entry.id,
        request=request,
        status_code=200,
        payload={"before_status": before_status, "after_status": entry.status},
    )
    return FeedbackRead.model_validate(entry.to_dict())


# ---------------------------------------------------------------------------
# Recent items — GET / POST /me/recent
# ---------------------------------------------------------------------------

@router.get("/recent", response_model=RecentItemListResponse)
def list_my_recent_items(
    resource_type: str | None = Query(None, description="Filter by resource type"),
    limit: int = Query(20, ge=1, le=MAX_RECENT_ITEMS),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the current user's most-recently-viewed items (sliding window)."""
    q = db.query(UserRecentItem).filter(UserRecentItem.user_id == current_user.id)
    if resource_type:
        q = q.filter(UserRecentItem.resource_type == resource_type)
    rows = (
        q.order_by(UserRecentItem.viewed_at.desc())
        .limit(limit)
        .all()
    )
    return RecentItemListResponse(
        data=[RecentItemRead.model_validate(r.to_dict()) for r in rows],
        total=len(rows),
    )


@router.post("/recent", response_model=RecentItemRead, status_code=201)
def record_recent_item(
    payload: RecentItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record that the current user viewed a resource.

    Re-visiting the same resource bubbles it to the top (unique constraint
    on user_id + resource_type + resource_id → upsert). The sliding window
    is pruned to MAX_RECENT_ITEMS rows per user.
    """
    # Try to find existing entry for the same (user, resource_type, resource_id)
    existing = (
        db.query(UserRecentItem)
        .filter(
            and_(
                UserRecentItem.user_id == current_user.id,
                UserRecentItem.resource_type == payload.resource_type,
                UserRecentItem.resource_id == payload.resource_id,
            )
        )
        .first()
    )
    if existing is not None:
        # Bubble to top
        existing.viewed_at = datetime.utcnow()
        if payload.resource_label is not None:
            existing.resource_label = payload.resource_label
        db.commit()
        db.refresh(existing)
        return RecentItemRead.model_validate(existing.to_dict())

    entry = UserRecentItem(
        user_id=current_user.id,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        resource_label=payload.resource_label,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    # Prune: keep only the MAX_RECENT_ITEMS most recent for this user
    all_rows = (
        db.query(UserRecentItem)
        .filter(UserRecentItem.user_id == current_user.id)
        .order_by(UserRecentItem.viewed_at.desc())
        .all()
    )
    if len(all_rows) > MAX_RECENT_ITEMS:
        for stale in all_rows[MAX_RECENT_ITEMS:]:
            db.delete(stale)
        db.commit()

    return RecentItemRead.model_validate(entry.to_dict())


@router.delete("/recent", status_code=204)
def clear_my_recent_items(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Clear all recent-item history for the current user."""
    db.query(UserRecentItem).filter(UserRecentItem.user_id == current_user.id).delete()
    db.commit()
    return None
