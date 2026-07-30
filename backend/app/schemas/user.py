"""
User-related Pydantic schemas.

Defines the request/response contracts for the authentication and
user-management API surface.
"""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.user import Role
from app.utils.validators import (
    validate_password_strength,
    validate_phone,
    validate_username,
)


class UserBase(BaseModel):
    """Fields shared across user-facing schemas."""

    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=20)
    username: str = Field(..., min_length=3, max_length=30)

    @field_validator("username")
    @classmethod
    def _validate_username(cls, value: str) -> str:
        return validate_username(value)

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        return validate_phone(value)


class UserCreate(UserBase):
    """Payload for self-service user registration."""

    password: str = Field(..., min_length=8, max_length=128)
    password_confirm: str = Field(..., min_length=8, max_length=128)
    role: Role = Field(default=Role.STUDENT)

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def _passwords_match(self) -> "UserCreate":
        if self.password != self.password_confirm:
            raise ValueError("password and password_confirm do not match.")
        return self


class UserLogin(BaseModel):
    """Payload for authenticating an existing user."""

    login: str = Field(
        ..., min_length=3, description="Registered email address or username."
    )
    password: str = Field(..., min_length=1)


class UserUpdate(BaseModel):
    """Payload for updating mutable profile fields of the current user."""

    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=20)

    @field_validator("phone")
    @classmethod
    def _validate_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        return validate_phone(value)


class UserResponse(BaseModel):
    """Public representation of a user, safe to return from the API."""

    model_config = ConfigDict(from_attributes=True)

    uuid: uuid.UUID
    full_name: str
    email: EmailStr
    phone: Optional[str]
    username: str
    role: Role
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]


class PasswordChange(BaseModel):
    """Payload for changing the current user's password."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    new_password_confirm: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _validate_new_password(cls, value: str) -> str:
        return validate_password_strength(value)

    @model_validator(mode="after")
    def _passwords_match(self) -> "PasswordChange":
        if self.new_password != self.new_password_confirm:
            raise ValueError("new_password and new_password_confirm do not match.")
        if self.new_password == self.current_password:
            raise ValueError("new_password must differ from current_password.")
        return self
