"""i18n translation service — v1.3.0.

Design choices:
- Catalogs are Python dicts (not JSON files) so they ship with the source
  and benefit from type checking. Adding a locale = adding a dict.
- Keys are dotted strings (`auth.login.invalid_credentials`). Nested dicts
  in the catalog are flattened on load.
- Missing keys fall back to French, then to the key itself. This avoids
  `KeyError` explosions in production but the missing-key event is logged
  at WARNING level so the i18n gap is visible.
- Variable interpolation uses `str.format_map` with a `defaultdict(str)`
  wrapper so missing variables render as empty strings rather than raising.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("guineecare.i18n")

DEFAULT_LOCALE = "fr"
SUPPORTED_LOCALES = ("fr", "en")


# --- French catalog (default) ---
_CATALOG_FR: dict[str, str] = {
    # Auth
    "auth.login.invalid_credentials": "Identifiants invalides.",
    "auth.login.account_locked": "Compte verrouillé après {attempts} échecs. Réessayez dans {minutes} minutes.",
    "auth.login.success": "Connexion réussie.",
    "auth.logout.success": "Déconnexion réussie.",
    "auth.refresh.invalid": "Token de rafraîchissement invalide ou expiré.",
    "auth.token.expired": "Token expiré.",
    "auth.token.invalid": "Token invalide.",
    "auth.token.revoked": "Token révoqué (jti blacklisté).",
    "auth.not_authenticated": "Non authentifié.",
    # RBAC
    "rbac.permission_denied": "Permission insuffisante : {permission} requis.",
    "rbac.role_required": "Rôle insuffisant : {role} requis.",
    # Multi-tenant
    "tenant.access_denied": "Accès à l'établissement {facility_id} refusé.",
    # Common
    "common.not_found": "Ressource introuvable.",
    "common.conflict": "Conflit — la ressource existe déjà ou est dans un état invalide.",
    "common.validation_error": "Erreur de validation.",
    "common.internal_error": "Erreur serveur interne.",
    "common.rate_limited": "Trop de requêtes. Réessayez dans {seconds}s.",
    # Patients
    "patient.duplicate_number": "Numéro patient déjà utilisé : {patient_number}.",
    "patient.not_found": "Patient introuvable (id={patient_id}).",
    # Documents
    "documents.invalid_note_type": "Type de note invalide — PRESCRIPTION requis, reçu : {actual}.",
    "documents.not_found": "Document source introuvable.",
    # Feedback
    "feedback.not_found": "Feedback introuvable.",
    # i18n
    "i18n.unsupported_locale": "Langue non supportée : {locale}. Langues supportées : {supported}.",
}


# --- English catalog ---
_CATALOG_EN: dict[str, str] = {
    # Auth
    "auth.login.invalid_credentials": "Invalid credentials.",
    "auth.login.account_locked": "Account locked after {attempts} failed attempts. Try again in {minutes} minutes.",
    "auth.login.success": "Login successful.",
    "auth.logout.success": "Logout successful.",
    "auth.refresh.invalid": "Invalid or expired refresh token.",
    "auth.token.expired": "Token expired.",
    "auth.token.invalid": "Invalid token.",
    "auth.token.revoked": "Token revoked (jti blacklisted).",
    "auth.not_authenticated": "Not authenticated.",
    # RBAC
    "rbac.permission_denied": "Insufficient permission: {permission} required.",
    "rbac.role_required": "Insufficient role: {role} required.",
    # Multi-tenant
    "tenant.access_denied": "Access to facility {facility_id} denied.",
    # Common
    "common.not_found": "Resource not found.",
    "common.conflict": "Conflict — resource already exists or is in an invalid state.",
    "common.validation_error": "Validation error.",
    "common.internal_error": "Internal server error.",
    "common.rate_limited": "Too many requests. Try again in {seconds}s.",
    # Patients
    "patient.duplicate_number": "Patient number already in use: {patient_number}.",
    "patient.not_found": "Patient not found (id={patient_id}).",
    # Documents
    "documents.invalid_note_type": "Invalid note type — PRESCRIPTION required, got: {actual}.",
    "documents.not_found": "Source document not found.",
    # Feedback
    "feedback.not_found": "Feedback not found.",
    # i18n
    "i18n.unsupported_locale": "Unsupported locale: {locale}. Supported: {supported}.",
}


_CATALOGS: dict[str, dict[str, str]] = {
    "fr": _CATALOG_FR,
    "en": _CATALOG_EN,
}


class _SafeDict(dict):
    """dict subclass that returns '' for missing keys (for str.format_map)."""

    def __missing__(self, key: str) -> str:
        return ""


def negotiate_locale(accept_language: str | None) -> str:
    """Map an `Accept-Language` header value to a supported locale.

    Examples:
    - `"fr-FR,fr;q=0.9,en;q=0.8"` → `"fr"`
    - `"en-US,en;q=0.9"` → `"en"`
    - `None` / `""` / `"de-DE"` → `DEFAULT_LOCALE`

    Algorithm: parse the header, sort by quality, return the first
    language whose primary subtag matches a supported locale. Falls
    back to DEFAULT_LOCALE.
    """
    if not accept_language:
        return DEFAULT_LOCALE

    # Parse "fr-FR,fr;q=0.9,en;q=0.8" → [("fr-FR", 1.0), ("fr", 0.9), ("en", 0.8)]
    entries: list[tuple[str, float]] = []
    for part in accept_language.split(","):
        part = part.strip()
        if not part:
            continue
        if ";" in part:
            lang, params = part.split(";", 1)
            q = 1.0
            for p in params.split(";"):
                p = p.strip()
                if p.startswith("q="):
                    try:
                        q = float(p[2:])
                    except ValueError:
                        q = 1.0
            entries.append((lang.strip().lower(), q))
        else:
            entries.append((part.lower(), 1.0))

    # Sort by descending quality
    entries.sort(key=lambda e: e[1], reverse=True)

    for lang, _ in entries:
        # Take the primary subtag ("fr-fr" → "fr")
        primary = lang.split("-")[0]
        if primary in SUPPORTED_LOCALES:
            return primary

    return DEFAULT_LOCALE


def translate(key: str, locale: str | None = None, **variables: Any) -> str:
    """Translate a dotted key into the negotiated locale.

    Resolution order:
    1. Look up `key` in the catalog for `locale`.
    2. If missing, fall back to the DEFAULT_LOCALE catalog.
    3. If still missing, return the key itself and log a warning.

    Variables are interpolated via `str.format_map` with a safe dict
    (missing variables render as empty strings, no KeyError).
    """
    loc = locale if locale in SUPPORTED_LOCALES else DEFAULT_LOCALE
    catalog = _CATALOGS.get(loc, _CATALOG_FR)

    value = catalog.get(key)
    if value is None:
        # Fallback to default locale
        if loc != DEFAULT_LOCALE:
            value = _CATALOG_FR.get(key)
        if value is None:
            logger.warning("i18n.missing_key key=%s locale=%s", key, loc)
            return key

    if variables:
        try:
            return value.format_map(_SafeDict(variables))
        except (IndexError, ValueError):
            logger.warning("i18n.format_error key=%s locale=%s vars=%s", key, loc, variables)
            return value
    return value


def get_catalog(locale: str) -> dict[str, str]:
    """Return the full catalog for a locale (or the default if unsupported)."""
    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"Unsupported locale: {locale}")
    return dict(_CATALOGS[locale])
