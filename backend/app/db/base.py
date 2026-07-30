"""
SQLAlchemy declarative base.

All ORM models must inherit from `Base` so that Alembic autogenerate
and metadata creation can discover them.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass
