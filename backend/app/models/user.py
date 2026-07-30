"""
User ORM model.

Defines the `User` entity and its `Role` enum. Designed to be the
central identity record that future modules (courses, projects,
IPBL teams, etc.) will reference via foreign keys.
"""
import enum
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Role(str, enum.Enum):
    """Application-wide user roles."""

    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    FACULTY = "FACULTY"
    STUDENT = "STUDENT"


class User(Base):
    """
    Registered user of the VTU AI Study Portal.

    `id` is the internal surrogate primary key used for efficient
    foreign-key relationships from future modules (courses, projects,
    submissions, etc.). `uuid` is the stable, non-guessable public
    identifier exposed through the API.
    """

    __tablename__ = "users"
    __table_args__ = {"comment": "Registered users of the VTU AI Study Portal."}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
         unique=True,
         nullable=False,
         default=uuid4,
         index=True,
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), unique=True, nullable=True, index=True
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    role: Mapped[Role] = mapped_column(
        Enum(Role, name="user_role", native_enum=True),
        nullable=False,
        default=Role.STUDENT,
        server_default=Role.STUDENT.value,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ------------------------------------------------------------------
    # Relationships are intentionally not yet declared here. Future
    # modules (e.g. IPBL projects, courses, submissions) will add
    # `relationship(..., back_populates="user")` mappings on this model
    # once those entities exist, keeping this model forward-compatible
    # without requiring structural changes.
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username!r} role={self.role}>"
