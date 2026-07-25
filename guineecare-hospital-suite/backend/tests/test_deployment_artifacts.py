"""Tests for the v1.0.0 production deployment artifacts.

Validates that:
- docker-compose.yml is valid YAML with all expected services.
- docker-compose.prod.yml overrides correctly (security hardening).
- nginx.prod.conf has the required security directives.
- .env.production.template contains all required variables.
- .env.example is consistent with the production template.
- .gitignore excludes .env.production, *.pem, tls/.
- Scripts are executable.
- Runbook exists and has the required sections.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# --- Docker compose ---------------------------------------------------------

def test_docker_compose_yml_valid():
    data = yaml.safe_load(_read(REPO_ROOT / "docker-compose.yml"))
    assert "services" in data
    services = data["services"]
    for expected in ("nginx", "backend", "frontend", "postgres", "redis", "db-backup"):
        assert expected in services, f"Missing service: {expected}"


def test_docker_compose_prod_yml_valid():
    data = yaml.safe_load(_read(REPO_ROOT / "docker-compose.prod.yml"))
    assert "services" in data
    backend = data["services"]["backend"]
    # Production hardening requirements
    assert backend.get("user") == "1001:1001", "backend must run as non-root user"
    assert backend.get("read_only") is True, "backend fs must be read-only"
    assert "no-new-privileges:true" in backend.get("security_opt", []), \
        "backend must have no-new-privileges"
    assert "ALL" in backend.get("cap_drop", []), "backend must drop ALL capabilities"
    env_list = backend["environment"]
    # docker-compose environment can be a list ["KEY=val", ...] or a dict
    if isinstance(env_list, list):
        env = {}
        for item in env_list:
            if "=" in item:
                k, v = item.split("=", 1)
                env[k] = v
    else:
        env = env_list
    assert env.get("ENVIRONMENT") == "production"
    assert env.get("SEED_DEMO_DATA") == "false"
    assert "AUTH_SECRET" in env["AUTH_SECRET"], "AUTH_SECRET must come from env"
    assert "DB_PASSWORD" in env["DATABASE_URL"], "DB password must come from env"


def test_docker_compose_prod_resources_enforced():
    data = yaml.safe_load(_read(REPO_ROOT / "docker-compose.prod.yml"))
    for svc_name in ("backend", "frontend", "postgres", "nginx", "redis"):
        svc = data["services"][svc_name]
        limits = svc.get("deploy", {}).get("resources", {}).get("limits", {})
        assert "memory" in limits, f"{svc_name} missing memory limit"
        assert "cpus" in limits, f"{svc_name} missing CPU limit"
        assert svc.get("restart") == "always", f"{svc_name} must restart=always"


def test_docker_compose_prod_nginx_uses_tls_volume():
    data = yaml.safe_load(_read(REPO_ROOT / "docker-compose.prod.yml"))
    nginx = data["services"]["nginx"]
    volumes = nginx.get("volumes", [])
    assert any("tls" in v for v in volumes), "nginx must mount tls/ volume"
    assert any("nginx.prod.conf" in v for v in volumes), \
        "nginx must use nginx.prod.conf (not the dev config)"


# --- nginx.prod.conf --------------------------------------------------------

def test_nginx_prod_conf_has_tls():
    conf = _read(REPO_ROOT / "nginx.prod.conf")
    assert "ssl_certificate" in conf
    assert "ssl_certificate_key" in conf
    assert "TLSv1.2" in conf and "TLSv1.3" in conf
    # TLS 1.0/1.1 forbidden
    assert "TLSv1 " not in conf
    assert "TLSv1.1" not in conf


def test_nginx_prod_conf_has_security_headers():
    conf = _read(REPO_ROOT / "nginx.prod.conf")
    for header in (
        "Strict-Transport-Security",
        "X-Content-Type-Options",
        "X-Frame-Options",
        "Content-Security-Policy",
        "Referrer-Policy",
    ):
        assert header in conf, f"Missing security header: {header}"


def test_nginx_prod_conf_http_redirects_to_https():
    conf = _read(REPO_ROOT / "nginx.prod.conf")
    assert "return 301 https://" in conf, "HTTP must redirect to HTTPS"


def test_nginx_prod_conf_metrics_ip_restricted():
    conf = _read(REPO_ROOT / "nginx.prod.conf")
    # /metrics should be IP-allowlisted
    metrics_section = conf.split("location /metrics")[1].split("}")[0] if "/metrics" in conf else ""
    assert "allow" in metrics_section, "/metrics must be IP-allowlisted"
    assert "deny all" in metrics_section, "/metrics must deny all by default"


def test_nginx_prod_conf_auth_rate_limited():
    conf = _read(REPO_ROOT / "nginx.prod.conf")
    # /api/v1/auth/login must have a stricter rate limit than general API
    assert "auth_limit" in conf, "auth_limit zone must be defined"
    assert "login_burst" in conf, "login_burst zone must be defined"
    assert "limit_req zone=auth_limit" in conf


def test_nginx_prod_conf_client_max_body_size():
    conf = _read(REPO_ROOT / "nginx.prod.conf")
    assert "client_max_body_size" in conf, "Must cap upload size"


# --- .env templates ---------------------------------------------------------

REQUIRED_ENV_VARS = {
    "ENVIRONMENT",
    "AUTH_SECRET",
    "DB_PASSWORD",
    "DATABASE_URL",
    "CORS_ORIGINS",
    "TOKEN_EXPIRE_MINUTES",
    "TRUSTED_PROXIES",
    "METRICS_TOKEN",
    "BOOTSTRAP_TOKEN",
    "SEED_DEMO_DATA",
}


def test_env_production_template_has_all_required_vars():
    content = _read(REPO_ROOT / ".env.production.template")
    for var in REQUIRED_ENV_VARS:
        assert f"{var}=" in content, f"Missing env var in template: {var}"


def test_env_production_template_has_placeholders():
    content = _read(REPO_ROOT / ".env.production.template")
    # All secrets must start with CHANGE_ME_
    for var in ("AUTH_SECRET", "DB_PASSWORD", "METRICS_TOKEN", "BOOTSTRAP_TOKEN", "REDIS_PASSWORD"):
        assert f"{var}=CHANGE_ME_" in content, \
            f"{var} must have CHANGE_ME_ placeholder in template"


def test_env_production_template_forbids_seed_demo_data():
    content = _read(REPO_ROOT / ".env.production.template")
    assert "SEED_DEMO_DATA=false" in content


def test_env_example_has_all_required_vars():
    content = _read(REPO_ROOT / ".env.example")
    for var in REQUIRED_ENV_VARS:
        assert f"{var}=" in content, f"Missing env var in .env.example: {var}"


# --- .gitignore -------------------------------------------------------------

def test_gitignore_excludes_secrets():
    content = _read(REPO_ROOT / ".gitignore")
    assert ".env.production" in content
    assert ".env.local" in content
    assert "*.pem" in content
    assert "*.key" in content
    assert "tls/" in content
    assert "*.dump" in content


# --- Scripts ----------------------------------------------------------------

REQUIRED_SCRIPTS = ("deploy.sh", "backup.sh", "restore.sh", "seed-pilot.sh")


def test_scripts_exist_and_are_executable():
    for name in REQUIRED_SCRIPTS:
        path = REPO_ROOT / "scripts" / name
        assert path.exists(), f"Missing script: {name}"
        mode = path.stat().st_mode
        assert mode & stat.S_IXUSR, f"{name} must be executable by owner"
        assert mode & stat.S_IXGRP, f"{name} must be executable by group"


def test_deploy_script_has_check_only_mode():
    content = _read(REPO_ROOT / "scripts" / "deploy.sh")
    assert "--check-only" in content
    assert "MISSING" in content or "missing" in content
    # Must validate CHANGE_ME placeholders
    assert "CHANGE_ME" in content


def test_deploy_script_validates_required_env_vars():
    content = _read(REPO_ROOT / "scripts" / "deploy.sh")
    assert "REQUIRED_VARS" in content
    for var in ("ENVIRONMENT", "AUTH_SECRET", "DB_PASSWORD"):
        assert var in content, f"deploy.sh must validate {var}"


def test_backup_script_has_verify_mode():
    content = _read(REPO_ROOT / "scripts" / "backup.sh")
    assert "--verify" in content
    assert "--list" in content
    assert "pg_dump" in content


def test_restore_script_has_confirm_prompt():
    content = _read(REPO_ROOT / "scripts" / "restore.sh")
    assert "CONFIRM" in content, "restore.sh must require manual confirmation"
    assert "DROP DATABASE" in content or "pg_restore" in content


# --- Runbook ----------------------------------------------------------------

def test_runbook_exists():
    path = REPO_ROOT / "docs" / "deploiement" / "RUNBOOK_CHU_DONKA.md"
    assert path.exists(), "Runbook must exist"


def test_runbook_has_required_sections():
    content = _read(REPO_ROOT / "docs" / "deploiement" / "RUNBOOK_CHU_DONKA.md")
    for section in (
        "Architecture cible",
        "Préparation du serveur",
        "Configuration des secrets",
        "Déploiement initial",
        "Opérations courantes",
        "Monitoring",
        "Procédures d'incident",
        "Maintenance planifiée",
        "Contacts",
        "Checklist go-live",
        "Rollback",
    ):
        assert section in content, f"Runbook missing section: {section}"


def test_runbook_has_go_live_checklist():
    content = _read(REPO_ROOT / "docs" / "deploiement" / "RUNBOOK_CHU_DONKA.md")
    assert "- [ ]" in content, "Runbook must contain a go-live checklist"
    # Must reference key items
    assert "DNS" in content or "dns" in content.lower()
    assert "TLS" in content or "tls" in content.lower()
    assert "backup" in content.lower()


# --- CI workflow ------------------------------------------------------------

def test_deploy_release_workflow_exists():
    path = REPO_ROOT / ".github" / "workflows" / "deploy-release.yml"
    assert path.exists()


def test_deploy_release_workflow_pushes_to_ghcr():
    content = _read(REPO_ROOT / ".github" / "workflows" / "deploy-release.yml")
    assert "ghcr.io" in content
    assert "docker/build-push-action" in content
    # Must trigger on v* tags
    assert '"v*"' in content
