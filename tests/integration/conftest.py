"""Pytest fixtures for integration tests.

This module provides fixtures for integration testing with real PostgreSQL database,
Redis instance, and plugin system. Fixtures include database engine, session management,
Redis client, test client setup, and plugin testing utilities.
"""

import os
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.api.main import app
from core.database import Base, get_db
from core.models.events import Topics
from core.pipeline.orchestrator import ProcessingOrchestrator
from core.plugin_manager import PluginManager
from core.queue.in_memory_queue import InMemoryQueuePlugin
from tests.integration.plugin_utils import PluginTestHelper


@pytest.fixture(scope="session")
def test_config() -> dict:
    """Load test configuration from .env.test file or environment variables.

    For CI/CD environments, configuration can be provided via environment variables.
    For local development, loads from .env.test file.

    Returns:
        dict: Configuration dictionary with DATABASE_URL and other settings.
    """
    # Priority: CI environment variables > individual DB_* vars > .env.test file
    # First check if individual DB components are provided (CI pattern)
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    # If individual components are provided, use them (CI mode)
    if db_host and db_port and db_name and db_user and db_password:
        database_url = (
            f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
    else:
        # Otherwise load from .env.test (local development)
        load_dotenv(".env.test", override=False)
        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://test_user:test_pass@localhost:5433/realestate_test",
        )

    # Redis configuration
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6380"))  # 6380 for local, 6379 for CI
    redis_db = int(os.getenv("REDIS_DB", "0"))

    config = {
        "database_url": database_url,
        "redis_url": f"redis://{redis_host}:{redis_port}/{redis_db}",
        "redis_host": redis_host,
        "redis_port": redis_port,
        "redis_db": redis_db,
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


@pytest.fixture(scope="function")
async def redis_client(test_config: dict) -> AsyncGenerator[redis.Redis, None]:
    """Create Redis client for each test.

    Provides a Redis client instance for integration testing.
    Automatically closes the connection after test completes.

    Args:
        test_config: Test configuration dictionary with Redis connection details.

    Yields:
        redis.Redis: Async Redis client instance.
    """
    client = await redis.from_url(
        test_config["redis_url"],
        encoding="utf-8",
        decode_responses=True,
        max_connections=10,
    )

    # Verify connection
    try:
        await client.ping()
    except Exception as e:
        await client.aclose()
        raise RuntimeError(
            f"Failed to connect to Redis at {test_config['redis_url']}: {e}"
        )

    yield client

    # Cleanup: close connection
    await client.aclose()


@pytest.fixture
async def redis_clean(redis_client: redis.Redis) -> AsyncGenerator[redis.Redis, None]:
    """Provide clean Redis instance for each test function.

    Flushes the Redis database before and after each test to ensure isolation.
    Use this fixture when tests need a clean Redis state.

    Args:
        redis_client: Redis client fixture.

    Yields:
        redis.Redis: Redis client with clean database.
    """
    # Clean before test
    await redis_client.flushdb()

    yield redis_client

    # Clean after test
    await redis_client.flushdb()


# ============================================================================
# Plugin Testing Fixtures
# ============================================================================


@pytest.fixture
def plugin_test_helper(tmp_path: Path) -> Generator[PluginTestHelper, None, None]:
    """Provide PluginTestHelper for plugin testing.

    Creates a temporary directory for test plugins and provides helper
    methods for managing plugin fixtures. Automatically cleans up after tests.

    Args:
        tmp_path: pytest temporary directory fixture.

    Yields:
        PluginTestHelper: Helper instance for plugin testing.
    """
    helper = PluginTestHelper(tmp_path)
    yield helper
    helper.cleanup()


@pytest.fixture
def plugin_fixtures_dir() -> Path:
    """Get path to plugin fixtures directory.

    Returns:
        Path: Path to tests/fixtures/plugins/ directory.
    """
    return Path(__file__).parent.parent / "fixtures" / "plugins"


@pytest.fixture
def sample_plugins(plugin_test_helper: PluginTestHelper) -> dict[str, Path]:
    """Copy sample plugin fixtures for testing.

    Creates copies of test plugins in the temporary test directory.
    Provides paths to commonly used test plugins.

    Args:
        plugin_test_helper: PluginTestHelper fixture.

    Returns:
        dict: Dictionary mapping plugin names to their paths.
    """
    return {
        "processing": plugin_test_helper.copy_plugin_fixture("test_processing_plugin"),
        "detection": plugin_test_helper.copy_plugin_fixture("test_detection_plugin"),
        "dependent": plugin_test_helper.copy_plugin_fixture("test_dependent_plugin"),
        "source": plugin_test_helper.copy_plugin_fixture("test_source_plugin"),
    }


@pytest.fixture
async def plugin_manager_with_fixtures(
    sample_plugins: dict[str, Path],
    tmp_path: Path,
) -> AsyncGenerator[PluginManager, None]:
    """Create PluginManager with sample plugin fixtures.

    Initializes a PluginManager instance with paths to test plugins.
    Automatically discovers and loads plugins. Cleans up after tests.

    Args:
        sample_plugins: Sample plugin paths fixture.
        tmp_path: pytest temporary directory fixture.

    Yields:
        PluginManager: Initialized plugin manager with test plugins.
    """
    # Create plugin directories list
    plugin_dirs = list(sample_plugins.values())

    # Initialize plugin manager
    manager = PluginManager(plugin_dirs=plugin_dirs)

    # Discover and load plugins
    await manager.discover_plugins()

    yield manager

    # Cleanup
    await manager.shutdown_all()


@pytest.fixture
async def orchestrator_with_real_plugins(
    plugin_fixtures_dir: Path,
) -> AsyncGenerator[ProcessingOrchestrator, None]:
    """Create ProcessingOrchestrator with real test processing plugin loaded and enabled.

    Initializes a PluginManager with test plugins, enables the processing plugin,
    creates an in-memory queue, and creates a ProcessingOrchestrator instance.
    This fixture is designed to test real plugin execution paths including plugin
    loading, priority ordering, timing measurement, and statistics tracking.

    Args:
        plugin_fixtures_dir: Path to plugin fixtures directory.

    Yields:
        ProcessingOrchestrator: Initialized orchestrator with real plugins ready for execution.
    """
    # Create in-memory queue for testing
    queue = InMemoryQueuePlugin()
    queue.connect()
    queue.create_topic(Topics.RAW_LISTINGS)
    queue.create_topic(Topics.PROCESSED_LISTINGS)
    queue.create_topic(Topics.PROCESSING_FAILED)

    # Create plugin manager
    manager = PluginManager()

    # Load processing plugin for testing
    processing_plugin_manifest = plugin_fixtures_dir / "test_processing_plugin" / "plugin.yaml"
    loaded, _ = manager.load_plugins(manifest_paths=[processing_plugin_manifest])
    
    # Enable the loaded plugin (synchronous method)
    if loaded:
        manager.enable("plugin-processing-test")

    # Create orchestrator with manager
    orchestrator = ProcessingOrchestrator(
        plugin_manager=manager,
        queue=queue,
    )

    # Start orchestrator (synchronous method)
    orchestrator.start()

    yield orchestrator

    # Cleanup (synchronous methods)
    orchestrator.stop()
    queue.disconnect()
