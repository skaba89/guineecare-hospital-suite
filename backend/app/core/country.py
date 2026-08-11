"""Country profiles for national and multi-country deployments.

GuinéeCare is Guinea-first, but country-specific rules must not leak into
shared clinical code. This module centralises deployment defaults and the
administrative/health hierarchy used by APIs, integrations and UI labels.

Adding another country should only require registering another CountryProfile
(and, where needed, a dedicated integration adapter), without changing the
core patient or clinical models.
"""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class AdministrativeLevel:
    key: str
    label: str


@dataclass(frozen=True)
class CountryProfile:
    code: str
    name: str
    currency_code: str
    phone_country_code: str
    timezone: str
    default_locale: str
    supported_locales: tuple[str, ...]
    administrative_levels: tuple[AdministrativeLevel, ...]
    health_system_levels: tuple[AdministrativeLevel, ...]
    national_integrations: tuple[str, ...] = ()


GUINEA_PROFILE = CountryProfile(
    code="GN",
    name="Guinée",
    currency_code="GNF",
    phone_country_code="+224",
    timezone="Africa/Conakry",
    default_locale="fr",
    # Keep this aligned with the translation catalog currently shipped by the app.
    supported_locales=("fr", "en"),
    administrative_levels=(
        AdministrativeLevel("admin_level_1", "Région"),
        AdministrativeLevel("admin_level_2", "Préfecture / Zone spéciale"),
        AdministrativeLevel("admin_level_3", "Commune"),
        AdministrativeLevel("admin_level_4", "Quartier / District"),
    ),
    health_system_levels=(
        AdministrativeLevel("national", "National"),
        AdministrativeLevel("health_region", "Région sanitaire"),
        AdministrativeLevel("health_district", "District sanitaire"),
        AdministrativeLevel("facility", "Formation sanitaire"),
        AdministrativeLevel("community", "Communauté"),
    ),
    national_integrations=(
        "DHIS2_SISR",
        "DHIS2_SURVEILLANCE",
        "DHIS2_PEV",
        "E_SIGL",
        "IHRIS",
    ),
)


COUNTRY_PROFILES: dict[str, CountryProfile] = {
    GUINEA_PROFILE.code: GUINEA_PROFILE,
}


def _generic_profile(country_code: str) -> CountryProfile:
    """Return a safe generic profile for a country not registered yet.

    This deliberately avoids inventing country-specific administrative names.
    Deployments can start with generic levels, then register a precise profile.
    """
    return CountryProfile(
        code=country_code,
        name=country_code,
        currency_code="",
        phone_country_code="",
        timezone="UTC",
        default_locale="fr",
        supported_locales=("fr", "en"),
        administrative_levels=(
            AdministrativeLevel("admin_level_1", "Niveau administratif 1"),
            AdministrativeLevel("admin_level_2", "Niveau administratif 2"),
            AdministrativeLevel("admin_level_3", "Niveau administratif 3"),
            AdministrativeLevel("admin_level_4", "Niveau administratif 4"),
        ),
        health_system_levels=(
            AdministrativeLevel("national", "National"),
            AdministrativeLevel("health_region", "Région sanitaire"),
            AdministrativeLevel("health_district", "District sanitaire"),
            AdministrativeLevel("facility", "Établissement"),
            AdministrativeLevel("community", "Communauté"),
        ),
    )


def get_country_profile(country_code: str | None = None) -> CountryProfile:
    """Resolve the active country profile.

    COUNTRY_CODE defaults to GN so existing GuinéeCare installations retain
    their current Guinea-first behaviour without additional configuration.
    Unknown ISO-like codes receive a generic profile instead of crashing.
    """
    code = (country_code or os.environ.get("COUNTRY_CODE", "GN")).strip().upper()
    if not code:
        code = "GN"
    return COUNTRY_PROFILES.get(code, _generic_profile(code))


def register_country_profile(profile: CountryProfile) -> None:
    """Register or replace a country profile at process startup."""
    COUNTRY_PROFILES[profile.code.upper()] = profile
