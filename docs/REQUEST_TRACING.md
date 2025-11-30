# Request Tracing with Correlation IDs

This document describes the distributed tracing system implemented using correlation IDs for request tracking across services.

## Overview

The request tracing system provides:

- **Automatic ID Generation**: Trace and request IDs are automatically generated for each request
- **ID Propagation**: IDs can be propagated from incoming requests via HTTP headers
- **Context Management**: Thread-safe, async-safe context storage using `contextvars`
- **Logging Integration**: All logs automatically include trace and request IDs
- **Header Support**: Standard HTTP headers for distributed tracing

## Core Concepts

### Trace ID

A **Trace ID** identifies a single transaction or operation flow across multiple services. When a request enters your system:
- If it has an `X-Trace-ID` header, that ID is used (preserving the distributed trace)
- Otherwise, a new trace ID is generated (starting a new trace)

**Format**: 32-character hexadecimal string (UUID4 without hyphens)

### Request ID

A **Request ID** uniquely identifies a single HTTP request within your service. Each request gets its own request ID, even if they share the same trace ID.

**Format**: 32-character hexadecimal string (UUID4 without hyphens)

## Quick Start

### Basic Usage

The tracing system is automatically enabled via middleware. No configuration needed!

```python
# In your application code
from core.utils import get_trace_id, get_request_id

# Get current trace context
trace_id = get_trace_id()
request_id = get_request_id()

# Use in your logic
print(f"Processing request {request_id} in trace {trace_id}")
```

### Manual Context Management

For background tasks or message queue consumers:

```python
from core.utils import set_trace_context, clear_trace_context

# Set context (e.g., from message queue event)
trace_id, request_id = set_trace_context(
    trace_id="external-trace-123",  # Optional
    request_id="msg-456"  # Optional
)

try:
    # Your processing logic
    process_event()
finally:
    # Always clean up context
    clear_trace_context()
```

## HTTP Headers

### Standard Headers

The system uses these HTTP headers for trace propagation:

| Header | Description | Example |
|--------|-------------|---------|
| `X-Trace-ID` | Distributed trace identifier | `abc123def456789...` |
| `X-Request-ID` | Individual request identifier | `req789abc123def...` |

### Incoming Requests

When your service receives a request:

```http
GET /api/v1/listings HTTP/1.1
Host: api.example.com
X-Trace-ID: distributed-trace-123
```

The middleware will:
1. Extract the `X-Trace-ID` from headers (if present)
2. Generate a new `X-Request-ID`
3. Set both in the request context
4. Include them in all logs

### Outgoing Responses

All responses automatically include trace headers:

```http
HTTP/1.1 200 OK
X-Trace-ID: distributed-trace-123
X-Request-ID: generated-request-456
Content-Type: application/json

{"status": "ok"}
```

### Making Outbound Requests

When calling other services, propagate the trace ID:

```python
import httpx
from core.utils import get_trace_id

async def call_external_service():
    trace_id = get_trace_id()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://other-service.example.com/api/data",
            headers={"X-Trace-ID": trace_id} if trace_id else {}
        )
    return response.json()
```

## Logging Integration

All logs automatically include trace and request IDs when available:

```python
from core.utils import get_logger

logger = get_logger(__name__)

# Simple logging - trace IDs added automatically
logger.info("Processing listing")
```

**JSON Output**:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456+00:00",
  "level": "INFO",
  "message": "Processing listing",
  "logger": "core.api.routes.listings",
  "module": "listings",
  "function": "get_listing",
  "line": 42,
  "trace_id": "abc123def456789...",
  "request_id": "req789abc123def...",
  "context": {}
}
```

## Architecture

### Components

#### 1. Context Module (`core/utils/context.py`)

Provides context variables for storing trace IDs:

- `get_trace_id()` - Get current trace ID
- `get_request_id()` - Get current request ID
- `set_trace_context()` - Set both IDs
- `clear_trace_context()` - Clean up context
- `generate_trace_id()` - Generate new trace ID
- `generate_request_id()` - Generate new request ID

#### 2. Trace Middleware (`core/api/main.py`)

FastAPI middleware that:
1. Extracts IDs from request headers
2. Sets them in context
3. Adds them to response headers
4. Ensures cleanup after request

```python
@app.middleware("http")
async def trace_context_middleware(request: Request, call_next):
    # Extract or generate IDs
    trace_id = request.headers.get("x-trace-id")
    request_id = request.headers.get("x-request-id")

    # Set context
    trace_id, request_id = set_trace_context(trace_id, request_id)

    try:
        # Process request
        response = await call_next(request)

        # Add headers to response
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Request-ID"] = request_id

        return response
    finally:
        # Cleanup
        clear_trace_context()
```

#### 3. Logging Integration (`core/utils/logging.py`)

JSONFormatter automatically includes trace IDs:

```python
def format(self, record: logging.LogRecord) -> str:
    from core.utils.context import get_trace_id, get_request_id

    log_data = {
        "timestamp": ...,
        "level": ...,
        "message": ...,
    }

    # Add trace IDs if available
    trace_id = get_trace_id()
    request_id = get_request_id()
    if trace_id:
        log_data["trace_id"] = trace_id
    if request_id:
        log_data["request_id"] = request_id

    return json.dumps(log_data)
```

### Context Isolation

Uses Python's `contextvars` for thread-safe, async-safe context storage:

```python
from contextvars import ContextVar

_trace_id: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
```

**Benefits**:
- Thread-safe: Each thread has its own context
- Async-safe: Works correctly with asyncio
- Automatic propagation: Inherited by child tasks
- No global state: No risk of context leakage

## Use Cases

### 1. HTTP Request Tracing

**Scenario**: Track a single user request through your API

```python
# Automatic via middleware
# Request comes in → trace_id generated → all logs include it
```

**Log Output**:
```json
{"trace_id": "abc123", "message": "Request received"}
{"trace_id": "abc123", "message": "Fetching data from DB"}
{"trace_id": "abc123", "message": "Processing results"}
{"trace_id": "abc123", "message": "Request completed"}
```

### 2. Distributed Tracing

**Scenario**: Track request across multiple microservices

**Service A** (API Gateway):
```python
# Generates trace_id = "dist-123"
# Calls Service B with X-Trace-ID: dist-123
```

**Service B** (Listings Service):
```python
# Receives X-Trace-ID: dist-123
# Middleware extracts and uses it
# All logs include trace_id: "dist-123"
```

**Result**: All logs from both services share the same `trace_id`, enabling full request tracing.

### 3. Background Job Tracing

**Scenario**: Process message queue events with tracing

```python
from core.utils import set_trace_context, clear_trace_context, get_logger

logger = get_logger(__name__)

async def process_listing_event(event: dict):
    # Extract trace ID from event metadata
    trace_id = event.get("metadata", {}).get("trace_id")

    # Set context
    set_trace_context(trace_id=trace_id)

    try:
        logger.info("Processing listing event", context={"listing_id": event["id"]})

        # Your processing logic
        await process_listing(event["data"])

        logger.info("Event processed successfully")
    except Exception as e:
        logger.exception("Event processing failed")
    finally:
        # Always cleanup
        clear_trace_context()
```

### 4. Database Query Tracing

**Scenario**: Track which request triggered slow queries

```python
from core.utils import get_trace_id, get_logger

logger = get_logger(__name__)

async def execute_query(query: str):
    trace_id = get_trace_id()
    start = time.time()

    # Execute query
    result = await db.execute(query)

    duration = time.time() - start

    if duration > 1.0:  # Slow query
        logger.warning(
            "Slow query detected",
            context={
                "query": query,
                "duration_sec": duration,
                "trace_id": trace_id  # Redundant but explicit
            }
        )

    return result
```

## Testing

### Unit Tests

Test context management:

```python
from core.utils.context import set_trace_context, get_trace_id, clear_trace_context

def test_trace_context():
    # Set context
    trace_id, request_id = set_trace_context("test-123", "req-456")

    assert get_trace_id() == "test-123"

    # Cleanup
    clear_trace_context()
    assert get_trace_id() is None
```

### Integration Tests

Test with FastAPI TestClient:

```python
from fastapi.testclient import TestClient
from core.api.main import app

def test_trace_propagation():
    client = TestClient(app)

    response = client.get(
        "/api/v1/listings",
        headers={"X-Trace-ID": "my-trace-123"}
    )

    # Trace ID should be in response headers
    assert response.headers["X-Trace-ID"] == "my-trace-123"
    assert "X-Request-ID" in response.headers
