"""Service 2FA/MFA v1.8.0 — gestion TOTP + codes de secours.

Utilise pyotp pour générer/vérifier les codes TOTP (RFC 6238).
Compatible Google Authenticator, Authy, Microsoft Authenticator, FreeOTP.

Codes de secours : 10 codes de 8 chiffres, hashés en DB (jamais en clair
après le setup). L'utilisateur doit les sauvegarder à l'activation.
"""
import hashlib
import json
import logging
import secrets as _secrets
from datetime import datetime

import pyotp

from app.core.datetime import utcnow
from app.modules.auth.two_factor_models import UserTwoFactor

logger = logging.getLogger("guineecare.auth.2fa")


def generate_totp_secret() -> str:
    """Génère un secret TOTP Base32 (32 chars)."""
    return pyotp.random_base32()


def generate_backup_codes(count: int = 10) -> list[str]:
    """Génère `count` codes de secours de 8 chiffres."""
    return [f"{_secrets.randbelow(100000000):08d}" for _ in range(count)]


def hash_backup_code(code: str) -> str:
    """Hash un code de secours avec SHA-256 (pour stockage sécurisé)."""
    return hashlib.sha256(code.encode()).hexdigest()


def hash_all_backup_codes(codes: list[str]) -> str:
    """Hash tous les codes de secours → JSON pour stockage DB."""
    return json.dumps([hash_backup_code(c) for c in codes])


def verify_backup_code(code: str, stored_hashes_json: str, used_codes_json: str) -> tuple[bool, str]:
    """Vérifie si un code de secours est valide et non utilisé.
    
    Returns:
        (is_valid, updated_used_codes_json)
    """
    try:
        stored_hashes = json.loads(stored_hashes_json) if stored_hashes_json else []
        used_codes = json.loads(used_codes_json) if used_codes_json else []
    except (json.JSONDecodeError, TypeError):
        return False, used_codes_json or "[]"

    code_hash = hash_backup_code(code.strip())
    
    if code_hash in stored_hashes and code_hash not in used_codes:
        used_codes.append(code_hash)
        return True, json.dumps(used_codes)
    
    return False, used_codes_json or "[]"


def get_totp_provisioning_uri(secret: str, email: str, issuer: str = "GuinéeCare") -> str:
    """Génère l'URI otpauth:// pour le QR code."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def verify_totp_code(secret: str, code: str) -> bool:
    """Vérifie un code TOTP (fenêtre ±1 pour tolérance horloge)."""
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception:
        return False


def setup_2fa(db, user_id: str) -> dict:
    """Démarre le setup 2FA : génère secret + backup codes + QR URI.
    
    Ne active PAS le 2FA — l'utilisateur doit vérifier avec un code TOTP
    avant que `enabled` passe à True.
    
    Returns:
        {
            "secret": "...",
            "qr_uri": "otpauth://...",
            "backup_codes": ["12345678", ...],
        }
    """
    # Vérifier s'il existe déjà un setup
    existing = db.query(UserTwoFactor).filter(UserTwoFactor.user_id == user_id).first()
    
    secret = generate_totp_secret()
    backup_codes = generate_backup_codes()
    backup_hashes = hash_all_backup_codes(backup_codes)
    
    if existing:
        # Régénérer le secret (re-setup)
        existing.totp_secret = secret
        existing.backup_codes_hash = backup_hashes
        existing.backup_codes_used = "[]"
        existing.enabled = False
        existing.enabled_at = None
    else:
        row = UserTwoFactor(
            user_id=user_id,
            totp_secret=secret,
            backup_codes_hash=backup_hashes,
            backup_codes_used="[]",
            enabled=False,
        )
        db.add(row)
    
    db.commit()
    
    # Récupérer l'email pour l'URI
    from app.modules.users.models import User
    user = db.query(User).filter(User.id == user_id).first()
    email = user.email if user else "user@guineecare.gn"
    
    qr_uri = get_totp_provisioning_uri(secret, email)
    
    return {
        "secret": secret,
        "qr_uri": qr_uri,
        "backup_codes": backup_codes,
    }


def enable_2fa(db, user_id: str, totp_code: str) -> tuple[bool, str]:
    """Active le 2FA après vérification du code TOTP.
    
    Returns:
        (success, message)
    """
    row = db.query(UserTwoFactor).filter(UserTwoFactor.user_id == user_id).first()
    if not row:
        return False, "2FA non configuré. Appelez /auth/2fa/setup d'abord."
    
    if row.enabled:
        return True, "2FA déjà activé."
    
    if not verify_totp_code(row.totp_secret, totp_code):
        return False, "Code TOTP invalide."
    
    row.enabled = True
    row.enabled_at = utcnow()
    db.commit()
    
    logger.info("2FA enabled for user %s", user_id)
    return True, "2FA activé avec succès."


def disable_2fa(db, user_id: str) -> bool:
    """Désactive le 2FA (garde le secret pour réactivation)."""
    row = db.query(UserTwoFactor).filter(UserTwoFactor.user_id == user_id).first()
    if not row:
        return False
    row.enabled = False
    row.enabled_at = None
    db.commit()
    return True


def verify_2fa_challenge(db, user_id: str, code: str) -> tuple[bool, str]:
    """Vérifie un code 2FA au login (TOTP ou backup code).
    
    Returns:
        (success, message)
    """
    row = db.query(UserTwoFactor).filter(UserTwoFactor.user_id == user_id).first()
    if not row or not row.enabled:
        return True, "2FA non activé"  # pas de 2FA = pas de vérification
    
    # 1. Essayer le code TOTP
    if verify_totp_code(row.totp_secret, code):
        return True, "OK"
    
    # 2. Essayer le code de secours
    is_valid, updated_used = verify_backup_code(
        code, 
        row.backup_codes_hash or "[]",
        row.backup_codes_used or "[]"
    )
    if is_valid:
        row.backup_codes_used = updated_used
        db.commit()
        logger.info("Backup code used for user %s", user_id)
        return True, "OK (backup code)"
    
    return False, "Code 2FA invalide."


def is_2fa_enabled(db, user_id: str) -> bool:
    """Vérifie si le 2FA est activé pour un utilisateur.
    
    Défensif : si la table n'existe pas encore (migration non appliquée),
    retourne False au lieu de crasher.
    """
    try:
        row = db.query(UserTwoFactor).filter(UserTwoFactor.user_id == user_id).first()
        return bool(row and row.enabled)
    except Exception as e:
        logger.warning("is_2fa_enabled failed (table may not exist): %s", e)
        return False


def get_remaining_backup_codes(db, user_id: str) -> int:
    """Retourne le nombre de codes de secours restants.
    
    Défensif : retourne 0 si la table n'existe pas.
    """
    try:
        row = db.query(UserTwoFactor).filter(UserTwoFactor.user_id == user_id).first()
        if not row or not row.backup_codes_hash or not row.backup_codes_used:
            return 0
        import json
        total = len(json.loads(row.backup_codes_hash))
        used = len(json.loads(row.backup_codes_used))
        return max(0, total - used)
    except Exception as e:
        logger.warning("get_remaining_backup_codes failed: %s", e)
        return 0
