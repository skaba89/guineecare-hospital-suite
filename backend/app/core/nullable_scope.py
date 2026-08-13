"""Helpers for resources that support both national defaults and facility overrides."""

from fastapi import HTTPException


def normalize_facility_override(current_user, requested_facility_id: str | None) -> str | None:
    """Facility users create local overrides; SUPER_ADMIN may create national defaults."""
    if current_user.role == "SUPER_ADMIN":
        return requested_facility_id
    return current_user.facility_id


def require_national_default_admin(current_user, facility_id: str | None) -> None:
    """National default rows (facility_id NULL) are mutable only by SUPER_ADMIN."""
    if facility_id is None and current_user.role != "SUPER_ADMIN":
        raise HTTPException(
            status_code=403,
            detail="Les valeurs nationales par défaut sont gérées uniquement par SUPER_ADMIN",
        )
