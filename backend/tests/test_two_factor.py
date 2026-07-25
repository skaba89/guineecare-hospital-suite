"""Tests du module 2FA/MFA v1.8.0 — setup, verify, challenge, backup codes."""
import pyotp
from app.modules.auth.two_factor_service import (
    generate_totp_secret,
    generate_backup_codes,
    verify_totp_code,
    hash_backup_code,
    hash_all_backup_codes,
    verify_backup_code,
    setup_2fa,
    enable_2fa,
    disable_2fa,
    verify_2fa_challenge,
    is_2fa_enabled,
    get_remaining_backup_codes,
)
from app.modules.auth.two_factor_models import UserTwoFactor
from app.modules.users.models import User
from app.core.security import hash_password


def _create_user(db):
    user = User(
        email="test2fa@guineecare.com",
        password_hash=hash_password("TestPass1!"),
        first_name="Test",
        last_name="2FA",
        role="SUPER_ADMIN",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_generate_totp_secret():
    """Le secret TOTP est Base32 (32 chars)."""
    secret = generate_totp_secret()
    assert len(secret) == 32
    # Base32 valid
    import base64
    try:
        base64.b32decode(secret)
    except Exception:
        assert False, "Secret not valid Base32"


def test_generate_backup_codes():
    """10 codes de secours de 8 chiffres."""
    codes = generate_backup_codes(10)
    assert len(codes) == 10
    for c in codes:
        assert len(c) == 8
        assert c.isdigit()


def test_verify_totp_code_valid():
    """Un code TOTP valide est accepté."""
    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert verify_totp_code(secret, code) is True


def test_verify_totp_code_invalid():
    """Un code TOTP invalide est rejeté."""
    secret = generate_totp_secret()
    assert verify_totp_code(secret, "000000") is False


def test_hash_backup_code():
    """Le hash n'est pas le code en clair."""
    code = "12345678"
    h = hash_backup_code(code)
    assert h != code
    assert len(h) == 64  # SHA-256 hex


def test_verify_backup_code_valid(db):
    """Un code de secours valide est accepté."""
    codes = generate_backup_codes(10)
    hashes = hash_all_backup_codes(codes)
    # Use first code
    is_valid, updated = verify_backup_code(codes[0], hashes, "[]")
    assert is_valid is True
    # Second use of same code should fail
    is_valid2, _ = verify_backup_code(codes[0], hashes, updated)
    assert is_valid2 is False


def test_setup_2fa(db):
    """setup_2fa génère secret + backup codes + QR URI."""
    user = _create_user(db)
    result = setup_2fa(db, user.id)
    assert "secret" in result
    assert len(result["secret"]) == 32
    assert "qr_uri" in result
    assert "otpauth://" in result["qr_uri"]
    assert "backup_codes" in result
    assert len(result["backup_codes"]) == 10
    # Vérifier en DB
    row = db.query(UserTwoFactor).filter(UserTwoFactor.user_id == user.id).first()
    assert row is not None
    assert row.enabled is False
    assert row.totp_secret == result["secret"]


def test_enable_2fa(db):
    """enable_2fa active le 2FA avec un code TOTP valide."""
    user = _create_user(db)
    result = setup_2fa(db, user.id)
    # Générer un code valide
    totp = pyotp.TOTP(result["secret"])
    code = totp.now()
    success, msg = enable_2fa(db, user.id, code)
    assert success is True
    assert is_2fa_enabled(db, user.id) is True


def test_enable_2fa_invalid_code(db):
    """enable_2fa échoue avec un code invalide."""
    user = _create_user(db)
    setup_2fa(db, user.id)
    success, msg = enable_2fa(db, user.id, "000000")
    assert success is False
    assert "invalide" in msg.lower()


def test_disable_2fa(db):
    """disable_2fa désactive le 2FA."""
    user = _create_user(db)
    result = setup_2fa(db, user.id)
    totp = pyotp.TOTP(result["secret"])
    enable_2fa(db, user.id, totp.now())
    assert is_2fa_enabled(db, user.id) is True
    disable_2fa(db, user.id)
    assert is_2fa_enabled(db, user.id) is False


def test_verify_2fa_challenge_totp(db):
    """verify_2fa_challenge accepte un code TOTP valide."""
    user = _create_user(db)
    result = setup_2fa(db, user.id)
    totp = pyotp.TOTP(result["secret"])
    enable_2fa(db, user.id, totp.now())
    # Nouveau code pour le challenge
    code = totp.now()
    success, msg = verify_2fa_challenge(db, user.id, code)
    assert success is True


def test_verify_2fa_challenge_backup_code(db):
    """verify_2fa_challenge accepte un code de secours."""
    user = _create_user(db)
    result = setup_2fa(db, user.id)
    totp = pyotp.TOTP(result["secret"])
    enable_2fa(db, user.id, totp.now())
    # Utiliser un backup code
    backup = result["backup_codes"][0]
    success, msg = verify_2fa_challenge(db, user.id, backup)
    assert success is True
    # Vérifier que le code est marqué comme utilisé
    remaining = get_remaining_backup_codes(db, user.id)
    assert remaining == 9


def test_verify_2fa_challenge_no_2fa(db):
    """verify_2fa_challenge retourne True si 2FA non activé."""
    user = _create_user(db)
    success, msg = verify_2fa_challenge(db, user.id, "any")
    assert success is True


def test_get_remaining_backup_codes(db):
    """get_remaining_backup_codes retourne 10 au départ, 9 après usage."""
    user = _create_user(db)
    result = setup_2fa(db, user.id)
    totp = pyotp.TOTP(result["secret"])
    enable_2fa(db, user.id, totp.now())
    assert get_remaining_backup_codes(db, user.id) == 10
    # Utiliser un backup
    verify_2fa_challenge(db, user.id, result["backup_codes"][0])
    assert get_remaining_backup_codes(db, user.id) == 9


def test_2fa_endpoints(auth_headers, client, db):
    """Test complet des endpoints 2FA via API."""
    # 1. Setup
    r = client.post("/api/v1/auth/2fa/setup", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert "secret" in data
    assert "qr_uri" in data
    assert "backup_codes" in data
    
    # 2. Verify with valid TOTP
    totp = pyotp.TOTP(data["secret"])
    code = totp.now()
    r = client.post("/api/v1/auth/2fa/verify", json={"code": code}, headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["two_factor_enabled"] is True
    
    # 3. Check /auth/me includes 2FA info
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["two_factor_enabled"] is True
    assert r.json()["backup_codes_remaining"] == 10
    
    # 4. Disable
    r = client.post("/api/v1/auth/2fa/disable", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["two_factor_enabled"] is False
