"""Provider abstraction pour SMS v1.4.0.

Permet d'envoyer des SMS via différents opérateurs locaux guinéens :
- Orange Guinée SMS Pro (https://api.orange.com/sms)
- MTN Guinée SMS Gateway
- Moov Africa SMS API
- MockProvider (toujours en succès, in-process — pour tests/dev)

Chaque provider implémente l'interface `SmsProviderBase.send()`. Les credentials
sont récupérés depuis la table `SmsProvider` (départ chiffrés).

Conventions :
- Best-effort : aucune exception n'est propagée à l'appelant. Les échecs sont
  retournés dans `SmsSendResult` pour journalisation dans `SmsMessage`.
- HTTP timeout : 10s (opérateurs guinéens parfois lents).
- Retry policy : gérée par le service, pas par le provider (idempotence).
"""
import json
import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import requests

from app.core.datetime import utcnow
from app.modules.notifications.sms_models import SmsProvider

logger = logging.getLogger("guineecare.sms")


# ---------------------------------------------------------------------------
# Chiffrement optionnel des credentials (Fernet si FERNET_KEY est défini)
# ---------------------------------------------------------------------------

_fernet = None
try:
    from cryptography.fernet import Fernet  # type: ignore

    _fernet_key = os.environ.get("SMS_FERNET_KEY")
    if _fernet_key:
        _fernet = Fernet(_fernet_key.encode() if isinstance(_fernet_key, str) else _fernet_key)
except ImportError:
    pass  # cryptography absent — fallback clair en local/test uniquement


def encrypt_credential(value: str | None) -> str | None:
    """Chiffre un secret côté service. Fallback en clair si Fernet indisponible."""
    if not value:
        return None
    if _fernet is None:
        return value  # mode dev/test — non chiffré
    return _fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_credential(value: str | None) -> str | None:
    """Déchiffre un secret. Si Fernet absent, retourne la valeur telle quelle."""
    if not value:
        return None
    if _fernet is None:
        return value
    try:
        return _fernet.decrypt(value.encode("utf-8")).decode("utf-8")
    except Exception:
        # Peut-être une valeur en clair héritée d'une install sans Fernet
        return value


# ---------------------------------------------------------------------------
# Result object
# ---------------------------------------------------------------------------

@dataclass
class SmsSendResult:
    """Résultat d'une tentative d'envoi SMS sur un provider donné."""
    delivered: bool
    operator_message_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    cost_gnf: int = 0
    sent_at: datetime | None = field(default_factory=utcnow)


# ---------------------------------------------------------------------------
# Base interface
# ---------------------------------------------------------------------------

class SmsProviderBase:
    """Interface commune à tous les providers SMS."""

    code: str = "base"
    name: str = "Base Provider"

    def __init__(self, config: SmsProvider):
        self.config = config
        self.api_url = config.api_url or ""
        self.sender_id = config.sender_id or "GUINEECARE"
        self.api_key = decrypt_credential(config.api_key_encrypted)
        self.api_secret = decrypt_credential(config.api_secret_encrypted)
        self.cost_per_sms = config.cost_per_sms_gnf or 0

    @property
    def enabled(self) -> bool:
        """Un provider est enabled si sa config DB l'active ET qu'il a ses credentials."""
        return bool(self.config.enabled) and bool(self.api_key or self.code == "mock")

    def send(self, *, to: str, body: str, **kwargs) -> SmsSendResult:
        """Envoie un SMS. NE LEVE JAMAIS d'exception — toujours retourner un result."""
        raise NotImplementedError

    def _validate_phone(self, to: str) -> bool:
        """Validation E.164 : +224XXXXXXXXX (Guinée) ou +XXX... (international)."""
        if not to:
            return False
        # E.164 : + suivi de 6 à 15 chiffres
        if not to.startswith("+"):
            return False
        digits = to[1:]
        return digits.isdigit() and 6 <= len(digits) <= 15


