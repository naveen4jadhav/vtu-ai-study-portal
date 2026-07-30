"""
Shared pytest fixtures for Module 2 tests.

Auth/user tests are integration tests that run against a real
PostgreSQL instance (the same one configured via `.env` /
`DATABASE_URL`), matching the project's production stack. Each test
runs inside a database transaction that is rolled back afterwards,
so tests never leave residual data behind.

Start a database before running these tests, e.g.:
    docker compose up -d db
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import engine, get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    """Create all tables once for the test session, then drop them."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session() -> Session:
    """
    Provide a session bound to a single connection/transaction.

    Uses SQLAlchemy 2.0's savepoint-joining mode so that `commit()`
    calls made by application code do not end the outer transaction,
    allowing a full rollback after each test for isolation.
    """
    connection = engine.connect()
    outer_transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        bind=connection,
        autocommit=False,
        autoflush=False,
        join_transaction_mode="create_savepoint",
    )
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """Provide a TestClient with `get_db` overridden to the test session."""

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
