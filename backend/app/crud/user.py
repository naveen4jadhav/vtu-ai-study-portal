"""
CRUD operations for the `User` model.

Pure data-access layer: no business rules, no HTTP concerns. Services
compose these functions to implement authentication and profile logic.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import Role, User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Fetch a user by internal integer primary key."""
    return db.get(User, user_id)


def get_user_by_uuid(db: Session, user_uuid: uuid.UUID) -> Optional[User]:
    """Fetch a user by public UUID."""
    return db.scalar(select(User).where(User.uuid == user_uuid))


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Fetch a user by email address (case-insensitive)."""
    return db.scalar(select(User).where(func_lower_eq(User.email, email)))


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Fetch a user by username (case-insensitive)."""
    return db.scalar(select(User).where(func_lower_eq(User.username, username)))


def get_user_by_login_identifier(db: Session, identifier: str) -> Optional[User]:
    """Fetch a user by email OR username, whichever the identifier matches."""
    normalized = identifier.strip().lower()
    return db.scalar(
        select(User).where(
            or_(
                func_lower_eq(User.email, normalized),
                func_lower_eq(User.username, normalized),
            )
        )
    )


def create_user(db: Session, user_in: UserCreate, role: Optional[Role] = None) -> User:
    """Persist a new user with a securely hashed password."""
    user = User(
        full_name=user_in.full_name,
        email=user_in.email.lower(),
        phone=user_in.phone,
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        role=role or user_in.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    """Apply partial profile updates to an existing user."""
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_password(db: Session, user: User, new_hashed_password: str) -> User:
    """Persist a new password hash for the given user."""
    user.hashed_password = new_hashed_password
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_last_login(db: Session, user: User) -> User:
    """Record the current timestamp as the user's most recent login."""
    user.last_login = datetime.now(timezone.utc)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user: User) -> User:
    """Soft-delete a user by marking their account inactive."""
    user.is_active = False
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> None:
    """Permanently remove a user record."""
    db.delete(user)
    db.commit()


def func_lower_eq(column, value: str):
    """Build a case-insensitive equality expression for a string column."""
    return func.lower(column) == value.lower()
