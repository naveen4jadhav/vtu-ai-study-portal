"""
JWT service.

Issues and validates access/refresh token pairs. Each token carries a
unique `jti` claim so individual tokens can be revoked (see
`app.crud.token`) independently of their natural expiration.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.core.config import settings
from app.core.exceptions import ExpiredTokenError, InvalidTokenError
from app.schemas.token import TokenPayload

TokenType = Literal["access", "refresh"]


class JWTService:
    """Encapsulates creation and verification of JWT access/refresh tokens."""

    @staticmethod
    def _create_token(
        subject: str, token_type: TokenType, expires_delta: timedelta
    ) -> tuple[str, str, datetime]:
        expire = datetime.now(timezone.utc) + expires_delta
        jti = str(uuid.uuid4())
        payload = {
            "sub": subject,
            "type": token_type,
            "jti": jti,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return token, jti, expire

    def create_access_token(self, subject: str) -> tuple[str, str, datetime]:
        """Create a short-lived access token. Returns (token, jti, expires_at)."""
        return self._create_token(
            subject,
            "access",
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

    def create_refresh_token(self, subject: str) -> tuple[str, str, datetime]:
        """Create a long-lived refresh token. Returns (token, jti, expires_at)."""
        return self._create_token(
            subject,
            "refresh",
            timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

    @staticmethod
    def decode_token(token: str) -> TokenPayload:
        """
        Decode and validate a JWT's signature and expiration.

        Raises `ExpiredTokenError` or `InvalidTokenError` on failure.
        """
        try:
            claims = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except ExpiredSignatureError as exc:
            raise ExpiredTokenError("Token has expired.") from exc
        except JWTError as exc:
            raise InvalidTokenError("Token is invalid or malformed.") from exc

        return TokenPayload(**claims)

    def verify_token_type(self, payload: TokenPayload, expected: TokenType) -> None:
        """Ensure a decoded token payload is of the expected type."""
        if payload.type != expected:
            raise InvalidTokenError(f"Expected a {expected} token.")


jwt_service = JWTService()