# ---------------------------------------------------------------------------
# Mock Provider — pour tests et démos. Enregistre dans un fichier JSONL
# optionnel (SMS_MOCK_LOG) pour audit local. Jamais d'appel réseau.
# ---------------------------------------------------------------------------

class MockSmsProvider(SmsProviderBase):
    code = "mock"
    name = "Mock Provider (dev/test)"

    @property
    def enabled(self) -> bool:
        # Le mock est toujours enabled — utile en dev/test sans credentials
        return bool(self.config.enabled) if self.config else True

    def send(self, *, to: str, body: str, **kwargs) -> SmsSendResult:
        if not self._validate_phone(to):
            return SmsSendResult(
                delivered=False,
                error_code="INVALID_PHONE",
                error_message=f"Numéro invalide (format E.164 attendu): {to}",
                cost_gnf=0,
            )

        mock_msg_id = f"MOCK-{secrets.token_hex(8)}"
        logger.info("[sms:mock] to=%s body=%r msg_id=%s", to, body[:80], mock_msg_id)

        # Log optionnel vers JSONL pour audit local (dev only)
        log_file = os.environ.get("SMS_MOCK_LOG")
        if log_file:
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "ts": utcnow().isoformat(),
                        "to": to,
                        "body": body,
                        "msg_id": mock_msg_id,
                    }, ensure_ascii=False) + "\n")
            except OSError as e:
                logger.warning("SMS mock log write failed: %s", e)

        return SmsSendResult(
            delivered=True,
            operator_message_id=mock_msg_id,
            cost_gnf=0,  # gratuit en mock
        )


# ---------------------------------------------------------------------------
# Orange Guinée SMS Pro — implémentation conforme à la doc Orange API
# (OAuth2 client_credentials → POST /smsmessaging/v1/outbound/{sender}/requests)
# ---------------------------------------------------------------------------

class OrangeSmsProvider(SmsProviderBase):
    code = "orange"
    name = "Orange Guinée SMS Pro"

    # Endpoint par défaut si non surchargé par la config
    DEFAULT_API_URL = "https://api.orange.com/smsmessaging/v1/outbound/tel%3A%2B{sender}/requests"
    DEFAULT_OAUTH_URL = "https://api.orange.com/oauth/v3/token"

    def send(self, *, to: str, body: str, **kwargs) -> SmsSendResult:
        if not self._validate_phone(to):
            return SmsSendResult(
                delivered=False,
                error_code="INVALID_PHONE",
                error_message=f"Numéro invalide: {to}",
            )
        if not self.api_key or not self.api_secret:
            return SmsSendResult(
                delivered=False,
                error_code="MISSING_CREDENTIALS",
                error_message="Orange provider requires api_key + api_secret",
            )

        try:
            # Étape 1 : obtenir un token OAuth2
            token = self._get_oauth_token()
            if not token:
                return SmsSendResult(
                    delivered=False,
                    error_code="OAUTH_FAILED",
                    error_message="Impossible d'obtenir le token OAuth2 Orange",
                )

            # Étape 2 : envoyer le SMS
            sender_encoded = f"tel:+{self.sender_id.lstrip('+')}"
            url = self.api_url or self.DEFAULT_API_URL.replace("{sender}", self.sender_id.lstrip("+"))
            payload = {
                "outboundSMSMessageRequest": {
                    "address": [f"tel:{to}"],
                    "senderAddress": sender_encoded,
                    "outboundSMSTextMessage": {"message": body[:480]},
                }
            }
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)

            if resp.status_code in (200, 201):
                data = resp.json() if resp.text else {}
                msg_id = (
                    data.get("outboundSMSMessageRequest", {}).get("resourceURL")
                    or f"ORANGE-{secrets.token_hex(6)}"
                )
                return SmsSendResult(
                    delivered=True,
                    operator_message_id=msg_id,
                    cost_gnf=self.cost_per_sms,
                )
            return SmsSendResult(
                delivered=False,
                error_code=f"HTTP_{resp.status_code}",
                error_message=resp.text[:500],
                cost_gnf=0,
            )
        except requests.Timeout:
            return SmsSendResult(
                delivered=False,
                error_code="TIMEOUT",
                error_message="Orange API timeout (>10s)",
            )
        except requests.RequestException as e:
            return SmsSendResult(
                delivered=False,
                error_code="NETWORK_ERROR",
                error_message=str(e)[:500],
            )
        except Exception as e:
            logger.exception("Orange SMS unexpected error")
            return SmsSendResult(
                delivered=False,
                error_code="UNEXPECTED",
                error_message=str(e)[:500],
            )

    def _get_oauth_token(self) -> str | None:
        """OAuth2 client_credentials flow."""
        try:
            # Basic auth = base64(client_id:client_secret)
            auth = (self.api_key, self.api_secret)
            resp = requests.post(
                self.DEFAULT_OAUTH_URL,
                data={"grant_type": "client_credentials"},
                auth=auth,
                timeout=10,
            )
            if resp.status_code == 200:
                return resp.json().get("access_token")
            logger.warning("Orange OAuth failed: %s %s", resp.status_code, resp.text[:200])
            return None
        except Exception as e:
            logger.warning("Orange OAuth exception: %s", e)
            return None


