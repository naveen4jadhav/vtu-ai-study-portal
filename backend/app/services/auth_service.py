"""
Authentication service.

Orchestrates the CRUD, password, and JWT layers to implement the
application's authentication use cases. This is the only layer that
API endpoints should talk to for auth-related business logic.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidPasswordError,
    InvalidTokenError,
)
from app.core.logging import get_logger
from app.crud import token as token_crud
from app.crud import user as user_crud
from app.models.user import Role, User
from app.schemas.token import Token
from app.schemas.user import PasswordChange, UserCreate
from app.services.jwt_service import jwt_service
from app.services.password_service import password_service

logger = get_logger("app.auth")


class AuthenticationService:
    """Implements registration, login, token refresh, logout, and password change."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------
    def register(self, user_in: UserCreate) -> User:
        """Register a new user, enforcing unique email/username constraints."""
        if user_crud.get_user_by_email(self.db, user_in.email):
            logger.warning("registration_failed reason=duplicate_email email=%s", user_in.email)
            raise DuplicateEmailError("A user with this email already exists.")

        if user_crud.get_user_by_username(self.db, user_in.username):
            logger.warning(
                "registration_failed reason=duplicate_username username=%s",
                user_in.username,
            )
            raise DuplicateUsernameError("A user with this username already exists.")

        # Self-service registration may never grant elevated roles; those
        # accounts are provisioned through a separate admin-only flow.
        user = user_crud.create_user(self.db, user_in, role=Role.STUDENT)
        logger.info(
            "user_registered user_id=%s username=%s email=%s",
            user.id,
            user.username,
            user.email,
        )
        return user

    # ------------------------------------------------------------------
    # Login
    # ------------------------------------------------------------------
    def authenticate(self, login: str, password: str) -> User:
        """Validate credentials and return the authenticated user."""
        user = user_crud.get_user_by_login_identifier(self.db, login)

        if user is None or not password_service.verify(password, user.hashed_password):
            logger.warning("login_failed reason=invalid_credentials login=%s", login)
            raise InvalidCredentialsError("Incorrect username/email or password.")

        if not user.is_active:
            logger.warning("login_failed reason=inactive_account user_id=%s", user.id)
            raise InactiveUserError("This account has been deactivated.")

        user_crud.update_last_login(self.db, user)
        logger.info("login_succeeded user_id=%s username=%s", user.id, user.username)
        return user

    def issue_token_pair(self, user: User) -> Token:
        """Create a new access/refresh token pair for the given user."""
        access_token, _, access_expire = jwt_service.create_access_token(str(user.uuid))
        refresh_token, _, _ = jwt_service.create_refresh_token(str(user.uuid))

        expires_in = int((access_expire - datetime.now(timezone.utc)).total_seconds())
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=max(expires_in, 0),
        )

    def login(self, login: str, password: str) -> Token:
        """Authenticate a user and issue a fresh token pair."""
        user = self.authenticate(login, password)
        return self.issue_token_pair(user)

    # ------------------------------------------------------------------
    # Refresh
    # ------------------------------------------------------------------
    def refresh(self, refresh_token: str) -> Token:
        """Validate a refresh token and issue a new token pair (rotation)."""
        payload = jwt_service.decode_token(refresh_token)
        jwt_service.verify_token_type(payload, "refresh")

        if payload.jti and token_crud.is_token_blacklisted(self.db, payload.jti):
            raise InvalidTokenError("This refresh token has been revoked.")

        if payload.sub is None:
            raise InvalidTokenError("Refresh token is missing its subject claim.")

        try:
            subject_uuid = uuid.UUID(payload.sub)
        except ValueError as exc:
            raise InvalidTokenError("Refresh token subject is not a valid UUID.") from exc

        user = user_crud.get_user_by_uuid(self.db, subject_uuid)
        if user is None or not user.is_active:
            raise InvalidTokenError("Refresh token no longer maps to an active user.")

        # Rotate: revoke the presented refresh token so it cannot be reused.
        if payload.jti and payload.exp:
            token_crud.blacklist_token(
                self.db,
                jti=payload.jti,
                token_type="refresh",
                expires_at=datetime.fromtimestamp(payload.exp, tz=timezone.utc),
            )

        logger.info("token_refreshed user_id=%s", user.id)
        return self.issue_token_pair(user)

    # ------------------------------------------------------------------
    # Logout
    # ------------------------------------------------------------------
    def logout(
        self,
        access_jti: str,
        access_exp: datetime,
        refresh_token: str | None = None,
    ) -> None:
        """Revoke the current access token and, if provided, its refresh token."""
        token_crud.blacklist_token(
            self.db, jti=access_jti, token_type="access", expires_at=access_exp
        )

        if refresh_token:
            try:
                payload = jwt_service.decode_token(refresh_token)
                if payload.jti and payload.exp:
                    token_crud.blacklist_token(
                        self.db,
                        jti=payload.jti,
                        token_type="refresh",
                        expires_at=datetime.fromtimestamp(payload.exp, tz=timezone.utc),
                    )
            except Exception:  # noqa: BLE001
                # A missing/invalid refresh token does not block logout of
                # the access token itself.
                pass

        logger.info("user_logged_out jti=%s", access_jti)

    # ------------------------------------------------------------------
    # Password change
    # ------------------------------------------------------------------
    def change_password(self, user: User, payload: PasswordChange) -> User:
        """Change the current user's password after verifying the old one."""
        if not password_service.verify(payload.current_password, user.hashed_password):
            logger.warning("password_change_failed reason=invalid_current user_id=%s", user.id)
            raise InvalidPasswordError("Current password is incorrect.")

        new_hash = password_service.hash(payload.new_password)
        updated_user = user_crud.update_password(self.db, user, new_hash)
        logger.info("password_changed user_id=%s", user.id)
        return updated_user
