"""
Structured JSON logging for the application.

This module provides a structured logging system that outputs logs in JSON format,
making them easy to parse and analyze in log aggregation systems.

Usage:
    from core.utils.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("User logged in", extra={"user_id": 123, "ip": "192.168.1.1"})
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records in JSON format.

    Standard fields:
    - timestamp: ISO8601 formatted UTC timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - message: The log message
    - logger: Logger name (usually module name)
    - module: Module name where log was called
    - function: Function name where log was called
    - line: Line number where log was called
    - context: Additional context fields passed via 'extra' parameter
    """

    # Fields to exclude from context (internal logging fields)
    RESERVED_FIELDS = {
        "name",
        "msg",
        "args",
        "created",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "thread",
        "threadName",
        "exc_info",
        "exc_text",
        "stack_info",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.

        Args:
            record: The log record to format

        Returns:
            JSON string representation of the log record
        """
        # Import here to avoid circular imports
        from core.utils.context import get_request_id, get_trace_id
        
        # Build the standard log structure
        log_data: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add trace IDs if available (from context)
        trace_id = get_trace_id()
        request_id = get_request_id()
        if trace_id:
            log_data["trace_id"] = trace_id
        if request_id:
            log_data["request_id"] = request_id

        # Extract context from extra fields
        context: Dict[str, Any] = {}
        for key, value in record.__dict__.items():
            if key not in self.RESERVED_FIELDS:
                context[key] = value

        if context:
            log_data["context"] = context

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add stack trace if present
        if record.stack_info:
            log_data["stack_trace"] = self.formatStack(record.stack_info)

        return json.dumps(log_data)


class StructuredLogger:
    """
    Wrapper around Python's logging.Logger that provides structured logging.

    This class provides a convenient interface for structured logging while
    maintaining compatibility with Python's standard logging module.
    """

    def __init__(self, logger: logging.Logger):
        """
        Initialize the structured logger.

        Args:
            logger: The underlying Python logger instance
        """
        self._logger = logger

    def _log(
        self,
        level: int,
        msg: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Internal method to log with context.

        Args:
            level: Log level (from logging module)
            msg: Log message
            context: Additional context fields to include
            exc_info: Whether to include exception info
            **kwargs: Additional keyword arguments passed to logger
        """
        extra = context.copy() if context else {}
        extra.update(kwargs)
        self._logger.log(level, msg, extra=extra, exc_info=exc_info)

    def debug(
        self, msg: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        """Log a debug message."""
        self._log(logging.DEBUG, msg, context, **kwargs)

    def info(
        self, msg: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        """Log an info message."""
        self._log(logging.INFO, msg, context, **kwargs)

    def warning(
        self, msg: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        """Log a warning message."""
        self._log(logging.WARNING, msg, context, **kwargs)

    def error(
        self,
        msg: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
        **kwargs: Any,
    ) -> None:
        """Log an error message."""
        self._log(logging.ERROR, msg, context, exc_info=exc_info, **kwargs)

    def critical(
        self,
        msg: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
        **kwargs: Any,
    ) -> None:
        """Log a critical message."""
        self._log(logging.CRITICAL, msg, context, exc_info=exc_info, **kwargs)

    def exception(
        self, msg: str, context: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        """Log an exception with traceback."""
        self._log(logging.ERROR, msg, context, exc_info=True, **kwargs)


def configure_logging(
    level: Optional[str] = None,
    format_type: Optional[str] = None,
    output: Optional[str] = None,
) -> None:
    """
    Configure the root logger with structured logging.

    This function can be called in two ways:
    1. With explicit parameters (for testing or custom setup)
    2. Without parameters - reads from config_manager (recommended)

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               If None, reads from CORE_LOG_LEVEL or config
        format_type: Output format ('json' or 'text')
                    If None, reads from CORE_LOG_FORMAT or config
        output: Output destination ('stdout' or file path)
               If None, reads from CORE_LOG_FILE or uses stdout

    Environment Variables (highest priority):
        CORE_LOG_LEVEL: Log level (default: INFO)
        CORE_LOG_FORMAT: Format type (default: json)
        CORE_LOG_FILE: File path for logs (default: stdout)
    """
    import os

    # Read from environment variables or use provided values
    if level is None:
        level = os.environ.get("CORE_LOG_LEVEL", "INFO")
    if format_type is None:
        format_type = os.environ.get("CORE_LOG_FORMAT", "json")
    if output is None:
        output = os.environ.get("CORE_LOG_FILE", "stdout")

    # Get the root logger
    root_logger = logging.getLogger()

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Set log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(log_level)

    # Create handler
    if output.lower() == "stdout":
        handler = logging.StreamHandler(sys.stdout)
    else:
        handler = logging.FileHandler(output)

    # Set formatter
    formatter: logging.Formatter
    if format_type.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def get_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        StructuredLogger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("User action", context={"user_id": 123, "action": "login"})
    """
    python_logger = logging.getLogger(name)
    return StructuredLogger(python_logger)
