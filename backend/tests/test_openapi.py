"""Tests for the enriched OpenAPI specification (v0.10.0).

Validates that:
- All endpoints have a tag.
- All endpoints have a summary.
- All protected endpoints declare a 401 response.
- All endpoints with a request body declare a 422 response.
- All protected endpoints reference HTTPBearer security.
- Tags are declared in the spec metadata.
- The /api/v1 root is tagged "system".
- The generated openapi.json (committed in docs/api/) is in sync with the
  runtime OpenAPI spec (drift detection).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.main import APP_VERSION, app


@pytest.fixture(scope="module")
def spec() -> dict:
    return app.openapi()


@pytest.fixture(scope="module")
def operations(spec):
    """Yield (method, path, operation_dict) for every HTTP method on every path."""
    out = []
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            if method in ("get", "post", "put", "patch", "delete"):
                out.append((method, path, op))
    return out


# --- Top-level metadata -------------------------------------------------------

def test_openapi_version_is_3_1(spec):
    assert spec["openapi"].startswith("3.1"), "OpenAPI 3.1.x expected"


def test_app_version_matches_current_release(spec):
    assert spec["info"]["version"] == APP_VERSION
    assert APP_VERSION == "1.3.0"


def test_app_has_description(spec):
    desc = spec["info"].get("description", "")
    assert desc and len(desc) > 500, "Description should be substantial (>500 chars)"
    assert "JWT" in desc
    assert "Bearer" in desc
    assert "RBAC" in desc


def test_app_has_contact_and_license(spec):
    assert spec["info"].get("contact", {}).get("name") == "GuinéeCare Tech Team"
    assert "license" in spec["info"]


def test_app_has_servers(spec):
    servers = spec.get("servers", [])
    assert len(servers) == 3
    urls = [s["url"] for s in servers]
    assert "/api/v1" in urls
    assert "http://localhost:8000/api/v1" in urls
    assert "https://api.guineecare.gn/api/v1" in urls


def test_app_has_security_scheme(spec):
    schemes = spec.get("components", {}).get("securitySchemes", {})
    assert "HTTPBearer" in schemes
    assert schemes["HTTPBearer"]["type"] == "http"
    assert schemes["HTTPBearer"]["scheme"] == "bearer"


def test_app_has_all_27_tags(spec):
    tags = {t["name"] for t in spec.get("tags", [])}
    expected = {
        "auth", "users", "rbac", "facilities", "departments",
        "patients", "admissions", "emergency", "hospitalization", "clinical",
        "maternity", "pharmacy", "laboratory", "imaging", "surgery",
        "billing", "personnel", "quality", "reporting", "audit",
        "activity", "notifications", "user-profile", "feedback",
        "documents", "search",
        "health", "metrics", "system",
    }
    missing = expected - tags
    assert not missing, f"Missing tags: {missing}"
    for t in spec["tags"]:
        assert t.get("description"), f"Tag {t['name']} has no description"


# --- Per-operation checks ----------------------------------------------------

PUBLIC_PATHS = frozenset({
    "/api/v1",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/health",
    "/health/live",
    "/health/ready",
    "/metrics",
})


def test_every_operation_has_tag(operations):
    no_tag = [(m, p) for m, p, op in operations if not op.get("tags")]
    assert not no_tag, f"Operations without tag: {no_tag}"


def test_every_operation_has_summary(operations):
    no_summary = [(m, p) for m, p, op in operations if not op.get("summary")]
    assert not no_summary, f"Operations without summary: {no_summary}"


def test_protected_operations_have_401_response(operations):
    missing = []
    for method, path, op in operations:
        if path in PUBLIC_PATHS:
            continue
        if "401" not in op.get("responses", {}):
            missing.append(f"{method.upper()} {path}")
    assert not missing, f"Protected operations missing 401 response: {missing}"


def test_protected_operations_have_403_response(operations):
    missing = []
    for method, path, op in operations:
        if path in PUBLIC_PATHS:
            continue
        if "403" not in op.get("responses", {}):
            missing.append(f"{method.upper()} {path}")
    assert not missing, f"Protected operations missing 403 response: {missing}"


def test_protected_operations_have_429_response(operations):
    missing = []
    for method, path, op in operations:
        if path in PUBLIC_PATHS:
            continue
        if "429" not in op.get("responses", {}):
            missing.append(f"{method.upper()} {path}")
    assert not missing, f"Protected operations missing 429 response: {missing}"


def test_protected_operations_have_500_response(operations):
    missing = []
    for method, path, op in operations:
        if path in PUBLIC_PATHS:
            continue
        if "500" not in op.get("responses", {}):
            missing.append(f"{method.upper()} {path}")
    assert not missing, f"Protected operations missing 500 response: {missing}"


def test_protected_operations_have_bearer_security(operations):
    missing = []
    for method, path, op in operations:
        if path in PUBLIC_PATHS:
            continue
        security = op.get("security") or []
        has_bearer = any("HTTPBearer" in s for s in security)
        if not has_bearer:
            missing.append(f"{method.upper()} {path}")
    assert not missing, f"Protected operations missing HTTPBearer security: {missing}"


def test_body_operations_have_422_response(operations):
    missing = []
    for method, path, op in operations:
        if "requestBody" in op and "422" not in op.get("responses", {}):
            missing.append(f"{method.upper()} {path}")
    assert not missing, f"Body operations missing 422 response: {missing}"


def test_api_root_is_tagged_system(spec):
    op = spec["paths"]["/api/v1"]["get"]
    assert "system" in op.get("tags", [])


def test_public_operations_have_no_security(operations):
    """Public endpoints should NOT declare Bearer security."""
    bad = []
    for method, path, op in operations:
        if path in PUBLIC_PATHS:
            security = op.get("security") or []
            if security:
                bad.append(f"{method.upper()} {path} → {security}")
    assert not bad, f"Public operations should not declare security: {bad}"


# --- Committed openapi.json drift detection ----------------------------------

def test_committed_openapi_json_in_sync(spec):
    """The committed docs/api/openapi.json must match the runtime spec."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    committed_path = repo_root / "docs" / "api" / "openapi.json"
    if not committed_path.exists():
        pytest.skip("docs/api/openapi.json not generated yet (run scripts/generate_openapi_artifacts.py)")

    committed = json.loads(committed_path.read_text(encoding="utf-8"))

    # Compare structural fields, not exact key order (dict equality ignores order).
    assert committed["info"]["version"] == spec["info"]["version"], (
        f"Version mismatch: runtime={spec['info']['version']}, "
        f"committed={committed['info']['version']}. "
        f"Run: python scripts/generate_openapi_artifacts.py"
    )
    assert committed["paths"].keys() == spec["paths"].keys(), (
        f"Path drift detected.\n"
        f"  Only in runtime:   {set(spec['paths'].keys()) - set(committed['paths'].keys())}\n"
        f"  Only in committed: {set(committed['paths'].keys()) - set(spec['paths'].keys())}\n"
        f"Run: python scripts/generate_openapi_artifacts.py"
    )

    # Verify each operation's responses are in sync
    drift = []
    for path, ops in spec["paths"].items():
        for method, op in ops.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            committed_op = committed["paths"][path][method]
            runtime_codes = set(op.get("responses", {}).keys())
            committed_codes = set(committed_op.get("responses", {}).keys())
            if runtime_codes != committed_codes:
                drift.append(
                    f"{method.upper()} {path}: runtime={runtime_codes} committed={committed_codes}"
                )
    assert not drift, (
        "Response code drift detected:\n  " + "\n  ".join(drift) +
        "\nRun: python scripts/generate_openapi_artifacts.py"
    )


def test_committed_postman_collection_exists():
    repo_root = Path(__file__).resolve().parent.parent.parent
    postman_path = repo_root / "docs" / "api" / "guineecare.postman_collection.json"
    assert postman_path.exists(), "Postman collection missing — run scripts/generate_openapi_artifacts.py"
    data = json.loads(postman_path.read_text(encoding="utf-8"))
    assert data["info"]["schema"].endswith("v2.1.0/collection.json")
    # Sanity check: at least 20 folders (we have 25)
    assert len(data["item"]) >= 20, f"Expected >=20 folders, got {len(data['item'])}"
