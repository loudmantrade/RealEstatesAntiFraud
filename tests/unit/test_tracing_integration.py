"""
Integration tests for request tracing middleware.

Tests cover:
- Trace ID generation and propagation
- Request ID generation
- HTTP header handling
- Integration with logging
- Context cleanup
"""

import json

from fastapi.testclient import TestClient

from core.api.main import app


class TestTraceMiddleware:
    """Tests for trace context middleware."""

    def test_trace_id_generated_if_not_provided(self):
        """Test that trace ID is generated if not in request."""
        client = TestClient(app)
        response = client.get("/health")

        assert response.status_code == 200
        assert "X-Trace-ID" in response.headers
        assert "X-Request-ID" in response.headers

        trace_id = response.headers["X-Trace-ID"]
        request_id = response.headers["X-Request-ID"]

        # Should be valid UUIDs (32 char hex)
        assert len(trace_id) == 32
        assert len(request_id) == 32
        int(trace_id, 16)  # Valid hex
        int(request_id, 16)

    def test_trace_id_propagated_from_request(self):
        """Test that incoming trace ID is propagated."""
        client = TestClient(app)
        incoming_trace_id = "abc123def456"

        response = client.get("/health", headers={"x-trace-id": incoming_trace_id})

        assert response.status_code == 200
        assert response.headers["X-Trace-ID"] == incoming_trace_id

    def test_request_id_propagated_from_request(self):
        """Test that incoming request ID is propagated."""
        client = TestClient(app)
        incoming_request_id = "req123abc456"

        response = client.get("/health", headers={"x-request-id": incoming_request_id})

        assert response.status_code == 200
        assert response.headers["X-Request-ID"] == incoming_request_id

    def test_both_ids_propagated(self):
        """Test that both IDs are propagated from request."""
        client = TestClient(app)
        trace_id = "trace123"
        request_id = "req456"

        response = client.get(
            "/health", headers={"x-trace-id": trace_id, "x-request-id": request_id}
        )

        assert response.status_code == 200
        assert response.headers["X-Trace-ID"] == trace_id
        assert response.headers["X-Request-ID"] == request_id

    def test_trace_id_unique_per_request(self):
        """Test that each request gets a unique trace ID."""
        client = TestClient(app)

        response1 = client.get("/health")
        response2 = client.get("/health")

        trace_id1 = response1.headers["X-Trace-ID"]
        trace_id2 = response2.headers["X-Trace-ID"]
        request_id1 = response1.headers["X-Request-ID"]
        request_id2 = response2.headers["X-Request-ID"]

        # Different requests should have different IDs
        assert trace_id1 != trace_id2
        assert request_id1 != request_id2

    def test_trace_id_in_different_endpoints(self):
        """Test that trace IDs work across different endpoints."""
        client = TestClient(app)
        trace_id = "consistent_trace"

        # Hit health endpoint
        response1 = client.get("/health", headers={"x-trace-id": trace_id})
        assert response1.headers["X-Trace-ID"] == trace_id

        # Hit docs endpoint
        response2 = client.get("/api/v1/docs", headers={"x-trace-id": trace_id})
        # Should propagate even if endpoint doesn't exist
        assert "X-Trace-ID" in response2.headers


class TestTraceLoggingIntegration:
    """Tests for trace ID integration with logging."""

    def test_logs_contain_trace_id(self, caplog):
        """Test that logs include trace ID from context."""
        import logging

        from core.utils.context import set_trace_context
        from core.utils.logging import JSONFormatter, get_logger

        # Set up logger with JSON formatter
        logger = get_logger("test.tracing")
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger._logger.handlers = [handler]
        logger._logger.setLevel(logging.INFO)

        # Set trace context
        set_trace_context("test_trace_123", "test_request_456")

        # Capture logs
        with caplog.at_level(logging.INFO):
            logger.info("Test message with trace")

        # Check that trace IDs are in the log
        assert len(caplog.records) > 0
        record = caplog.records[0]

        # Format the record as JSON
        formatter = JSONFormatter()
        log_output = formatter.format(record)
        log_data = json.loads(log_output)

        assert log_data["trace_id"] == "test_trace_123"
        assert log_data["request_id"] == "test_request_456"
        assert log_data["message"] == "Test message with trace"

    def test_logs_without_trace_id(self, caplog):
        """Test that logs work fine without trace ID."""
        import logging

        from core.utils.context import clear_trace_context
        from core.utils.logging import JSONFormatter, get_logger

        # Clear any existing context
        clear_trace_context()

        logger = get_logger("test.no_trace")
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger._logger.handlers = [handler]
        logger._logger.setLevel(logging.INFO)

        with caplog.at_level(logging.INFO):
            logger.info("Test message without trace")

        assert len(caplog.records) > 0
        record = caplog.records[0]

        formatter = JSONFormatter()
        log_output = formatter.format(record)
        log_data = json.loads(log_output)

        # Trace IDs should not be present
        assert "trace_id" not in log_data
        assert "request_id" not in log_data
        assert log_data["message"] == "Test message without trace"


class TestContextCleanup:
    """Tests for context cleanup after requests."""

    def test_context_cleaned_up_after_request(self):
        """Test that context is cleaned up after request completes."""
        from core.utils.context import get_trace_id

        client = TestClient(app)

        # Make request
        response = client.get("/health")
        assert response.status_code == 200

        # After request, context should be cleared
        # (because middleware cleanup runs in finally block)
        assert get_trace_id() is None

    def test_context_cleaned_up_on_error(self):
        """Test that context is cleaned up even if request fails."""
        from core.utils.context import get_trace_id

        client = TestClient(app)

        # Request non-existent endpoint
        response = client.get("/nonexistent")
        assert response.status_code == 404

        # Context should still be cleared
        assert get_trace_id() is None


class TestEndToEnd:
    """End-to-end tests for request tracing."""

    def test_full_request_trace_lifecycle(self):
        """Test complete request tracing lifecycle."""
        client = TestClient(app)

        # 1. Request without trace ID
        response = client.get("/health")

        # Should generate IDs
        trace_id = response.headers["X-Trace-ID"]
        request_id = response.headers["X-Request-ID"]
        assert trace_id is not None
        assert request_id is not None

        # 2. Request with existing trace ID (simulating distributed trace)
        existing_trace = "distributed_trace_789"
        response2 = client.get("/health", headers={"x-trace-id": existing_trace})

        # Should preserve trace ID but generate new request ID
        assert response2.headers["X-Trace-ID"] == existing_trace
        assert response2.headers["X-Request-ID"] != request_id

        # 3. Multiple sequential requests should have different IDs
        response3 = client.get("/health")
        response4 = client.get("/health")

        assert response3.headers["X-Trace-ID"] != response4.headers["X-Trace-ID"]
        assert response3.headers["X-Request-ID"] != response4.headers["X-Request-ID"]
