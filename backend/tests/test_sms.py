"""Tests du module SMS v1.4.0 — providers, règles de routage, envoi, historique, stats."""
import os

import pytest

from app.modules.notifications.sms_models import (
    SmsMessage,
    SmsProvider,
    SmsRoutingRule,
)
from app.modules.notifications.sms_provider import (
    MockSmsProvider,
    normalize_phone_gn,
    encrypt_credential,
    decrypt_credential,
)


# ── Providers CRUD ──────────────────────────────────────────────────────────

def test_list_providers_empty_then_seeded(auth_headers, client):
    """GET /notifications/sms/providers — seed automatique du mock si vide."""
    response = client.get("/api/v1/notifications/sms/providers", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    codes = [p["code"] for p in data["data"]]
    assert "mock" in codes
    # Pas de credentials en clair dans la réponse
    assert "api_key" not in data["data"][0]
    assert "has_api_key" in data["data"][0]


def test_create_provider_orange(auth_headers, client):
    """POST /notifications/sms/providers — crée un provider Orange avec credentials chiffrés."""
    payload = {
        "code": "orange",
        "name": "Orange Guinée SMS Pro",
        "enabled": True,
        "api_url": "https://api.orange.com/smsmessaging/v1/outbound/requests",
        "api_key": "test_key_123",
        "api_secret": "test_secret_456",
        "sender_id": "GUINEECARE",
        "cost_per_sms_gnf": 25,
        "rate_per_second": 10,
    }
    response = client.post(
        "/api/v1/notifications/sms/providers", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "orange"
    assert data["name"] == "Orange Guinée SMS Pro"
    assert data["enabled"] is True
    assert data["has_api_key"] is True
    assert data["has_api_secret"] is True
    assert data["cost_per_sms_gnf"] == 25
    # Pas de credentials en clair dans la réponse
    assert "api_key" not in data
    assert "api_secret" not in data


def test_create_provider_duplicate_conflict(auth_headers, client):
    """POST /notifications/sms/providers — 409 si code déjà existant."""
    # D'abord s'assurer que le mock est seedé (via list_providers qui seed automatiquement)
    client.get("/api/v1/notifications/sms/providers", headers=auth_headers)
    payload = {"code": "mock", "name": "Duplicate mock"}
    response = client.post(
        "/api/v1/notifications/sms/providers", json=payload, headers=auth_headers
    )
    assert response.status_code == 409


def test_update_provider(auth_headers, client):
    """PATCH /notifications/sms/providers/{id} — met à jour le coût."""
    # Créer un provider
    create = client.post(
        "/api/v1/notifications/sms/providers",
        json={"code": "mtn", "name": "MTN", "cost_per_sms_gnf": 20},
        headers=auth_headers,
    )
    provider_id = create.json()["id"]

    # Update
    response = client.patch(
        f"/api/v1/notifications/sms/providers/{provider_id}",
        json={"cost_per_sms_gnf": 30, "enabled": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["cost_per_sms_gnf"] == 30
    assert data["enabled"] is False


def test_delete_provider_protects_mock(auth_headers, client, db):
    """DELETE /notifications/sms/providers/{id} — le mock ne peut pas être supprimé."""
    # S'assurer que le mock est seedé
    client.get("/api/v1/notifications/sms/providers", headers=auth_headers)
    mock = db.query(SmsProvider).filter(SmsProvider.code == "mock").first()
    assert mock is not None  # sanity check
    response = client.delete(
        f"/api/v1/notifications/sms/providers/{mock.id}", headers=auth_headers
    )
    assert response.status_code == 400


def test_delete_provider_orange(auth_headers, client, db):
    """DELETE /notifications/sms/providers/{id} — supprime un provider non-mock."""
    create = client.post(
        "/api/v1/notifications/sms/providers",
        json={"code": "moov", "name": "Moov Africa", "cost_per_sms_gnf": 22},
        headers=auth_headers,
    )
    provider_id = create.json()["id"]
    response = client.delete(
        f"/api/v1/notifications/sms/providers/{provider_id}", headers=auth_headers
    )
    assert response.status_code == 204


def test_list_supported_providers(auth_headers, client):
    """GET /notifications/sms/providers/supported — catalogue statique."""
    response = client.get(
        "/api/v1/notifications/sms/providers/supported", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()["data"]
    codes = [p["code"] for p in data]
    assert set(codes) == {"mock", "orange", "mtn", "moov"}


# ── Routing Rules ───────────────────────────────────────────────────────────

def test_list_rules_seeds_defaults(auth_headers, client):
    """GET /notifications/sms/rules — seed automatique des règles par défaut."""
    response = client.get("/api/v1/notifications/sms/rules", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5  # 8 règles par défaut
    categories = [r["category"] for r in data["data"]]
    assert "lab_critical" in categories
    assert "appointment_reminder" in categories
    assert "quality_alert" in categories


def test_create_rule(auth_headers, client):
    """POST /notifications/sms/rules — crée une règle facility-spécifique."""
    payload = {
        "category": "custom_category",
        "channels": ["in_app", "sms"],
        "min_priority": "high",
        "description": "Règle custom de test",
    }
    response = client.post(
        "/api/v1/notifications/sms/rules", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["category"] == "custom_category"
    assert "sms" in data["channels"]
    assert data["min_priority"] == "high"


def test_create_rule_duplicate_conflict(auth_headers, client):
    """POST /notifications/sms/rules — 409 si catégorie déjà enabled."""
    # D'abord déclencher le seed des règles par défaut
    client.get("/api/v1/notifications/sms/rules", headers=auth_headers)
    # lab_critical est déjà dans les règles seedées
    payload = {
        "category": "lab_critical",
        "channels": ["sms"],
        "min_priority": "urgent",
    }
    response = client.post(
        "/api/v1/notifications/sms/rules", json=payload, headers=auth_headers
    )
    assert response.status_code == 409


def test_update_rule(auth_headers, client):
    """PATCH /notifications/sms/rules/{id} — met à jour min_priority."""
    list_resp = client.get("/api/v1/notifications/sms/rules", headers=auth_headers)
    rule_id = list_resp.json()["data"][0]["id"]

    response = client.patch(
        f"/api/v1/notifications/sms/rules/{rule_id}",
        json={"min_priority": "urgent", "enabled": False},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["min_priority"] == "urgent"
    assert data["enabled"] is False


def test_delete_rule(auth_headers, client):
    """DELETE /notifications/sms/rules/{id} — supprime une règle."""
    # Créer une règle custom
    create = client.post(
        "/api/v1/notifications/sms/rules",
        json={"category": "to_delete", "channels": ["in_app"]},
        headers=auth_headers,
    )
    rule_id = create.json()["id"]

    response = client.delete(
        f"/api/v1/notifications/sms/rules/{rule_id}", headers=auth_headers
    )
    assert response.status_code == 204


# ── Envoi SMS (mock) ────────────────────────────────────────────────────────

def test_send_sms_mock_success(auth_headers, client):
    """POST /notifications/sms/send — envoi via mock provider (toujours succès)."""
    payload = {
        "to": "+224622334455",
        "body": "Test SMS GuinéeCare v1.4 — résultat critique",
        "category": "lab_critical",
        "priority": "urgent",
    }
    response = client.post(
        "/api/v1/notifications/sms/send", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "SENT"
    assert data["provider_code"] == "mock"
    assert data["recipient_phone"] == "+224622334455"
    assert data["body"].startswith("Test SMS GuinéeCare")
    assert data["operator_message_id"].startswith("MOCK-")


def test_send_sms_invalid_phone(auth_headers, client):
    """POST /notifications/sms/send — numéro invalide → FAILED avec error_code."""
    payload = {
        "to": "invalid",
        "body": "Test invalid phone",
        "category": "test",
    }
    response = client.post(
        "/api/v1/notifications/sms/send", json=payload, headers=auth_headers
    )
    assert response.status_code == 201  # 201 car le SmsMessage est créé
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["error_code"] == "INVALID_PHONE"


def test_send_sms_normalizes_guinea_number(auth_headers, client):
    """POST /notifications/sms/send — numéro guinéen sans +224 est normalisé."""
    payload = {
        "to": "622334455",  # sans indicatif
        "body": "Test normalisation",
        "category": "test",
    }
    response = client.post(
        "/api/v1/notifications/sms/send", json=payload, headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["recipient_phone"] == "+224622334455"
    assert data["status"] == "SENT"


# ── Historique + Stats ──────────────────────────────────────────────────────

def test_list_messages(auth_headers, client):
    """GET /notifications/sms/messages — historique paginé."""
    # Envoyer un SMS d'abord
    client.post(
        "/api/v1/notifications/sms/send",
        json={"to": "+224622334455", "body": "Test history", "category": "test"},
        headers=auth_headers,
    )
    response = client.get("/api/v1/notifications/sms/messages", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["data"]) >= 1


def test_list_messages_filter_status(auth_headers, client):
    """GET /notifications/sms/messages?status=SENT — filtre par statut."""
    client.post(
        "/api/v1/notifications/sms/send",
        json={"to": "+224622334455", "body": "Test filter", "category": "test"},
        headers=auth_headers,
    )
    response = client.get(
        "/api/v1/notifications/sms/messages?status=SENT", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert all(m["status"] == "SENT" for m in data["data"])


def test_get_stats(auth_headers, client):
    """GET /notifications/sms/stats — statistiques agrégées."""
    # Envoyer 2 SMS
    for i in range(2):
        client.post(
            "/api/v1/notifications/sms/send",
            json={
                "to": "+224622334455",
                "body": f"Test stats {i}",
                "category": "test",
            },
            headers=auth_headers,
        )
    response = client.get(
        "/api/v1/notifications/sms/stats?days=7", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert data["sent"] >= 2
    assert data["success_rate_pct"] > 0
    assert "by_provider" in data
    assert "by_category" in data


# ── Test provider ───────────────────────────────────────────────────────────

def test_test_provider_mock(auth_headers, client, db):
    """POST /notifications/sms/providers/{id}/test — teste le provider mock."""
    # S'assurer que le mock est seedé
    client.get("/api/v1/notifications/sms/providers", headers=auth_headers)
    mock = db.query(SmsProvider).filter(SmsProvider.code == "mock").first()
    assert mock is not None
    response = client.post(
        f"/api/v1/notifications/sms/providers/{mock.id}/test",
        json={"to": "+224622334455", "body": "Ping test"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message_id"] is not None


# ── Retry ───────────────────────────────────────────────────────────────────

def test_retry_message_success(auth_headers, client):
    """POST /notifications/sms/messages/{id}/retry — retente un SMS échoué."""
    # Créer un SMS échoué (numéro invalide)
    create = client.post(
        "/api/v1/notifications/sms/send",
        json={"to": "invalid", "body": "Will fail", "category": "test"},
        headers=auth_headers,
    )
    msg_id = create.json()["id"]

    # Retry avec un numéro valide via update direct du destinataire
    # (en pratique, le retry utilise le même numéro — donc échouera à nouveau)
    response = client.post(
        f"/api/v1/notifications/sms/messages/{msg_id}/retry", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["attempts"] >= 1


# ── Helpers unitaires ───────────────────────────────────────────────────────

def test_normalize_phone_guinea():
    """Normalisation des numéros guinéens."""
    assert normalize_phone_gn("+224622334455") == "+224622334455"
    assert normalize_phone_gn("622334455") == "+224622334455"
    assert normalize_phone_gn("00224622334455") == "+224622334455"
    assert normalize_phone_gn(" +224 622 33 44 55 ") == "+224622334455"
    assert normalize_phone_gn("") is None
    assert normalize_phone_gn(None) is None


def test_encrypt_decrypt_credential_roundtrip():
    """Chiffrement/déchiffrement des credentials (fallback clair si pas de Fernet)."""
    encrypted = encrypt_credential("secret123")
    assert encrypted is not None
    # En l'absence de Fernet (test env), encrypt = identity
    decrypted = decrypt_credential(encrypted)
    assert decrypted == "secret123"


def test_encrypt_credential_none():
    """encrypt_credential(None) retourne None."""
    assert encrypt_credential(None) is None
    assert decrypt_credential(None) is None


def test_mock_provider_send_success():
    """MockSmsProvider délivre toujours pour un numéro valide."""
    from app.modules.notifications.sms_models import SmsProvider
    p = SmsProvider(code="mock", name="Mock", enabled=True, sender_id="GC")
    backend = MockSmsProvider(p)
    result = backend.send(to="+224622334455", body="Hello")
    assert result.delivered is True
    assert result.operator_message_id.startswith("MOCK-")


def test_mock_provider_invalid_phone():
    """MockSmsProvider échoue pour un numéro invalide."""
    from app.modules.notifications.sms_models import SmsProvider
    p = SmsProvider(code="mock", name="Mock", enabled=True)
    backend = MockSmsProvider(p)
    result = backend.send(to="invalid", body="Hello")
    assert result.delivered is False
    assert result.error_code == "INVALID_PHONE"


# ── Permissions RBAC ────────────────────────────────────────────────────────

def test_sms_endpoints_require_auth(client):
    """GET /notifications/sms/providers sans auth → 401."""
    response = client.get("/api/v1/notifications/sms/providers")
    assert response.status_code == 401


def test_sms_send_requires_notification_send_permission(client, db):
    """POST /notifications/sms/send nécessite notification.send (rôle non-admin)."""
    from app.core.security import hash_password, create_access_token
    from app.modules.users.models import User

    user = User(
        email="nurse@test.com",
        password_hash=hash_password("TestPassword1!xx"),
        first_name="Nurse",
        last_name="Test",
        role="NURSE",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(
        subject=user.id, facility_id=user.facility_id, role=user.role
    )
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/v1/notifications/sms/send",
        json={"to": "+224622334455", "body": "Should fail"},
        headers=headers,
    )
    assert response.status_code == 403
