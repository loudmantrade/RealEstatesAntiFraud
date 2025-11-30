# Redis Test Infrastructure

This document describes the Redis test infrastructure setup for integration testing.

## Overview

Redis is used for:
- Message queue implementation (`RedisQueue`)
- Caching layer
- Session storage
- Real-time features

The test infrastructure provides Redis instances for both local development and CI/CD environments.

## Local Development Setup

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ with test dependencies

### Starting Redis

```bash
# Start all test services (PostgreSQL + Redis)
docker-compose -f docker-compose.test.yml up -d

# Check services status
docker-compose -f docker-compose.test.yml ps

# View Redis logs
docker logs real-estate-redis-test

# Stop services
docker-compose -f docker-compose.test.yml down
```

### Redis Configuration

Local Redis runs on **port 6380** (not 6379) to avoid conflicts with any Redis instance you might have running locally.

```yaml
# docker-compose.test.yml
redis-test:
  image: redis:7-alpine
  ports:
    - "6380:6379"  # Local: 6380, Container: 6379
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

### Environment Variables

For local testing, create or update `.env.test`:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0
```

## CI/CD Setup

### GitHub Actions

Redis is automatically configured in CI pipeline as a service container:

```yaml
# .github/workflows/ci.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - 6379:6379
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

Environment variables in CI:

```yaml
env:
  REDIS_HOST: localhost
  REDIS_PORT: 6379  # CI uses standard port
  REDIS_DB: 0
```

## Test Fixtures

### Available Fixtures

#### `redis_client` (session-scoped)

Provides a Redis client for the entire test session. Connection is established once and reused.

```python
@pytest.mark.asyncio
async def test_something(redis_client):
    await redis_client.set("key", "value")
    value = await redis_client.get("key")
    assert value == "value"
```

#### `redis_clean` (function-scoped)

Provides a clean Redis instance for each test. Database is flushed before and after each test.

```python
@pytest.mark.asyncio
async def test_isolated(redis_clean):
    # Redis is empty at start
    keys = await redis_clean.keys("*")
    assert keys == []

    # Your test code...
```

### Fixture Implementation

Located in `tests/integration/conftest.py`:

```python
@pytest.fixture(scope="session")
async def redis_client(test_config: dict):
    """Session-scoped Redis client."""
    client = await redis.from_url(
        test_config["redis_url"],
        encoding="utf-8",
        decode_responses=True,
    )
    yield client
    await client.flushdb()
    await client.close()

@pytest.fixture(scope="function")
async def redis_clean(redis_client):
    """Function-scoped clean Redis."""
    await redis_client.flushdb()
    yield redis_client
    await redis_client.flushdb()
```

## Writing Redis Tests

### Basic Test Example

```python
import pytest
import redis.asyncio as redis

@pytest.mark.asyncio
class TestMyFeature:
    async def test_redis_operation(self, redis_clean):
        """Test with clean Redis state."""
        # Set data
        await redis_clean.set("user:1", "John")

        # Get data
        name = await redis_clean.get("user:1")
        assert name == "John"
```

### Testing Queue Operations

```python
@pytest.mark.asyncio
async def test_queue_push_pop(redis_clean):
    """Test queue operations."""
    # Push to queue
    await redis_clean.lpush("queue:tasks", "task1", "task2")

    # Pop from queue
    task = await redis_clean.rpop("queue:tasks")
    assert task == "task1"

    # Check remaining
    length = await redis_clean.llen("queue:tasks")
    assert length == 1
```

### Testing with Expiry

```python
@pytest.mark.asyncio
async def test_cache_with_ttl(redis_clean):
    """Test cached data with TTL."""
    # Set with 60 second expiry
    await redis_clean.setex("cache:key", 60, "cached_value")

    # Verify TTL
    ttl = await redis_clean.ttl("cache:key")
    assert 0 < ttl <= 60

    # Get value
    value = await redis_clean.get("cache:key")
    assert value == "cached_value"
