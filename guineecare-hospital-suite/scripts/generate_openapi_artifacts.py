"""Generate static OpenAPI JSON + Postman collection for GuinéeCare API.

Outputs:
  - docs/api/openapi.json (machine-readable OpenAPI 3.1 spec)
  - docs/api/guineecare.postman_collection.json (importable Postman v2.1)
  - docs/api/guineecare-local.postman_environment.json (localhost env)

Usage:
  cd backend
  python ../scripts/generate_openapi_artifacts.py
"""
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure backend is importable
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# Boot config (no DB connection needed for openapi generation)
os.environ["DATABASE_URL"] = "sqlite:///./dev_guineecare.db"
os.environ["AUTH_SECRET"] = "dev-secret-key-2025"
os.environ["ENVIRONMENT"] = "test"

from app.main import app  # noqa: E402

OUT_DIR = ROOT / "docs" / "api"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✓ {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


def generate_openapi() -> dict:
    print("→ Generating OpenAPI 3.1 spec…")
    spec = app.openapi()
    openapi_path = OUT_DIR / "openapi.json"
    write_json(openapi_path, spec)
    return spec


def build_postman_item(method: str, path: str, op: dict, base_url: str) -> dict:
    """Convert an OpenAPI operation to a Postman v2.1 request item."""
    # Replace path params with :name for Postman variables
    pm_url = "{{base_url}}" + path.replace("/api/v1", "")
    # OpenAPI path uses {id}, Postman uses {{id}} — but we already replaced /api/v1.
    # Replace {param} → {{param}} for Postman variables.
    pm_url = pm_url.replace("{", "{{").replace("}", "}}")

    summary = op.get("summary", path)
    description = op.get("description") or op.get("summary", "")
    tags = op.get("tags", ["uncategorized"])
    folder = tags[0]

    # Build query params from parameters
    query_params = []
    for p in op.get("parameters", []):
        if p.get("in") == "query":
            query_params.append(
                {
                    "key": p["name"],
                    "value": p.get("schema", {}).get("example", "")
                            or p.get("schema", {}).get("default", ""),
                    "description": p.get("description", ""),
                    "disabled": "required" not in p or not p["required"]
                    and p.get("name") not in ("page", "page_size"),
                }
            )
        elif p.get("in") == "path":
            # Already encoded in URL via {{param}}
            pass

    # Build request body if present
    body_raw = ""
    if "requestBody" in op:
        content = op["requestBody"].get("content", {})
        app_json = content.get("application/json", {})
        example = app_json.get("example")
        if example is None:
            # Try to extract from schema $ref
            schema = app_json.get("schema", {})
            if "example" in schema:
                example = schema["example"]
        if example:
            body_raw = json.dumps(example, ensure_ascii=False, indent=2)

    item: dict = {
        "name": summary,
        "request": {
            "method": method.upper(),
            "header": [
                {"key": "Content-Type", "value": "application/json", "type": "text"},
                {
                    "key": "Authorization",
                    "value": "Bearer {{access_token}}",
                    "type": "text",
                    "description": "JWT Bearer token (récupéré via POST /auth/login)",
                },
            ],
            "url": {
                "raw": pm_url,
                "host": ["{{host}}"],
                "path": [p for p in pm_url.replace("{{host}}", "").lstrip("/").split("/") if p],
                "query": query_params,
            },
            "description": description,
        },
        "response": [],
    }

    if body_raw:
        item["request"]["body"] = {
            "mode": "raw",
            "raw": body_raw,
            "options": {"raw": {"language": "json"}},
        }

    # Tag the item with its folder so we can group afterwards
    item["_folder"] = folder
    return item


def generate_postman_collection(spec: dict) -> dict:
    print("→ Generating Postman v2.1 collection…")
    items_by_folder: dict[str, list[dict]] = {}
    order = [
        "system",
        "auth",
        "users",
        "rbac",
        "facilities",
        "departments",
        "patients",
        "admissions",
        "emergency",
        "hospitalization",
        "clinical",
        "maternity",
        "pharmacy",
        "laboratory",
        "imaging",
        "surgery",
        "billing",
        "personnel",
        "quality",
        "reporting",
        "audit",
        "activity",
        "notifications",
        "health",
        "metrics",
    ]

    for path, ops in spec.get("paths", {}).items():
        for method, op in ops.items():
            if method not in ("get", "post", "put", "patch", "delete"):
                continue
            item = build_postman_item(method, path, op, base_url="{{base_url}}")
            items_by_folder.setdefault(item.pop("_folder"), []).append(item)

    folders = []
    for folder_name in order:
        if folder_name in items_by_folder:
            folders.append({"name": f"{folder_name.title()} API", "item": items_by_folder[folder_name]})
    # Add any stragglers
    for folder_name, items in items_by_folder.items():
        if folder_name not in order:
            folders.append({"name": f"{folder_name.title()} API", "item": items})

    collection = {
        "info": {
            "name": "GuinéeCare Hospital Suite API",
            "_postman_id": "guineecare-v0-10-0",
            "description": (
                "Collection Postman pour l'API GuinéeCare.\n\n"
                "## Démarrage rapide\n"
                "1. Importez l'environement `guineecare-local.postman_environment.json`.\n"
                "2. Définissez `host` = `localhost:8000` et `base_url` = `http://localhost:8000/api/v1`.\n"
                "3. Appelez `Auth > Login` avec un compte de test (voir README).\n"
                "4. Le script de response injecte automatiquement `access_token` et `refresh_token`.\n"
                "5. Les autres requêtes utilisent `Bearer {{access_token}}`.\n"
            ),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "event": [
            {
                "listen": "prerequest",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// Auto-refresh token si bientôt expiré (optionnel)",
                        "// const exp = pm.environment.get('access_token_exp');",
                        "// if (exp && Date.now() > exp - 60000) { ... }",
                    ],
                },
            },
            {
                "listen": "test",
                "script": {
                    "type": "text/javascript",
                    "exec": [
                        "// Capture automatique des tokens après login/refresh",
                        "if (pm.request.url.path.includes('auth/login') || pm.request.url.path.includes('auth/refresh')) {",
                        "    const json = pm.response.json();",
                        "    if (json.access_token) {",
                        "        pm.environment.set('access_token', json.access_token);",
                        "        // 60 minutes - 1 minute de marge",
                        "        pm.environment.set('access_token_exp', Date.now() + 59 * 60 * 1000);",
                        "    }",
                        "    if (json.refresh_token) {",
                        "        pm.environment.set('refresh_token', json.refresh_token);",
                        "    }",
                        "}",
                        "// Vérification standard",
                        "pm.test('Status 2xx', () => pm.expect(pm.response.code).to.be.within(200, 299));",
                    ],
                },
            },
        ],
        "variable": [
            {"key": "host", "value": "localhost:8000"},
            {"key": "base_url", "value": "http://localhost:8000/api/v1"},
            {"key": "access_token", "value": ""},
            {"key": "refresh_token", "value": ""},
            {"key": "access_token_exp", "value": "0"},
        ],
        "item": folders,
    }

    path = OUT_DIR / "guineecare.postman_collection.json"
    write_json(path, collection)


