"""Modèle 2FA/MFA v1.8.0 — authentification à deux facteurs TOTP.

Stocke le secret TOTP + codes de secours pour chaque utilisateur.
Le 2FA est optionnel (l'utilisateur l'active depuis son profil).

Workflow :
1. POST /auth/2fa/setup → génère un secret + QR code (base64 PNG)
2. User scanne le QR avec Google Authenticator / Authy / Microsoft Authenticator
3. POST /auth/2fa/verify → user saisit le code TOTP → active le 2FA
4. Au login : POST /auth/login → si 2FA activé, retourne {requires_2fa: true, challenge: ...}
5. POST /auth/2fa/challenge → user saisit le code TOTP → obtient le token

Codes de secours : 10 codes à usage unique, générés au setup.
Si l'utilisateur perd son téléphone, il peut utiliser un code de secours.
"""
import secrets
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text

from app.core.datetime import utcnow
from app.db.base import Base


class UserTwoFactor(Base):
    """Configuration 2FA d'un utilisateur.

    Un utilisateur peut avoir au maximum une entrée active.
    Si `enabled` est False, le 2FA est désactivé (mais le secret est conservé
    pour réactivation rapide).
    """
    __tablename__ = "user_two_factors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True, unique=True)
    
    # Secret TOTP (Base32, 32 chars)
    totp_secret = Column(String(64), nullable=False)
    
    # Codes de secours (JSON array de 10 codes, hashés)
    backup_codes_hash = Column(Text, nullable=True)
    backup_codes_used = Column(Text, nullable=True)  # JSON array des codes déjà utilisés
    
    # État
    enabled = Column(Boolean, nullable=False, default=False)
    enabled_at = Column(DateTime, nullable=True)
    
    # Métadonnées
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "enabled": bool(self.enabled),
            "enabled_at": self.enabled_at.isoformat() if self.enabled_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