```

### Testing Transactions

```python
@pytest.mark.asyncio
async def test_transaction(redis_clean):
    """Test atomic operations."""
    pipeline = redis_clean.pipeline(transaction=True)

    pipeline.set("counter", 0)
    pipeline.incr("counter")
    pipeline.incr("counter")

    results = await pipeline.execute()

    counter = await redis_clean.get("counter")
    assert counter == "2"
```

## Running Redis Tests

### Run All Integration Tests

```bash
# With Redis running in docker-compose
pytest tests/integration/ -v
```

### Run Only Redis Infrastructure Tests

```bash
pytest tests/integration/test_redis_infrastructure.py -v
```

### Run Specific Test

```bash
pytest tests/integration/test_redis_infrastructure.py::TestRedisInfrastructure::test_redis_connection -v
```

### With Coverage

```bash
pytest tests/integration/ --cov=core --cov-report=term-missing -v
```

## Troubleshooting

### Redis Not Connecting (Local)

```bash
# Check if Redis container is running
docker ps | grep redis

# Check Redis logs
docker logs real-estate-redis-test

# Try manual connection
docker exec -it real-estate-redis-test redis-cli ping
# Should return: PONG

# Restart Redis
docker-compose -f docker-compose.test.yml restart redis-test
```

### Port Already in Use

If port 6380 is already in use locally:

```bash
# Check what's using the port
lsof -i :6380

# Kill the process or change port in docker-compose.test.yml
```

### Connection Timeout in Tests

```python
# Add connection timeout to test fixture if needed
client = await redis.from_url(
    redis_url,
    socket_connect_timeout=5,
    socket_timeout=5,
)
```

### CI Failures

If tests pass locally but fail in CI:

1. Check that `REDIS_HOST` and `REDIS_PORT` match CI service configuration
2. Verify Redis service health check is passing in CI logs
3. Check for port conflicts with other services
4. Verify Redis service is defined in correct job

## Redis Best Practices for Tests

### 1. Always Use Clean Fixtures

```python
# ✅ Good: Isolated test
async def test_something(redis_clean):
    ...

# ❌ Bad: Shared state
async def test_something(redis_client):
    # Data from previous tests may exist
```

### 2. Clean Up After Complex Operations

```python
async def test_complex_operation(redis_clean):
    try:
        # Test code
        await redis_clean.set("key", "value")
        # ... more operations ...
    finally:
        # Explicit cleanup if needed
        await redis_clean.delete("key")
```

### 3. Use Pipelines for Batch Operations

```python
# ✅ Efficient: One round-trip
pipeline = redis_clean.pipeline()
for i in range(100):
    pipeline.set(f"key_{i}", f"val_{i}")
await pipeline.execute()

# ❌ Slow: 100 round-trips
for i in range(100):
    await redis_clean.set(f"key_{i}", f"val_{i}")
```

### 4. Test with Realistic Data Sizes

```python
# Test with realistic message sizes
large_message = "x" * 1024 * 10  # 10KB
await redis_clean.lpush("queue", large_message)
```

### 5. Verify Cleanup

```python
async def test_cleanup(redis_clean):
    # Start clean
    keys = await redis_clean.keys("*")
    assert len(keys) == 0

    # Test operations...
```

## Performance Considerations

### Redis in tmpfs

Test Redis uses tmpfs (RAM disk) for better performance:

```yaml
tmpfs:
  - /data  # Redis data in memory, not disk
```

### Connection Pooling

Redis client uses connection pooling by default:

```python
client = await redis.from_url(
    redis_url,
    max_connections=10,  # Pool size
)
```

### Disable Persistence

Test Redis disables persistence for speed:

```yaml
command: redis-server --save ""  # No RDB snapshots
```

## Related Documentation

- [Messaging Architecture](./MESSAGING.md) - How Redis is used for queues
- [Integration Testing](../tests/integration/README.md) - General integration testing guide
- [Redis Official Docs](https://redis.io/docs/) - Redis documentation

## Related Issues

- #108 - Redis test infrastructure setup
- #103 - Integration tests for messaging layer
- #26-#28 - Messaging implementation
