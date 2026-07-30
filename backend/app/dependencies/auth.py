"""
Authentication and authorization dependencies.

Provides FastAPI dependencies for resolving the current user from a
bearer access token, and for enforcing role-based access control.
"""
import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, InactiveUserError, InvalidTokenError
from app.crud import token as token_crud
from app.crud import user as user_crud
from app.db.session import get_db
from app.models.user import Role, User
from app.schemas.token import TokenPayload
from app.services.jwt_service import jwt_service

bearer_scheme = HTTPBearer(auto_error=True, description="JWT access token.")


def get_current_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> TokenPayload:
    """Decode and validate the bearer access token, returning its claims."""
    payload = jwt_service.decode_token(credentials.credentials)
    jwt_service.verify_token_type(payload, "access")
    return payload


def get_current_user(
    payload: TokenPayload = Depends(get_current_token_payload),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the authenticated `User` from a validated access token."""
    if payload.jti and token_crud.is_token_blacklisted(db, payload.jti):
        raise InvalidTokenError("This access token has been revoked.")

    if payload.sub is None:
        raise InvalidTokenError("Access token is missing its subject claim.")

    try:
        subject_uuid = uuid.UUID(payload.sub)
    except ValueError as exc:
        raise InvalidTokenError("Access token subject is not a valid UUID.") from exc

    user = user_crud.get_user_by_uuid(db, subject_uuid)
    if user is None:
        raise InvalidTokenError("Access token does not map to an existing user.")

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Ensure the resolved user's account is active."""
    if not current_user.is_active:
        raise InactiveUserError("This account has been deactivated.")
    return current_user


def require_roles(*allowed_roles: Role):
    """
    Build a dependency that restricts access to the given roles.

    `SUPER_ADMIN` is always permitted, regardless of the roles listed,
    since it represents the highest privilege level in the system.
    """

    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role == Role.SUPER_ADMIN:
            return current_user
        if current_user.role not in allowed_roles:
            raise ForbiddenError(
                "You do not have permission to perform this action."
            )
        return current_user

    return dependency


admin_only = require_roles(Role.ADMIN)
faculty_only = require_roles(Role.FACULTY)
student_only = require_roles(Role.STUDENT)
