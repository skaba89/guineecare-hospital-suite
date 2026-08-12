"""Regression tests for the JWT implementation used by GuinéeCare."""
from datetime import timedelta

import jwt
import pytest

from app.core.security import create_access_token, decode_access_token


def test_access_token_round_trip_preserves_security_claims():
    token = create_access_token(
        subject="user-123",
        facility_id="facility-456",
        role="DOCTOR",
        expires_delta=timedelta(minutes=5),
        jti="jti-regression-test",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["facility_id"] == "facility-456"
    assert payload["role"] == "DOCTOR"
    assert payload["jti"] == "jti-regression-test"
    assert "iat" in payload
    assert "exp" in payload


def test_access_token_rejects_tampering():
    token = create_access_token(subject="user-123")
    header, payload, signature = token.split(".")
    tampered_signature = ("A" if signature[0] != "A" else "B") + signature[1:]

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(f"{header}.{payload}.{tampered_signature}")
