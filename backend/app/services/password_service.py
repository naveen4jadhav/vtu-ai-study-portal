"""
Password service.

Wraps the low-level bcrypt utilities from `app.core.security` with
application-specific password policy enforcement.
"""
from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.utils.validators import validate_password_strength


class PasswordService:
    """Encapsulates password hashing, verification, and policy checks."""

    @staticmethod
    def hash(password: str) -> str:
        """Hash a plaintext password."""
        return hash_password(password)

    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        """Verify a plaintext password against a bcrypt hash."""
        return verify_password(plain_password, hashed_password)

    @staticmethod
    def enforce_policy(password: str) -> None:
        """
        Validate a password against the application's password policy.

        Raises `ValueError` if the password does not meet the policy;
        callers are expected to translate this into the appropriate
        domain exception.
        """
        validate_password_strength(password, min_length=settings.PASSWORD_MIN_LENGTH)


password_service = PasswordService()
