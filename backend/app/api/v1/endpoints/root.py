"""
Root and version metadata endpoints.
"""

from fastapi import APIRouter, status

from app.core.config import settings

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    summary="Root endpoint",
)
def read_root() -> dict[str, str]:
    """
    Return basic project identification metadata.
    """
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


@router.get(
    "/version",
    status_code=status.HTTP_200_OK,
    summary="Version information",
)
def read_version() -> dict[str, str]:
    """
    Return API version and current environment.
    """
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }