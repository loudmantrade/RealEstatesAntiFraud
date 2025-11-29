"""
Unit tests for database base module.

Tests database session dependency injection and lifecycle.
"""

from unittest.mock import MagicMock, patch

import pytest

from core.database.base import Base, get_db


class TestBase:
    """Test SQLAlchemy Base."""

    def test_declarative_base_exists(self):
        """Test that Base is a valid SQLAlchemy declarative base."""
        assert Base is not None
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


class TestGetDb:
    """Test get_db dependency injection function."""

    def test_get_db_yields_session(self):
        """Test get_db yields a database session."""
        mock_session = MagicMock()

        with patch("core.database.session.SessionLocal", return_value=mock_session):
            # Get the generator
            db_generator = get_db()

            # Get the yielded session
            session = next(db_generator)

            assert session is mock_session
            mock_session.close.assert_not_called()

    def test_get_db_closes_session_on_exit(self):
        """Test get_db closes session after yield."""
        mock_session = MagicMock()

        with patch("core.database.session.SessionLocal", return_value=mock_session):
            db_generator = get_db()

            # Consume the generator
            session = next(db_generator)
            assert session is mock_session

            # Trigger finally block
            try:
                next(db_generator)
            except StopIteration:
                pass

            # Verify session was closed
            mock_session.close.assert_called_once()

    def test_get_db_closes_session_on_exception(self):
        """Test get_db closes session even when exception occurs."""
        mock_session = MagicMock()

        with patch("core.database.session.SessionLocal", return_value=mock_session):
            db_generator = get_db()
            session = next(db_generator)

            # Simulate exception in request handling
            try:
                db_generator.throw(RuntimeError("Simulated error"))
            except RuntimeError:
                pass

            # Session should still be closed
            mock_session.close.assert_called_once()

    def test_get_db_creates_new_session_each_call(self):
        """Test get_db creates a new session for each call."""
        mock_session_1 = MagicMock()
        mock_session_2 = MagicMock()

        with patch(
            "core.database.session.SessionLocal",
            side_effect=[mock_session_1, mock_session_2],
        ):
            # First call
            db_gen_1 = get_db()
            session_1 = next(db_gen_1)

            # Second call
            db_gen_2 = get_db()
            session_2 = next(db_gen_2)

            # Should be different sessions
            assert session_1 is not session_2
            assert session_1 is mock_session_1
            assert session_2 is mock_session_2

    def test_get_db_as_context_manager(self):
        """Test using get_db in a context-like pattern."""
        mock_session = MagicMock()

        with patch("core.database.session.SessionLocal", return_value=mock_session):
            db_generator = get_db()

            # Simulate FastAPI dependency injection pattern
            try:
                session = next(db_generator)
                # Use session (simulated request processing)
                assert session is mock_session
            finally:
                # Cleanup (FastAPI does this automatically)
                try:
                    next(db_generator)
                except StopIteration:
                    pass

            mock_session.close.assert_called_once()

    def test_get_db_generator_protocol(self):
        """Test get_db follows generator protocol correctly."""
        mock_session = MagicMock()

        with patch("core.database.session.SessionLocal", return_value=mock_session):
            db_generator = get_db()

            # Verify it's a generator
            assert hasattr(db_generator, "__next__")
            assert hasattr(db_generator, "send")
            assert hasattr(db_generator, "throw")
            assert hasattr(db_generator, "close")