# ---------------------------------------------------------------------------
# MTN Guinée SMS Gateway — HTTP POST simple avec authentification par clé API
# Doc : https://developers.mtn.com (variable selon le pays)
# ---------------------------------------------------------------------------

class MtnSmsProvider(SmsProviderBase):
    code = "mtn"
    name = "MTN Guinée SMS Gateway"

    DEFAULT_API_URL = "https://api.mtn.com/v1/sms/send"

    def send(self, *, to: str, body: str, **kwargs) -> SmsSendResult:
        if not self._validate_phone(to):
            return SmsSendResult(
                delivered=False,
                error_code="INVALID_PHONE",
                error_message=f"Numéro invalide: {to}",
            )
        if not self.api_key:
            return SmsSendResult(
                delivered=False,
                error_code="MISSING_CREDENTIALS",
                error_message="MTN provider requires api_key",
            )

        try:
            url = self.api_url or self.DEFAULT_API_URL
            payload = {
                "to": to,
                "from": self.sender_id,
                "message": body[:480],
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=10)

            if resp.status_code in (200, 201, 202):
                data = resp.json() if resp.text else {}
                msg_id = data.get("messageId") or data.get("id") or f"MTN-{secrets.token_hex(6)}"
                return SmsSendResult(
                    delivered=True,
                    operator_message_id=msg_id,
                    cost_gnf=self.cost_per_sms,
                )
            return SmsSendResult(
                delivered=False,
                error_code=f"HTTP_{resp.status_code}",
                error_message=resp.text[:500],
            )
        except requests.Timeout:
            return SmsSendResult(
                delivered=False,
                error_code="TIMEOUT",
                error_message="MTN API timeout",
            )
        except requests.RequestException as e:
            return SmsSendResult(
                delivered=False,
                error_code="NETWORK_ERROR",
                error_message=str(e)[:500],
            )
        except Exception as e:
            logger.exception("MTN SMS unexpected error")
            return SmsSendResult(
                delivered=False,
                error_code="UNEXPECTED",
                error_message=str(e)[:500],
            )


# ---------------------------------------------------------------------------
# Moov Africa SMS API — HTTP POST avec clé API et sender ID
# ---------------------------------------------------------------------------

