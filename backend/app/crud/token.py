"""CRUD operations for revoked JWT tokens (`TokenBlacklist`)."""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.token_blacklist import TokenBlacklist


def blacklist_token(
    db: Session, jti: str, token_type: str, expires_at: datetime
) -> TokenBlacklist:
    """Record a token's `jti` as revoked so it can no longer be used."""
    entry = TokenBlacklist(jti=jti, token_type=token_type, expires_at=expires_at)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def is_token_blacklisted(db: Session, jti: str) -> bool:
    """Check whether a token identifier has been revoked."""
    return (
        db.scalar(select(TokenBlacklist).where(TokenBlacklist.jti == jti)) is not None
    )
