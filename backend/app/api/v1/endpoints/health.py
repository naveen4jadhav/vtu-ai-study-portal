"""Health check endpoint used by load balancers and orchestrators."""
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter()


@router.get("", status_code=status.HTTP_200_OK, summary="Liveness/health check")
def health_check() -> dict[str, str]:
    """Return a simple liveness signal for the API process."""
    return {"status": "healthy"}


@router.get(
    "/db",
    status_code=status.HTTP_200_OK,
    summary="Database connectivity health check",
)
def health_check_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """Verify the API can reach and query the database."""
    db.execute(text("SELECT 1"))
    return {"status": "healthy", "database": "connected"}
