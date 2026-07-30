"""
Reusable field validation helpers.

Email validation is delegated to Pydantic's `EmailStr` (backed by the
`email-validator` package). These helpers cover the fields Pydantic
does not validate out of the box: username, password strength, and
phone number.
"""
import re

USERNAME_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.]{2,29}$")
PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")

PASSWORD_UPPERCASE_PATTERN = re.compile(r"[A-Z]")
PASSWORD_LOWERCASE_PATTERN = re.compile(r"[a-z]")
PASSWORD_DIGIT_PATTERN = re.compile(r"\d")
PASSWORD_SPECIAL_PATTERN = re.compile(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]")


def validate_username(username: str) -> str:
    """
    Validate a username.

    Must start with a letter, be 3-30 characters, and contain only
    letters, digits, underscores, and periods.
    """
    if not USERNAME_PATTERN.match(username):
        raise ValueError(
            "Username must be 3-30 characters, start with a letter, and "
            "contain only letters, digits, underscores, or periods."
        )
    return username


def validate_phone(phone: str) -> str:
    """Validate a phone number in a loose E.164-compatible format."""
    if not PHONE_PATTERN.match(phone):
        raise ValueError(
            "Phone number must contain 8-15 digits and may include a "
            "leading '+' country code prefix."
        )
    return phone


def validate_password_strength(password: str, min_length: int = 8) -> str:
    """
    Enforce the application password policy.

    Requires a minimum length plus at least one uppercase letter, one
    lowercase letter, one digit, and one special character.
    """
    if len(password) < min_length:
        raise ValueError(f"Password must be at least {min_length} characters long.")
    if not PASSWORD_UPPERCASE_PATTERN.search(password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not PASSWORD_LOWERCASE_PATTERN.search(password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not PASSWORD_DIGIT_PATTERN.search(password):
        raise ValueError("Password must contain at least one digit.")
    if not PASSWORD_SPECIAL_PATTERN.search(password):
        raise ValueError("Password must contain at least one special character.")
    return password
