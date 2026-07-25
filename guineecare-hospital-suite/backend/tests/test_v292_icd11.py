"""Tests — v2.9.2 : ICD-11 module

Couverture :
- search_icd11 : recherche par code, label FR, label EN, insensible à la casse
- get_icd11_by_code : récupération directe par code
- list_icd11_categories : liste des catégories
- Routes API : /icd11/search, /icd11/{code}, /icd11/categories
- RBAC : JWT requis (401 sans token)
"""
import pytest

from app.modules.icd11.catalog import (
    ICD11_CATALOG,
    get_icd11_by_code,
    list_icd11_categories,
    search_icd11,
)


# ---------------------------------------------------------------------------
# 1. Catalogue — fonctions pures
# ---------------------------------------------------------------------------
class TestICD11Catalog:
    def test_catalog_not_empty(self):
        """Le catalogue contient au moins 50 codes."""
        assert len(ICD11_CATALOG) >= 50

    def test_search_by_code_exact(self):
        """Recherche exacte par code → score 100, en tête."""
        results = search_icd11("1F03")  # Paludisme à P. falciparum
        assert len(results) >= 1
        assert results[0]["code"] == "1F03"
        assert "falciparum" in results[0]["label_fr"].lower()

    def test_search_by_code_prefix(self):
        """Recherche par préfixe de code → tous les codes commençant par le préfixe."""
        results = search_icd11("1F")
        assert len(results) >= 2  # Au moins 1F03 et 1F2Z (paludismes)
        codes = [r["code"] for r in results]
        assert "1F03" in codes
        assert "1F2Z" in codes

    def test_search_by_label_fr(self):
        """Recherche par label FR → match."""
        results = search_icd11("paludisme")
        assert len(results) >= 1
        assert any("paludisme" in r["label_fr"].lower() for r in results)

    def test_search_by_label_en(self):
        """Recherche par label EN → match."""
        results = search_icd11("malaria")
        assert len(results) >= 1
        assert any("malaria" in r["label_en"].lower() for r in results)

    def test_search_case_insensitive(self):
        """Recherche insensible à la casse."""
        results_lower = search_icd11("paludisme")
        results_upper = search_icd11("PALUDISME")
        results_mixed = search_icd11("Paludisme")
        assert len(results_lower) == len(results_upper) == len(results_mixed)

    def test_search_empty_query_returns_empty(self):
        """Requête vide → liste vide."""
        assert search_icd11("") == []
        assert search_icd11("   ") == []

    def test_search_unknown_returns_empty(self):
        """Recherche d'un terme inexistant → liste vide."""
        results = search_icd11("zzz_inexistant_zzz")
        assert results == []

    def test_search_respects_limit(self):
        """La limite est respectée."""
        results = search_icd11("a", limit=5)
        assert len(results) <= 5

    def test_get_by_code_existing(self):
        """get_icd11_by_code retourne le code s'il existe."""
        result = get_icd11_by_code("1F03")
        assert result is not None
        assert result["code"] == "1F03"
        assert "label_fr" in result
        assert "label_en" in result
        assert "category" in result

    def test_get_by_code_non_existing(self):
        """get_icd11_by_code retourne None si code inexistant."""
        assert get_icd11_by_code("ZZZ99") is None

    def test_get_by_code_case_insensitive(self):
        """get_icd11_by_code insensible à la casse."""
        upper = get_icd11_by_code("1F03")
        lower = get_icd11_by_code("1f03")
        assert upper is not None
        assert lower is not None
        assert upper["code"] == lower["code"]

    def test_list_categories_not_empty(self):
        """list_icd11_categories retourne une liste non vide."""
        cats = list_icd11_categories()
        assert len(cats) >= 5
        assert "Infectious" in cats or "Paludisme" in " ".join(cats)

    def test_known_guinean_codes_present(self):
        """Codes critiques pour la pratique guinéenne présents."""
        codes = [c for c, _, _, _ in ICD11_CATALOG]
        # Paludisme (endémique en Guinée)
        assert "1F03" in codes
        assert "1F2Z" in codes
        # Hypertension
        assert "BA00" in codes
        # Diabète
        assert "5A1A" in codes
        # Prééclampsie (maternité)
        assert "JB02" in codes
        # Hémorragie post-partum
        assert "JC24" in codes


# ---------------------------------------------------------------------------
# 2. Routes API
# ---------------------------------------------------------------------------
class TestICD11Routes:
    def test_search_endpoint(self, client, admin_headers):
        """GET /icd11/search?q=... retourne 200 + résultats."""
        resp = client.get("/api/v1/icd11/search?q=paludisme", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data
        assert data["query"] == "paludisme"
        assert data["total"] >= 1
        assert any("paludisme" in r["label_fr"].lower() for r in data["data"])

    def test_search_endpoint_requires_auth(self, client):
        """GET /icd11/search sans auth → 401."""
        resp = client.get("/api/v1/icd11/search?q=test")
        assert resp.status_code == 401

    def test_search_endpoint_short_query_422(self, client, admin_headers):
        """GET /icd11/search?q= (vide) → 422 (min_length=1)."""
        resp = client.get("/api/v1/icd11/search?q=", headers=admin_headers)
        assert resp.status_code == 422

    def test_get_by_code_endpoint(self, client, admin_headers):
        """GET /icd11/{code} retourne le détail du code."""
        resp = client.get("/api/v1/icd11/1F03", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["code"] == "1F03"
        assert "falciparum" in data["data"]["label_fr"].lower()

    def test_get_by_code_not_found(self, client, admin_headers):
        """GET /icd11/ZZZ99 → 404."""
        resp = client.get("/api/v1/icd11/ZZZ99", headers=admin_headers)
        assert resp.status_code == 404

    def test_categories_endpoint(self, client, admin_headers):
        """GET /icd11/categories retourne la liste des catégories."""
        resp = client.get("/api/v1/icd11/categories", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert len(data["data"]) >= 5

    def test_search_limit_param(self, client, admin_headers):
        """GET /icd11/search?q=...&limit=3 → max 3 résultats."""
        resp = client.get("/api/v1/icd11/search?q=a&limit=3", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) <= 3

    def test_search_doctor_can_access(self, client, db):
        """DOCTOR peut accéder à /icd11/search (catalogue de référence)."""
        from app.core.security import hash_password, create_access_token
        from app.modules.users.models import User

        doctor = User(
            email="doc-icd@test.com",
            password_hash=hash_password("TestPassword1!xx"),
            first_name="Doc",
            last_name="ICD",
            role="DOCTOR",
            is_active=True,
        )
        db.add(doctor)
        db.commit()
        db.refresh(doctor)
        token = create_access_token(
            subject=doctor.id, facility_id=doctor.facility_id, role=doctor.role,
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.get("/api/v1/icd11/search?q=paludisme", headers=headers)
        assert resp.status_code == 200