def generate_postman_environment() -> None:
    print("→ Generating Postman environment (local dev)…")
    env = {
        "name": "GuinéeCare - Local",
        "values": [
            {"key": "host", "value": "localhost:8000", "enabled": True},
            {"key": "base_url", "value": "http://localhost:8000/api/v1", "enabled": True},
            {"key": "access_token", "value": "", "enabled": True},
            {"key": "refresh_token", "value": "", "enabled": True},
            {"key": "access_token_exp", "value": "0", "enabled": True},
            {"key": "admin_email", "value": "admin@guineecare.com", "enabled": True},
            {"key": "admin_password", "value": "admin123", "enabled": True},
            {"key": "doctor_email", "value": "dr.diallo@chu-donka.gn", "enabled": True},
            {"key": "doctor_password", "value": "doctor123", "enabled": True},
        ],
        "_postman_variable_scope": "environment",
        "_postman_exported_using": "GuinéeCare v0.10.0",
    }
    write_json(OUT_DIR / "guineecare-local.postman_environment.json", env)


def main() -> None:
    print(f"\n=== Generating OpenAPI artifacts for {app.title} v{app.version} ===\n")
    spec = generate_openapi()
    generate_postman_collection(spec)
    generate_postman_environment()
    print("\n✅ All artifacts generated in docs/api/")


if __name__ == "__main__":
    main()
