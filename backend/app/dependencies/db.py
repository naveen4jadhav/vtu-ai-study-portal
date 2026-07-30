"""Shared FastAPI dependencies related to database access."""
from app.db.session import get_db

__all__ = ["get_db"]
