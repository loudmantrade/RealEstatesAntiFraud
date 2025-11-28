# Structured JSON Logging

This document describes the structured JSON logging system implemented in the RealEstatesAntiFraud project.

## Overview

The logging system provides structured JSON logging with the following features:

- **JSON Output Format**: All logs are formatted as JSON for easy parsing by log aggregation systems
- **Standard Fields**: Every log entry includes timestamp, level, message, logger name, module, function, and line number
- **Context Fields**: Additional context can be passed via the `context` parameter
- **Configuration**: Logging can be configured via environment variables or programmatically
- **FastAPI Integration**: Automatic request/response logging with timing information
- **High Test Coverage**: 97% test coverage with comprehensive unit and integration tests

## Quick Start

### Basic Usage

```python
from core.utils.logging import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("Application started")

# Logging with context
logger.info(
    "User logged in",
    context={
        "user_id": 123,
        "ip_address": "192.168.1.1",
        "session_id": "abc-123"
    }
)

# Error logging with exception
try:
    result = risky_operation()
except Exception:
    logger.exception(
        "Operation failed",
        context={"operation": "risky_operation"}
    )
```

### Configuration

#### Environment Variables

The logging system reads configuration from environment variables:

```bash
# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export CORE_LOG_LEVEL=INFO

# Output format (json or text)
export CORE_LOG_FORMAT=json

# Output destination (stdout or file path)
export CORE_LOG_FILE=stdout
```

#### Programmatic Configuration

```python
from core.utils.logging import configure_logging

# Configure with explicit parameters
configure_logging(
    level="DEBUG",
    format_type="json",
    output="stdout"
)

# Or let it read from environment variables
configure_logging()
```

## JSON Output Format

### Standard Fields

Every log entry includes these standard fields:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "level": "INFO",
  "message": "User logged in",
  "logger": "core.api.routes.auth",
  "module": "auth",
  "function": "login",
  "line": 42
}
```

### With Context

When you provide additional context:

```python
logger.info(
    "User logged in",
    context={
        "user_id": 123,
        "ip_address": "192.168.1.1"
    }
)
```

The output includes a `context` field:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "level": "INFO",
  "message": "User logged in",
  "logger": "core.api.routes.auth",
  "module": "auth",
  "function": "login",
  "line": 42,
  "context": {
    "user_id": 123,
    "ip_address": "192.168.1.1"
  }
}
```

### With Exception

When logging exceptions:

```python
try:
    risky_operation()
except Exception:
    logger.exception("Operation failed")
```

The output includes the full exception traceback:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "level": "ERROR",
  "message": "Operation failed",
  "logger": "core.api.routes.operations",
  "module": "operations",
  "function": "risky_operation",
  "line": 123,
  "exception": "Traceback (most recent call last):\n  File ...\nValueError: Invalid input"
}
```

## FastAPI Integration

The logging system is automatically integrated with FastAPI via middleware:

### Application Lifecycle Events

```json
// Application startup
{
  "timestamp": "2024-01-15T10:00:00.000000+00:00",
  "level": "INFO",
  "message": "Application starting",
  "context": {
    "app_name": "RealEstatesAntiFraud Core API",
    "version": "1.0.0",
    "docs_url": "/api/v1/docs"
  }
}

// Application shutdown
{
  "timestamp": "2024-01-15T18:00:00.000000+00:00",
  "level": "INFO",
  "message": "Application shutting down",
  "context": {
    "app_name": "RealEstatesAntiFraud Core API"
  }
}
```

### HTTP Request Logging

Each HTTP request generates two log entries:

```json
// Request received
{
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "level": "INFO",
  "message": "HTTP request received",
  "context": {
    "method": "GET",
    "path": "/api/v1/listings",
    "query_params": "page=1&limit=10",
    "client_ip": "192.168.1.1"
  }
}

// Request completed
{
  "timestamp": "2024-01-15T10:30:45.234567+00:00",
  "level": "INFO",
  "message": "HTTP request completed",
  "context": {
    "method": "GET",
    "path": "/api/v1/listings",
    "status_code": 200,
    "duration_ms": 111.11
  }
}
```

## Log Levels

The system supports all standard Python log levels:

| Level    | Numeric Value | Usage                                      |
|----------|---------------|--------------------------------------------|
| DEBUG    | 10            | Detailed debugging information             |
| INFO     | 20            | General informational messages             |
| WARNING  | 30            | Warning messages (potential issues)        |
| ERROR    | 40            | Error messages (operation failed)          |
| CRITICAL | 50            | Critical errors (system-level failures)    |

### Example Usage

```python
logger = get_logger(__name__)

# Debug - detailed information for debugging
logger.debug("Cache lookup", context={"key": "user:123", "hit": True})

# Info - normal operations
logger.info("User created", context={"user_id": 123, "email": "user@example.com"})

# Warning - potential problems
logger.warning("Rate limit approaching", context={"user_id": 123, "requests": 95})

# Error - operation failed
logger.error("Database connection failed", context={"host": "db.example.com"})

# Critical - system-level failure
logger.critical("Out of disk space", context={"available_bytes": 0})

# Exception - error with full traceback
try:
    process_data()
except Exception:
    logger.exception("Data processing failed", context={"batch_id": 456})
```

## Best Practices

### 1. Use Structured Context

Instead of string interpolation, use the `context` parameter:

```python
# ❌ Bad - loses structure
logger.info(f"User {user_id} performed action {action}")

# ✅ Good - maintains structure
logger.info(
    "User action performed",
    context={"user_id": user_id, "action": action}
)
```

### 2. Include Relevant Context

Provide context that will help with debugging and analysis:

```python
logger.info(
    "Database query executed",
    context={
        "table": "listings",
        "operation": "select",
        "rows_returned": 50,
        "duration_ms": 125.5,
        "filters": {"city": "Moscow", "price_max": 10000000}
    }
)
```

### 3. Use Appropriate Log Levels

- **DEBUG**: Detailed information for debugging (not logged in production)
- **INFO**: Normal operations, business events
- **WARNING**: Recoverable issues, deprecation warnings
- **ERROR**: Operation failures that need attention
- **CRITICAL**: System-level failures requiring immediate action

### 4. Log Exceptions with Context

When catching exceptions, always provide context:

```python
try:
    update_listing(listing_id, data)
except ValidationError:
    logger.exception(
        "Listing update validation failed",
        context={
            "listing_id": listing_id,
            "fields": list(data.keys())
        }
    )
except DatabaseError:
    logger.exception(
        "Database error during listing update",
        context={"listing_id": listing_id}
    )
```

### 5. Avoid Logging Sensitive Data

Never log passwords, tokens, or other sensitive information:

```python
# ❌ Bad - logs password
logger.info("User login", context={"username": username, "password": password})

# ✅ Good - omits sensitive data
logger.info("User login", context={"username": username})
```

## Log Aggregation

The JSON format makes it easy to integrate with log aggregation systems:

### Example: Elasticsearch Query

```json
{
  "query": {
    "bool": {
      "must": [
        {"term": {"level": "ERROR"}},
        {"range": {"timestamp": {"gte": "now-1h"}}},
        {"term": {"context.user_id": 123}}
      ]
    }
  }
}
```

### Example: CloudWatch Insights Query

```
fields @timestamp, message, context.user_id, context.action
| filter level = "ERROR"
| filter @timestamp > ago(1h)
| stats count() by context.action
```

## Testing

The logging system has comprehensive test coverage (97%):

```bash
# Run logging tests
pytest tests/unit/test_logging.py -v

# Run with coverage report
pytest tests/unit/test_logging.py --cov=core.utils.logging --cov-report=term-missing
```

Test categories:
- JSON formatter output validation
- All log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Context field injection
- Exception logging with tracebacks
- Configuration from environment variables
- Integration with FastAPI

## Architecture

### Components

1. **JSONFormatter**: Custom `logging.Formatter` that outputs JSON
2. **StructuredLogger**: Wrapper around Python's `logging.Logger` with context support
3. **configure_logging()**: Configures the root logger with JSON output
4. **get_logger()**: Factory function to create structured loggers
5. **FastAPI Middleware**: Automatic HTTP request/response logging

### Design Decisions

- **No External Dependencies**: Uses only Python standard library
- **Standard Logging Compatibility**: Built on Python's `logging` module
- **Thread-Safe**: All operations are thread-safe via Python's logging locks
- **Performance**: Minimal overhead, efficient JSON serialization
- **Extensibility**: Easy to add custom fields or formatters

## Future Enhancements

Planned improvements for the logging system:

1. **Request Tracing** (Issue #20):
   - Correlation IDs for distributed tracing
   - Request chain tracking across services
   - Integration with OpenTelemetry

2. **Log Sampling**:
   - Reduce log volume in high-traffic scenarios
   - Configurable sampling rates per log level

3. **Log Enrichment**:
   - Automatic addition of service name, version, environment
   - Host/container information
   - Git commit hash

4. **Async Logging**:
   - Non-blocking log writes for improved performance
   - Queue-based handler for high-volume scenarios

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/)
- [JSON Logging Standards](https://www.ietf.org/archive/id/draft-sinnema-cloudevents-subscriptions-01.html)
- [OpenTelemetry Logging](https://opentelemetry.io/docs/reference/specification/logs/)
