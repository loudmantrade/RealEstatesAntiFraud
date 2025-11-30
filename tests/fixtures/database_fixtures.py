"""
Database Session Fixtures.

Provides pytest fixtures for database session management in tests.
Supports both SQLite (default, in-memory) and PostgreSQL (via environment variable).

Features:
- Automatic session creation and cleanup
- Transaction isolation between tests
- Configurable via TEST_DATABASE_URL
- Thread-safe configuration

Usage:
    def test_database_operations(db_session, listing_factory):
        listing = listing_factory.create_listing()
        db_session.add(listing)
        db_session.commit()

        result = db_session.query(ListingModel).first()
        assert result is not None
"""

import os

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from core.database.base import Base


@pytest.fixture(scope="session")
def test_database_url():
    """Get test database URL from environment or use SQLite in-memory.

    Override with environment variable:
        export TEST_DATABASE_URL="postgresql://user:pass@localhost/test_db"

    Returns:
        str: Database URL for tests
    """
    return os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")


@pytest.fixture(scope="session")
def test_engine(test_database_url):
    """Create test database engine.

    Creates engine once per test session. For SQLite, enables foreign keys
    and uses check_same_thread=False for multi-threaded tests.

    Args:
        test_database_url: Database URL from test_database_url fixture

    Returns:
        sqlalchemy.engine.Engine: Database engine

    Yields:
        Engine instance that is disposed after all tests complete
    """
    # SQLite-specific configuration
    connect_args = {}
    if "sqlite" in test_database_url:
        connect_args = {"check_same_thread": False}

    engine = create_engine(
        test_database_url,
        echo=False,  # Set to True for SQL debugging
        connect_args=connect_args,
    )

    # Enable foreign keys for SQLite
    if "sqlite" in test_database_url:

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine

    # Cleanup
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create isolated database session for each test.

    Uses nested transaction with rollback to ensure test isolation.
    Each test gets a fresh session, and all changes are rolled back
    after the test completes.

    Args:
        test_engine: Database engine from test_engine fixture

    Returns:
        sqlalchemy.orm.Session: Database session

    Yields:
        Session instance with automatic rollback after test

    Example:
        def test_create_listing(db_session, listing_factory):
            listing = listing_factory.create_listing()
            db_session.add(listing)
            db_session.commit()

            # Query in same session
            result = db_session.query(ListingModel).first()
            assert result.listing_id == listing.listing_id

            # Automatic rollback - next test starts clean
    """
    # Create connection and begin transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create session bound to this connection
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
    )
    session = TestingSessionLocal()

    yield session

    # Cleanup: close session and rollback transaction
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def clean_db(db_session):
    """Provide clean database session with explicit table truncation.

    Truncates all tables before yielding session. Use when you need
    guaranteed empty database state, though db_session already provides
    isolation via transaction rollback.

    Args:
        db_session: Database session from db_session fixture

    Returns:
        sqlalchemy.orm.Session: Clean database session

    Yields:
        Session with all tables truncated

    Example:
        def test_fresh_database(clean_db, listing_factory):
            # Guaranteed zero records in all tables
            count = clean_db.query(ListingModel).count()
            assert count == 0

            # Add test data
            listings = listing_factory.create_batch(5)
            clean_db.add_all(listings)
            clean_db.commit()
    """
    # Truncate all tables in reverse dependency order
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()

    yield db_session


@pytest.fixture
def db_session_factory(test_engine):
    """Factory for creating multiple database sessions.

    Use when you need to simulate multiple concurrent database connections
    or test transaction isolation between sessions.

    Args:
        test_engine: Database engine from test_engine fixture

    Returns:
        callable: Function that creates new session instances

    Example:
        def test_concurrent_sessions(db_session_factory, listing_factory):
            session1 = db_session_factory()
            session2 = db_session_factory()

            # Different sessions see different uncommitted data
            listing = listing_factory.create_listing()
            session1.add(listing)
            session1.flush()

            # session2 doesn't see uncommitted changes
            count = session2.query(ListingModel).count()
            assert count == 0

            session1.close()
            session2.close()
    """
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    def _create_session() -> Session:
        return TestingSessionLocal()

    return _create_session
