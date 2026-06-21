"""Tests for the i18n module — v1.3.0.

Covers:
- `translate()` resolution (FR/EN, missing key fallback, variable interpolation).
- `negotiate_locale()` Accept-Language parsing.
- REST endpoints `GET /api/v1/i18n/translations/{locale}` and `GET /api/v1/i18n/supported`.
- Error message translation helper.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestTranslate:
    def test_translate_fr_default(self):
        from app.modules.i18n import translate
        assert translate("auth.login.invalid_credentials") == "Identifiants invalides."

    def test_translate_en(self):
        from app.modules.i18n import translate
        assert translate("auth.login.invalid_credentials", locale="en") == "Invalid credentials."

    def test_translate_missing_key_falls_back_to_fr(self):
        from app.modules.i18n import translate
        # Key that exists in fr but not en
        # (all keys are mirrored, so we use a definitely-missing key)
        result = translate("nonexistent.key.123", locale="en")
        assert result == "nonexistent.key.123"  # returns the key itself

    def test_translate_with_variables(self):
        from app.modules.i18n import translate
        result = translate(
            "auth.login.account_locked",
            locale="fr",
            attempts=5,
            minutes=15,
        )
        assert "5" in result
        assert "15" in result
        assert "verrouillé" in result

    def test_translate_with_missing_variable_renders_empty(self):
        from app.modules.i18n import translate
        # Missing variable `attempts` → renders as empty string, no KeyError
        result = translate("auth.login.account_locked", locale="fr", minutes=10)
        assert "10" in result
        # Should not raise

    def test_translate_unsupported_locale_falls_back_to_fr(self):
        from app.modules.i18n import translate
        result = translate("auth.login.invalid_credentials", locale="de")
        assert result == "Identifiants invalides."


class TestNegotiateLocale:
    @pytest.mark.parametrize(
        "header,expected",
        [
            (None, "fr"),
            ("", "fr"),
            ("fr", "fr"),
            ("fr-FR", "fr"),
            ("fr-FR,fr;q=0.9,en;q=0.8", "fr"),
            ("en", "en"),
            ("en-US,en;q=0.9", "en"),
            ("en-US", "en"),
            ("de-DE,de;q=0.9,en;q=0.8", "en"),  # de not supported, fall to en
            ("de-DE,de;q=0.9,fr;q=0.8", "fr"),  # de not supported, fall to fr
            ("zh-CN", "fr"),  # nothing matches, fall to default
        ],
    )
    def test_negotiate(self, header, expected):
        from app.modules.i18n import negotiate_locale
        assert negotiate_locale(header) == expected

    def test_quality_sort(self):
        """en;q=0.9,fr;q=1.0 → fr should win because of higher quality."""
        from app.modules.i18n import negotiate_locale
        assert negotiate_locale("en;q=0.9,fr;q=1.0") == "fr"


class TestI18nRoutes:
    """REST endpoint tests for /api/v1/i18n/*."""

    def test_get_supported_locales(self, client: TestClient):
        # Public endpoint — no auth needed
        r = client.get("/api/v1/i18n/supported")
        assert r.status_code == 200
        data = r.json()
        assert data["default"] == "fr"
        assert "fr" in data["locales"]
        assert "en" in data["locales"]

    def test_get_translations_fr(self, client: TestClient):
        r = client.get("/api/v1/i18n/translations/fr")
        assert r.status_code == 200
        data = r.json()
        assert data["locale"] == "fr"
        assert data["count"] > 0
        assert "auth.login.invalid_credentials" in data["translations"]
        assert data["translations"]["auth.login.invalid_credentials"] == "Identifiants invalides."

    def test_get_translations_en(self, client: TestClient):
        r = client.get("/api/v1/i18n/translations/en")
        assert r.status_code == 200
        data = r.json()
        assert data["locale"] == "en"
        assert data["translations"]["auth.login.invalid_credentials"] == "Invalid credentials."

    def test_get_translations_unsupported_locale(self, client: TestClient):
        r = client.get("/api/v1/i18n/translations/de")
        assert r.status_code == 404
        assert "non supportée" in r.json()["detail"].lower() or "not found" in r.json()["detail"].lower()

    def test_translations_endpoint_does_not_require_auth(self, client: TestClient):
        """The /i18n/translations endpoint must be public — the frontend
        needs it before the user logs in (to display the login page in
        the browser's preferred language)."""
        r = client.get("/api/v1/i18n/translations/fr")
        assert r.status_code == 200
