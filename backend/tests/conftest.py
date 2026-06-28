import pytest
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def _bypass_admin_auth():
    """Existing admin tests hit /admin/* without a real Better Auth JWT — treat them as
    admin. The auth dependency itself is exercised in test_admin_auth.py."""
    app.dependency_overrides[require_admin] = lambda: {"role": "admin", "id": "test"}
    yield
    app.dependency_overrides.pop(require_admin, None)


@pytest.fixture
def db_session():
    """A session wrapped in a transaction that is rolled back after each test.

    `create_savepoint` makes the endpoint's own commits roll back too, so HTTP tests
    that POST (e.g. /auth/signup) stay isolated."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
