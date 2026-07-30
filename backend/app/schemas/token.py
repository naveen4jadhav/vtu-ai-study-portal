"""Token-related Pydantic schemas."""
from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Access + refresh token pair returned on login and refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class TokenRefresh(BaseModel):
    """Payload for requesting a new token pair from a refresh token."""

    refresh_token: str


class TokenPayload(BaseModel):
    """Decoded JWT claims used internally by the authentication layer."""

    sub: Optional[str] = None
    jti: Optional[str] = None
    type: Optional[str] = None
    exp: Optional[int] = None
