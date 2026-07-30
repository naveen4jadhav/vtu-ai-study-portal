"""
Application-level domain exceptions.

These exceptions decouple business/service logic from HTTP concerns.
Services and CRUD code raise these; `register_exception_handlers`
translates them into consistent JSON error responses.
"""
from fastapi import status


class AppException(Exception):
    """Base class for all domain-level application exceptions."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "app_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DuplicateEmailError(AppException):
    """Raised when attempting to register/update with an email already in use."""

    status_code = status.HTTP_409_CONFLICT
    code = "duplicate_email"


class DuplicateUsernameError(AppException):
    """Raised when attempting to register/update with a username already in use."""

    status_code = status.HTTP_409_CONFLICT
    code = "duplicate_username"


class InvalidCredentialsError(AppException):
    """Raised when login credentials (username/email + password) do not match."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "invalid_credentials"


class InvalidPasswordError(AppException):
    """Raised when the supplied current password does not match, or fails policy."""

    status_code = status.HTTP_400_BAD_REQUEST
    code = "invalid_password"


class InvalidTokenError(AppException):
    """Raised when a JWT token is malformed, has an invalid signature, or wrong type."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "invalid_token"


class ExpiredTokenError(AppException):
    """Raised when a JWT token has expired."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "expired_token"


class UnauthorizedError(AppException):
    """Raised when a request lacks valid authentication credentials."""

    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"


class ForbiddenError(AppException):
    """Raised when an authenticated user lacks permission for the action."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"


class UserNotFoundError(AppException):
    """Raised when a referenced user does not exist."""

    status_code = status.HTTP_404_NOT_FOUND
    code = "user_not_found"


class InactiveUserError(AppException):
    """Raised when an action is attempted against a deactivated user account."""

    status_code = status.HTTP_403_FORBIDDEN
    code = "inactive_user"
