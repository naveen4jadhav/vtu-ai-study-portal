"""Unit tests for the JWT service (access/refresh token issuance and validation)."""
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.exceptions import ExpiredTokenError, InvalidTokenError
from app.services.jwt_service import jwt_service

SUBJECT = "11111111-1111-1111-1111-111111111111"


class TestTokenCreation:
    def test_access_token_has_correct_type_claim(self) -> None:
        token, jti, _ = jwt_service.create_access_token(SUBJECT)
        payload = jwt_service.decode_token(token)
        assert payload.type == "access"
        assert payload.sub == SUBJECT
        assert payload.jti == jti

    def test_refresh_token_has_correct_type_claim(self) -> None:
        token, jti, _ = jwt_service.create_refresh_token(SUBJECT)
        payload = jwt_service.decode_token(token)
        assert payload.type == "refresh"
        assert payload.sub == SUBJECT
        assert payload.jti == jti

    def test_access_and_refresh_tokens_have_unique_jti(self) -> None:
        _, access_jti, _ = jwt_service.create_access_token(SUBJECT)
        _, refresh_jti, _ = jwt_service.create_refresh_token(SUBJECT)
        assert access_jti != refresh_jti


class TestTokenValidation:
    def test_verify_token_type_passes_for_matching_type(self) -> None:
        token, _, _ = jwt_service.create_access_token(SUBJECT)
        payload = jwt_service.decode_token(token)
        jwt_service.verify_token_type(payload, "access")

    def test_verify_token_type_raises_for_mismatched_type(self) -> None:
        token, _, _ = jwt_service.create_refresh_token(SUBJECT)
        payload = jwt_service.decode_token(token)
        with pytest.raises(InvalidTokenError):
            jwt_service.verify_token_type(payload, "access")

    def test_decode_raises_for_invalid_signature(self) -> None:
        bad_token = jwt.encode(
            {"sub": SUBJECT, "type": "access", "jti": "x"},
            "a-completely-different-secret-key",
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(InvalidTokenError):
            jwt_service.decode_token(bad_token)

    def test_decode_raises_for_expired_token(self) -> None:
        expired_token = jwt.encode(
            {
                "sub": SUBJECT,
                "type": "access",
                "jti": "expired-jti",
                "exp": datetime.now(timezone.utc) - timedelta(minutes=5),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(ExpiredTokenError):
            jwt_service.decode_token(expired_token)

    def test_decode_raises_for_malformed_token(self) -> None:
        with pytest.raises(InvalidTokenError):
            jwt_service.decode_token("not-a-valid-jwt")
