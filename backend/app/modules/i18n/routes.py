"""i18n REST endpoints — v1.3.0.

- `GET /api/v1/i18n/translations/{locale}` — return the full catalog for
  client-side rendering (frontend uses react-i18next with `fr.json` /
  `en.json` catalogs fetched at app boot).
- `GET /api/v1/i18n/supported` — list supported locales + the default.
"""
from fastapi import APIRouter, HTTPException, Path

from app.modules.i18n.service import (
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    get_catalog,
)

router = APIRouter(prefix="/i18n", tags=["i18n"])


@router.get(
    "/translations/{locale}",
    summary="Catalogue de traductions pour une langue",
    description=(
        "Retourne l'ensemble des clés de traduction pour la langue demandée. "
        "Utilisé par le frontend au démarrage pour hydrater react-i18next "
        "avec `i18next.init({ resources: { [locale]: { translation: catalog } } })`."
    ),
)
def get_translations(
    locale: str = Path(..., description="Code langue ISO 639-1 (fr, en).", min_length=2, max_length=2),
):
    if locale not in SUPPORTED_LOCALES:
        raise HTTPException(
            status_code=404,
            detail=f"Langue non supportée: {locale}. Langues supportées: {', '.join(SUPPORTED_LOCALES)}",
        )
    return {
        "locale": locale,
        "translations": get_catalog(locale),
        "count": len(get_catalog(locale)),
    }


@router.get(
    "/supported",
    summary="Langues supportées",
    description="Liste des langues supportées par l'API + langue par défaut.",
)
def list_supported_locales():
    return {
        "locales": list(SUPPORTED_LOCALES),
        "default": DEFAULT_LOCALE,
    }
