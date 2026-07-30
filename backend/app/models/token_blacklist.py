"""
Token blacklist ORM model.

Stores revoked JWT identifiers (`jti`) so that logout and refresh-token
rotation can invalidate tokens before their natural expiration, despite
JWTs being otherwise stateless.
"""
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class TokenBlacklist(Base):
    """A revoked JWT, identified by its unique `jti` claim."""

    __tablename__ = "token_blacklist"
    __table_args__ = {"comment": "Revoked JWT identifiers (access/refresh)."}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    jti: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, index=True
    )
    token_type: Mapped[str] = mapped_column(String(20), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TokenBlacklist jti={self.jti!r} type={self.token_type}>"