class MoovSmsProvider(SmsProviderBase):
    code = "moov"
    name = "Moov Africa SMS API"

    DEFAULT_API_URL = "https://api.moov-africa.com/v1/sms/send"

    def send(self, *, to: str, body: str, **kwargs) -> SmsSendResult:
        if not self._validate_phone(to):
            return SmsSendResult(
                delivered=False,
                error_code="INVALID_PHONE",
                error_message=f"Numéro invalide: {to}",
            )
        if not self.api_key:
            return SmsSendResult(
                delivered=False,
                error_code="MISSING_CREDENTIALS",
                error_message="Moov provider requires api_key",
            )

        try:
            url = self.api_url or self.DEFAULT_API_URL
            payload = {
                "recipient": to,
                "sender": self.sender_id,
                "text": body[:480],
                "api_key": self.api_key,  # Moov utilise souvent body plutôt que header
            }
            headers = {
                "Content-Type": "application/json",
            }
            if self.api_secret:
                headers["X-Api-Signature"] = self.api_secret

            resp = requests.post(url, json=payload, headers=headers, timeout=10)

            if resp.status_code in (200, 201, 202):
                data = resp.json() if resp.text else {}
                msg_id = data.get("message_id") or data.get("id") or f"MOOV-{secrets.token_hex(6)}"
                return SmsSendResult(
                    delivered=True,
                    operator_message_id=msg_id,
                    cost_gnf=self.cost_per_sms,
                )
            return SmsSendResult(
                delivered=False,
                error_code=f"HTTP_{resp.status_code}",
                error_message=resp.text[:500],
            )
        except requests.Timeout:
            return SmsSendResult(
                delivered=False,
                error_code="TIMEOUT",
                error_message="Moov API timeout",
            )
        except requests.RequestException as e:
            return SmsSendResult(
                delivered=False,
                error_code="NETWORK_ERROR",
                error_message=str(e)[:500],
            )
        except Exception as e:
            logger.exception("Moov SMS unexpected error")
            return SmsSendResult(
                delivered=False,
                error_code="UNEXPECTED",
                error_message=str(e)[:500],
            )


# ---------------------------------------------------------------------------
# Factory : retourne la bonne classe de provider selon le code
# ---------------------------------------------------------------------------

_PROVIDER_CLASSES: dict[str, type[SmsProviderBase]] = {
    "mock": MockSmsProvider,
    "orange": OrangeSmsProvider,
    "mtn": MtnSmsProvider,
    "moov": MoovSmsProvider,
}


def get_provider_class(code: str) -> type[SmsProviderBase]:
    """Retourne la classe de provider pour un code donné. Fallback sur mock."""
    return _PROVIDER_CLASSES.get(code, MockSmsProvider)


def list_supported_providers() -> list[dict[str, Any]]:
    """Liste les providers supportés par l'application (pour l'UI d'admin)."""
    return [
        {"code": "mock", "name": "Mock (dev/test)", "needs_credentials": False},
        {"code": "orange", "name": "Orange Guinée SMS Pro", "needs_credentials": True},
        {"code": "mtn", "name": "MTN Guinée SMS Gateway", "needs_credentials": True},
        {"code": "moov", "name": "Moov Africa SMS API", "needs_credentials": True},
    ]


def normalize_phone_gn(phone: str | None) -> str | None:
    """Normalise un numéro de téléphone guinéen au format E.164.

    Accepte :
    - "+224 622 33 44 55" → "+224622334455"
    - "622334455" → "+224622334455" (préfixe Guinée ajouté)
    - "00224622334455" → "+224622334455"

    Retourne None si le numéro ne peut être normalisé.
    """
    if not phone:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    if not digits:
        return None
    # Cas 1 : déjà en +224 ou 00224
    if digits.startswith("00224"):
        digits = digits[5:]
    elif digits.startswith("224") and len(digits) > 10:
        digits = digits[3:]
    # Numéro guinéen mobile = 9 chiffres (6XX XXX XXX ou 7XX)
    if len(digits) == 9 and digits[0] in ("6", "7"):
        return f"+224{digits}"
    # Déjà E.164 complet
    if phone.startswith("+") and digits:
        return f"+{digits}"
    return None
