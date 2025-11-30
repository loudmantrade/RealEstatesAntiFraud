"""
Unit tests for structured logging module.

Tests cover:
- JSON formatter output format
- All log levels
- Context field injection
- Configuration changes
- Exception logging
"""

import json
import logging
import os
from io import StringIO
from typing import Any, Dict

import pytest

from core.utils.logging import (
    JSONFormatter,
    StructuredLogger,
    configure_logging,
    get_logger,
)


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def test_json_formatter_basic_output(self):
        """Test that formatter produces valid JSON."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)

        # Should be valid JSON
        log_data = json.loads(output)

        # Check standard fields
        assert "timestamp" in log_data
        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Test message"
        assert log_data["logger"] == "test.logger"
        assert log_data["module"] == "path"
        assert log_data["function"] is None  # funcName is None when not set
        assert log_data["line"] == 42

    def test_json_formatter_with_context(self):
        """Test that extra fields are included in context."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Add extra fields
        record.user_id = 123
        record.request_id = "abc-123"
        record.action = "login"

        output = formatter.format(record)
        log_data = json.loads(output)

        # Check context fields
        assert "context" in log_data
        assert log_data["context"]["user_id"] == 123
        assert log_data["context"]["request_id"] == "abc-123"
        assert log_data["context"]["action"] == "login"

    def test_json_formatter_with_exception(self):
        """Test that exceptions are properly formatted."""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            exc_info = sys.exc_info()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="/test/path.py",
            lineno=42,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        # Check exception field
        assert "exception" in log_data
        assert "ValueError: Test error" in log_data["exception"]
        assert "Traceback" in log_data["exception"]

    def test_json_formatter_timestamp_format(self):
        """Test that timestamp is in ISO8601 format."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/path.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        log_data = json.loads(output)

        # Check timestamp format (ISO8601 with timezone)
        timestamp = log_data["timestamp"]
        assert "T" in timestamp  # Date-time separator
        assert "Z" in timestamp or "+" in timestamp  # Timezone indicator


class TestStructuredLogger:
    """Tests for StructuredLogger class."""

    @pytest.fixture
    def logger_with_handler(self) -> tuple[StructuredLogger, StringIO]:
        """Create a logger with string handler for testing."""
        # Create string IO handler
        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(JSONFormatter())

        # Create Python logger
        python_logger = logging.getLogger(f"test.{id(self)}")
        python_logger.handlers.clear()
        python_logger.addHandler(handler)
        python_logger.setLevel(logging.DEBUG)

        # Create structured logger
        structured_logger = StructuredLogger(python_logger)

        return structured_logger, string_io

    def test_debug_level(self, logger_with_handler):
        """Test debug level logging."""
        logger, string_io = logger_with_handler

        logger.debug("Debug message", context={"detail": "test"})

        output = string_io.getvalue()
        log_data = json.loads(output)

        assert log_data["level"] == "DEBUG"
        assert log_data["message"] == "Debug message"
        assert log_data["context"]["detail"] == "test"

    def test_info_level(self, logger_with_handler):
        """Test info level logging."""
        logger, string_io = logger_with_handler

        logger.info("Info message", context={"user_id": 123})

        output = string_io.getvalue()
        log_data = json.loads(output)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Info message"
        assert log_data["context"]["user_id"] == 123

    def test_warning_level(self, logger_with_handler):
        """Test warning level logging."""
        logger, string_io = logger_with_handler

        logger.warning("Warning message")

        output = string_io.getvalue()
        log_data = json.loads(output)

        assert log_data["level"] == "WARNING"
        assert log_data["message"] == "Warning message"

    def test_error_level(self, logger_with_handler):
        """Test error level logging."""
        logger, string_io = logger_with_handler

        logger.error("Error message", context={"error_code": 500})

        output = string_io.getvalue()
        log_data = json.loads(output)

        assert log_data["level"] == "ERROR"
        assert log_data["message"] == "Error message"
        assert log_data["context"]["error_code"] == 500

    def test_critical_level(self, logger_with_handler):
        """Test critical level logging."""
        logger, string_io = logger_with_handler

        logger.critical("Critical message")

        output = string_io.getvalue()
        log_data = json.loads(output)

        assert log_data["level"] == "CRITICAL"
        assert log_data["message"] == "Critical message"

    def test_exception_logging(self, logger_with_handler):
        """Test exception logging with traceback."""
        logger, string_io = logger_with_handler

        try:
            raise ValueError("Test error")
        except ValueError:
            logger.exception("Exception occurred", context={"operation": "test"})

        output = string_io.getvalue()
        log_data = json.loads(output)

        assert log_data["level"] == "ERROR"
        assert log_data["message"] == "Exception occurred"
        assert log_data["context"]["operation"] == "test"
        assert "exception" in log_data
        assert "ValueError: Test error" in log_data["exception"]

    def test_context_with_kwargs(self, logger_with_handler):
        """Test that kwargs are merged with context."""
        logger, string_io = logger_with_handler

        logger.info("Message", context={"field1": "value1"}, field2="value2", field3=123)

        output = string_io.getvalue()
        log_data = json.loads(output)

        assert log_data["context"]["field1"] == "value1"
        assert log_data["context"]["field2"] == "value2"
        assert log_data["context"]["field3"] == 123


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_with_explicit_params(self):
        """Test configuration with explicit parameters."""
        configure_logging(level="DEBUG", format_type="json", output="stdout")

        root_logger = logging.getLogger()

        assert root_logger.level == logging.DEBUG
        assert len(root_logger.handlers) > 0

        # Check formatter type
        handler = root_logger.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_configure_with_text_format(self):
        """Test configuration with text format."""
        configure_logging(level="INFO", format_type="text", output="stdout")

        root_logger = logging.getLogger()
        handler = root_logger.handlers[0]

        assert not isinstance(handler.formatter, JSONFormatter)
        assert isinstance(handler.formatter, logging.Formatter)

    def test_configure_from_env_vars(self, monkeypatch):
        """Test configuration from environment variables."""
        monkeypatch.setenv("CORE_LOG_LEVEL", "WARNING")
        monkeypatch.setenv("CORE_LOG_FORMAT", "json")

        configure_logging()

        root_logger = logging.getLogger()
        assert root_logger.level == logging.WARNING

    def test_configure_clears_existing_handlers(self):
        """Test that configuration clears existing handlers."""
        # Add some handlers
        root_logger = logging.getLogger()
        initial_handler_count = len(root_logger.handlers)

        root_logger.addHandler(logging.StreamHandler())
        root_logger.addHandler(logging.StreamHandler())

        # Configure should clear them
        configure_logging()

        # Should have only 1 handler (the one we just configured)
        assert len(root_logger.handlers) == 1


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_structured_logger(self):
        """Test that get_logger returns StructuredLogger instance."""
        logger = get_logger("test.module")

        assert isinstance(logger, StructuredLogger)

    def test_get_logger_with_module_name(self):
        """Test getting logger with module name."""
        logger = get_logger(__name__)

        assert isinstance(logger, StructuredLogger)

    def test_multiple_loggers_same_name(self):
        """Test that multiple calls with same name return loggers with same underlying instance."""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")

        # They should wrap the same Python logger
        assert logger1._logger is logger2._logger


class TestIntegration:
    """Integration tests for logging system."""

    def test_end_to_end_json_logging(self):
        """Test complete flow from configuration to logging."""
        # Configure
        configure_logging(level="INFO", format_type="json", output="stdout")

        # Get logger
        logger = get_logger("test.integration")

        # Create string IO to capture output
        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(JSONFormatter())

        # Replace root logger handler
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)

        # Log with context
        logger.info(
            "Integration test",
            context={"user_id": 456, "action": "test", "nested": {"key": "value"}},
        )

        # Verify output
        output = string_io.getvalue()
        log_data = json.loads(output)

        assert log_data["level"] == "INFO"
        assert log_data["message"] == "Integration test"
        assert log_data["context"]["user_id"] == 456
        assert log_data["context"]["action"] == "test"
        assert log_data["context"]["nested"]["key"] == "value"

    def test_logging_with_different_levels(self):
        """Test that log level filtering works correctly."""
        configure_logging(level="WARNING", format_type="json", output="stdout")

        string_io = StringIO()
        handler = logging.StreamHandler(string_io)
        handler.setFormatter(JSONFormatter())

        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(handler)

        logger = get_logger("test.levels")

        # These should not appear (below WARNING)
        logger.debug("Debug message")
        logger.info("Info message")

        # These should appear
        logger.warning("Warning message")
        logger.error("Error message")

        output = string_io.getvalue()
        lines = output.strip().split("\n")

        # Should have only 2 log entries (warning and error)
        assert len(lines) == 2

        log1 = json.loads(lines[0])
        log2 = json.loads(lines[1])

        assert log1["level"] == "WARNING"
        assert log2["level"] == "ERROR"
