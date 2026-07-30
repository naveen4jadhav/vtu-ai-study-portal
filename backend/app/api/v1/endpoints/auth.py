"""Authentication and current-user API endpoints."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTokenError
from app.db.session import get_db
from app.dependencies.auth import get_current_active_user, get_current_token_payload
from app.models.user import User
from app.schemas.token import Token, TokenPayload, TokenRefresh
from app.schemas.user import PasswordChange, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthenticationService

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    """Create a new user account with the STUDENT role."""
    service = AuthenticationService(db)
    return service.register(user_in)


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate and obtain an access/refresh token pair",
)
def login(credentials: UserLogin, db: Session = Depends(get_db)) -> Token:
    """Authenticate with an email/username and password."""
    service = AuthenticationService(db)
    return service.login(credentials.login, credentials.password)


@router.post(
    "/refresh",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Exchange a refresh token for a new token pair",
)
def refresh(payload: TokenRefresh, db: Session = Depends(get_db)) -> Token:
    """Rotate a valid refresh token for a new access/refresh token pair."""
    service = AuthenticationService(db)
    return service.refresh(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke the current access token (and refresh token, if supplied)",
)
def logout(
    payload: TokenRefresh | None = None,
    token_payload: TokenPayload = Depends(get_current_token_payload),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Revoke the presented access token, optionally also its refresh token."""
    if not token_payload.jti or not token_payload.exp:
        raise InvalidTokenError("Access token is missing required claims.")

    service = AuthenticationService(db)
    access_exp = datetime.fromtimestamp(token_payload.exp, tz=timezone.utc)
    service.logout(
        access_jti=token_payload.jti,
        access_exp=access_exp,
        refresh_token=payload.refresh_token if payload else None,
    )
    return {"message": "Successfully logged out."}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the current authenticated user's profile",
)
def read_current_user(current_user: User = Depends(get_current_active_user)) -> User:
    """Return the profile of the currently authenticated user."""
    return current_user


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change the current user's password",
)
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Change the authenticated user's password."""
    service = AuthenticationService(db)
    service.change_password(current_user, payload)
    return {"message": "Password changed successfully."}