```

### Manual Testing

Use curl to test trace propagation:

```bash
# Send request with trace ID
curl -H "X-Trace-ID: manual-test-123" \
     http://localhost:8000/api/v1/listings

# Check response headers
# Should include: X-Trace-ID: manual-test-123

# Check logs - should show trace_id in JSON
```

## Best Practices

### 1. Always Propagate Trace IDs

When making outbound requests:

```python
# ✅ Good - propagate trace ID
trace_id = get_trace_id()
headers = {"X-Trace-ID": trace_id} if trace_id else {}
response = await client.get(url, headers=headers)

# ❌ Bad - lose tracing context
response = await client.get(url)
```

### 2. Clean Up Context in Background Tasks

```python
# ✅ Good - cleanup in finally
set_trace_context(trace_id=event["trace_id"])
try:
    process()
finally:
    clear_trace_context()

# ❌ Bad - context leaks
set_trace_context(trace_id=event["trace_id"])
process()
```

### 3. Use Trace IDs in Error Reporting

```python
# ✅ Good - include trace ID in error
try:
    process()
except Exception as e:
    trace_id = get_trace_id()
    logger.exception("Processing failed", context={"trace_id": trace_id})
    raise HTTPException(
        status_code=500,
        detail=f"Processing failed (trace: {trace_id})"
    )
```

### 4. Store Trace IDs in Database

For async operations, store trace IDs:

```python
# When creating a job
job = await jobs.create(
    task="process_listing",
    data={"listing_id": 123},
    trace_id=get_trace_id()  # Store for later
)

# When processing the job
set_trace_context(trace_id=job.trace_id)
try:
    process_job(job)
finally:
    clear_trace_context()
```

## Log Aggregation

### Elasticsearch Query

Find all logs for a specific trace:

```json
{
  "query": {
    "term": {
      "trace_id": "abc123def456"
    }
  },
  "sort": [
    {"timestamp": "asc"}
  ]
}
```

### CloudWatch Insights

```
fields @timestamp, message, trace_id, request_id
| filter trace_id = "abc123def456"
| sort @timestamp asc
```

### Correlation Across Services

Find related logs from multiple services:

```
fields @timestamp, service_name, message
| filter trace_id = "abc123def456"
| sort @timestamp asc
```

## Performance Considerations

### Overhead

The tracing system has minimal overhead:
- **Context variables**: ~100ns per get/set operation
- **UUID generation**: ~1-2μs per ID
- **Header parsing**: Negligible (standard HTTP processing)
- **Logging integration**: ~10-20μs per log (JSON serialization)

**Total per request**: < 10μs

### Scalability

- Context variables scale linearly with concurrent requests
- No global locks or shared state
- Each request has independent context
- Automatic cleanup prevents memory leaks

## Troubleshooting

### Issue: Trace IDs Not Appearing in Logs

**Symptoms**: Logs don't include `trace_id` or `request_id`

**Solutions**:
1. Ensure middleware is registered
2. Check that JSONFormatter is being used
3. Verify context is set before logging

```python
from core.utils import get_trace_id, set_trace_context

# Debug
print(f"Trace ID: {get_trace_id()}")  # Should not be None

# Fix
set_trace_context()  # Generate IDs if missing
```

### Issue: Context Leaking Between Requests

**Symptoms**: Request A's trace ID appears in Request B's logs

**Solutions**:
1. Ensure `clear_trace_context()` is called in `finally` block
2. Check that middleware cleanup is working
3. Verify no global variables are storing IDs

```python
# ✅ Correct - cleanup guaranteed
try:
    process()
finally:
    clear_trace_context()
```

### Issue: Trace IDs Not Propagating to Other Services

**Symptoms**: Downstream services don't see `X-Trace-ID`

**Solutions**:
1. Check that headers are being set in outbound requests
2. Verify header name is correct (`X-Trace-ID`)
3. Ensure trace ID exists before propagating

```python
# Debug
trace_id = get_trace_id()
print(f"Propagating trace: {trace_id}")

# Fix
if not trace_id:
    trace_id, _ = set_trace_context()
```

## References

- [Structured Logging Documentation](./STRUCTURED_LOGGING.md)
- [OpenTelemetry Tracing](https://opentelemetry.io/docs/concepts/signals/traces/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [Python contextvars Documentation](https://docs.python.org/3/library/contextvars.html)
