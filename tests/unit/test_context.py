"""
Unit tests for request context management and tracing.

Tests cover:
- Context variable management
- Trace and request ID generation
- Context propagation
- Context cleanup
"""

import uuid

import pytest

from core.utils.context import (
    clear_trace_context,
    generate_request_id,
    generate_trace_id,
    get_request_id,
    get_trace_context,
    get_trace_id,
    set_request_id,
    set_trace_context,
    set_trace_id,
)


class TestIDGeneration:
    """Tests for ID generation functions."""

    def test_generate_trace_id_format(self):
        """Test that trace ID is valid UUID hex."""
        trace_id = generate_trace_id()

        assert isinstance(trace_id, str)
        assert len(trace_id) == 32  # UUID4 hex without hyphens
        # Should be valid hex
        int(trace_id, 16)

    def test_generate_request_id_format(self):
        """Test that request ID is valid UUID hex."""
        request_id = generate_request_id()

        assert isinstance(request_id, str)
        assert len(request_id) == 32
        int(request_id, 16)

    def test_generate_ids_are_unique(self):
        """Test that generated IDs are unique."""
        trace_ids = {generate_trace_id() for _ in range(100)}
        request_ids = {generate_request_id() for _ in range(100)}

        assert len(trace_ids) == 100
        assert len(request_ids) == 100


class TestContextGettersSetters:
    """Tests for context getters and setters."""

    def teardown_method(self):
        """Clean up context after each test."""
        clear_trace_context()

    def test_get_trace_id_when_not_set(self):
        """Test getting trace ID when not set returns None."""
        assert get_trace_id() is None

    def test_get_request_id_when_not_set(self):
        """Test getting request ID when not set returns None."""
        assert get_request_id() is None

    def test_set_and_get_trace_id(self):
        """Test setting and getting trace ID."""
        test_id = "abc123"
        set_trace_id(test_id)

        assert get_trace_id() == test_id

    def test_set_and_get_request_id(self):
        """Test setting and getting request ID."""
        test_id = "req456"
        set_request_id(test_id)

        assert get_request_id() == test_id

    def test_set_trace_context_with_ids(self):
        """Test setting both IDs via set_trace_context."""
        trace_id = "trace123"
        request_id = "req456"

        returned_trace, returned_request = set_trace_context(trace_id, request_id)

        assert returned_trace == trace_id
        assert returned_request == request_id
        assert get_trace_id() == trace_id
        assert get_request_id() == request_id

    def test_set_trace_context_generates_ids(self):
        """Test that set_trace_context generates IDs if not provided."""
        trace_id, request_id = set_trace_context()

        assert trace_id is not None
        assert request_id is not None
        assert len(trace_id) == 32
        assert len(request_id) == 32
        assert get_trace_id() == trace_id
        assert get_request_id() == request_id

    def test_set_trace_context_partial(self):
        """Test setting only one ID via set_trace_context."""
        # Only trace_id
        trace_id, request_id = set_trace_context(trace_id="custom_trace")
        assert trace_id == "custom_trace"
        assert request_id is not None
        assert len(request_id) == 32

        clear_trace_context()

        # Only request_id
        trace_id, request_id = set_trace_context(request_id="custom_request")
        assert request_id == "custom_request"
        assert trace_id is not None
        assert len(trace_id) == 32

    def test_get_trace_context(self):
        """Test getting all context as dictionary."""
        set_trace_context("trace123", "req456")

        context = get_trace_context()

        assert context == {"trace_id": "trace123", "request_id": "req456"}

    def test_get_trace_context_when_empty(self):
        """Test getting context when nothing is set."""
        context = get_trace_context()

        assert context == {"trace_id": None, "request_id": None}


class TestContextCleanup:
    """Tests for context cleanup."""

    def test_clear_trace_context(self):
        """Test that clear_trace_context removes all IDs."""
        set_trace_context("trace123", "req456")

        clear_trace_context()

        assert get_trace_id() is None
        assert get_request_id() is None

    def test_clear_trace_context_idempotent(self):
        """Test that clearing multiple times is safe."""
        set_trace_context()
        clear_trace_context()
        clear_trace_context()

        assert get_trace_id() is None
        assert get_request_id() is None


class TestContextIsolation:
    """Tests for context isolation between different contexts."""

    def teardown_method(self):
        """Clean up after tests."""
        clear_trace_context()

    def test_context_isolation(self):
        """Test that context variables are isolated."""
        # Set context
        set_trace_context("trace1", "req1")
        assert get_trace_id() == "trace1"

        # Change context
        set_trace_context("trace2", "req2")
        assert get_trace_id() == "trace2"
        assert get_request_id() == "req2"

    def test_overwrite_ids(self):
        """Test that setting new IDs overwrites old ones."""
        set_trace_id("old_trace")
        set_request_id("old_request")

        set_trace_id("new_trace")
        set_request_id("new_request")

        assert get_trace_id() == "new_trace"
        assert get_request_id() == "new_request"


class TestIntegration:
    """Integration tests for context management."""

    def teardown_method(self):
        """Clean up after tests."""
        clear_trace_context()

    def test_full_lifecycle(self):
        """Test complete lifecycle of trace context."""
        # Start with clean context
        assert get_trace_id() is None
        assert get_request_id() is None

        # Set context (simulating middleware)
        trace_id, request_id = set_trace_context()
        assert trace_id is not None
        assert request_id is not None

        # Use context (simulating request handling)
        context = get_trace_context()
        assert context["trace_id"] == trace_id
        assert context["request_id"] == request_id

        # Clean up (simulating request completion)
        clear_trace_context()
        assert get_trace_id() is None
        assert get_request_id() is None

    def test_context_propagation_scenario(self):
        """Test realistic scenario of context propagation."""
        # Incoming request with trace ID
        incoming_trace_id = "external-trace-123"

        # Set context with incoming trace ID
        trace_id, request_id = set_trace_context(trace_id=incoming_trace_id)

        # Trace ID should be preserved
        assert trace_id == incoming_trace_id
        # Request ID should be generated
        assert request_id is not None
        assert len(request_id) == 32

        # Context available throughout request
        assert get_trace_id() == incoming_trace_id
        assert get_request_id() == request_id

        # Cleanup
        clear_trace_context()
