"""
Multi-Tenant Row-Level Security (RLS) for GuinéeCare.

Every business table has a `facility_id` column. This module enforces that:
- SUPER_ADMIN can see all facilities (cross-tenant access)
- All other roles can ONLY see data from their own facility
- Facility-scoping is applied at the SQLAlchemy query level automatically

Usage in routes:
    from app.core.tenant import tenant_query

    @router.get("/staff")
    def list_staff(db: Session = Depends(get_db), current_user: User = Depends(require_permission("personnel.read"))):
        query = tenant_query(db, StaffMember, current_user)
        return paginate(query, pagination)
"""

from sqlalchemy.orm import Session, Query

from app.modules.users.models import User


# Roles that have cross-tenant visibility (can see ALL facilities)
CROSS_TENANT_ROLES = {"SUPER_ADMIN"}


def tenant_query(db: Session, model, current_user: User, base_query: Query | None = None) -> Query:
    """Apply tenant filtering to a SQLAlchemy query.

    If the user's role is in CROSS_TENANT_ROLES, no facility filter is applied.
    Otherwise, the query is filtered to only include rows where
    facility_id matches the user's facility_id.

    Args:
        db: Database session
        model: SQLAlchemy model class (must have facility_id column)
        current_user: The authenticated user
        base_query: Optional existing query to filter. If None, creates db.query(model).

    Returns:
        Filtered SQLAlchemy query
    """
    query = base_query or db.query(model)

    # SUPER_ADMIN sees everything
    if current_user.role in CROSS_TENANT_ROLES:
        return query

    # All other roles: only see their facility
    facility_id = current_user.facility_id
    if facility_id is None:
        # User has no facility assigned - return empty result set
        return query.filter(model.facility_id == "__NO_FACILITY__")

    if hasattr(model, "facility_id"):
        return query.filter(model.facility_id == facility_id)

    # Model doesn't have facility_id - return as-is (e.g., global lookup tables)
    return query


def enforce_facility_access(current_user: User, target_facility_id: str | None) -> None:
    """Verify that the current user is allowed to access data for a given facility.

    Raises HTTPException(403) if the user doesn't have access.

    Args:
        current_user: The authenticated user
        target_facility_id: The facility being accessed
    """
    from fastapi import HTTPException

    if current_user.role in CROSS_TENANT_ROLES:
        return  # SUPER_ADMIN can access any facility

    if target_facility_id and target_facility_id != current_user.facility_id:
        raise HTTPException(
            status_code=403,
            detail="Accès interdit : vous ne pouvez accéder qu'aux données de votre établissement",
        )


def get_user_facility_id(current_user: User) -> str | None:
    """Get the facility_id for the current user, or None for cross-tenant users."""
    if current_user.role in CROSS_TENANT_ROLES:
        return None  # Cross-tenant, no single facility
    return current_user.facility_id
