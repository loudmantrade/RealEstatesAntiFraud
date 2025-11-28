"""Pytest fixtures for integration tests.

This module provides fixtures for integration testing with real PostgreSQL database.
Fixtures include database engine, session management, and test client setup.
"""

import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.api.main import app
from core.database import Base, get_db


@pytest.fixture(scope="session")
def test_config() -> dict:
    """Load test configuration from .env.test file or environment variables.

    For CI/CD environments, configuration can be provided via environment variables.
    For local development, loads from .env.test file.

    Returns:
        dict: Configuration dictionary with DATABASE_URL and other settings.
    """
    # Load .env.test file if exists (for local development)
    load_dotenv(".env.test", override=False)

    # Build database URL from individual components or use full URL
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5433")
    db_name = os.getenv("DB_NAME", "realestate_test")
    db_user = os.getenv("DB_USER", "test_user")
    db_password = os.getenv("DB_PASSWORD", "test_pass")

    # Use DATABASE_URL if provided, otherwise construct from components
    database_url = os.getenv(
        "DATABASE_URL",
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
    )

    config = {
        "database_url": database_url,
        "api_host": os.getenv("API_HOST", "0.0.0.0"),
        "api_port": int(os.getenv("API_PORT", "8001")),
        "log_level": os.getenv("LOG_LEVEL", "DEBUG"),
        "testing": os.getenv("TESTING", "true").lower() == "true",
    }

    return config


@pytest.fixture(scope="session")
def engine(test_config: dict):
    """Create database engine for the test session.

    Creates all tables at the start of the test session and drops them at the end.
    Uses session scope for efficiency - tables are created once per test run.

    Args:
        test_config: Test configuration dictionary.

    Yields:
        Engine: SQLAlchemy engine instance.
    """
    engine = create_engine(
        test_config["database_url"],
        pool_pre_ping=True,  # Verify connections before using
        echo=False,  # Set to True for SQL query logging
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after all tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine) -> Generator[Session, None, None]:
    """Create a new database session for each test function.

    Uses transaction rollback to ensure test isolation - each test gets
    a clean database state. Changes made during the test are rolled back.

    Args:
        engine: SQLAlchemy engine from session fixture.

    Yields:
        Session: SQLAlchemy session instance.
    """
    # Create a new connection
    connection = engine.connect()

    # Begin a transaction
    transaction = connection.begin()

    # Create a session bound to the connection
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    # Rollback the transaction (undo all changes)
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create FastAPI test client with database session override.

    Overrides the get_db dependency to use the test database session.
    This ensures all API calls during tests use the same transactional session.

    Args:
        db_session: Test database session.

    Yields:
        TestClient: FastAPI test client instance.
    """

    def override_get_db():
        """Override get_db dependency to use test session."""
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture

    # Override the dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Clear dependency overrides
    app.dependency_overrides.clear()
