"""Internationalization (i18n) module — v1.3.0.

Provides:
- A translation service (`translate(key, locale, **vars)`) that resolves a
  dotted key (e.g. `auth.login.invalid_credentials`) against a flat catalog.
- Two catalogs baked into the codebase: `fr` (default) and `en`.
- A REST endpoint `GET /api/v1/i18n/translations/{locale}` that returns the
  full catalog for client-side rendering (frontend uses react-i18next).
- A `LocaleMiddleware` that reads the `Accept-Language` header and stashes
  the negotiated locale on `request.state.locale` for downstream handlers.
- A helper `negotiate_locale(accept_language)` that maps the header value
  to one of the supported locales, falling back to `DEFAULT_LOCALE`.

The catalogs intentionally cover only the strings surfaced to end-users
(error messages, validation messages, common UI labels). Clinical content
(CIM-10 labels, DCI names) stays in French per OHADA convention.
"""
from app.modules.i18n.service import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    negotiate_locale,
    translate,
)
from app.modules.i18n.routes import router

__all__ = [
    "DEFAULT_LOCALE",
    "SUPPORTED_LOCALES",
    "negotiate_locale",
    "translate",
    "router",
]
