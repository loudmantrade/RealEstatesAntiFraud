"""Integration tests for Redis infrastructure.

These tests verify that Redis is properly configured and accessible
in both local and CI environments.
"""

import pytest
import redis.asyncio as redis

pytestmark = [pytest.mark.integration, pytest.mark.redis]


@pytest.mark.asyncio
class TestRedisInfrastructure:
    """Test Redis infrastructure setup and connectivity."""

    async def test_redis_connection(self, redis_client: redis.Redis):
        """Test that Redis connection is established."""
        result = await redis_client.ping()
        assert result is True

    async def test_redis_set_and_get(self, redis_clean: redis.Redis):
        """Test basic Redis set/get operations."""
        # Set a value
        await redis_clean.set("test_key", "test_value")

        # Get the value
        value = await redis_clean.get("test_key")
        assert value == "test_value"

    async def test_redis_delete(self, redis_clean: redis.Redis):
        """Test Redis delete operation."""
        # Set a value
        await redis_clean.set("test_key", "test_value")

        # Delete it
        result = await redis_clean.delete("test_key")
        assert result == 1

        # Verify it's gone
        value = await redis_clean.get("test_key")
        assert value is None

    async def test_redis_expiry(self, redis_clean: redis.Redis):
        """Test Redis key expiration."""
        # Set a value with 1 second TTL
        await redis_clean.setex("temp_key", 1, "temp_value")

        # Immediately get it
        value = await redis_clean.get("temp_key")
        assert value == "temp_value"

        # Check TTL is set
        ttl = await redis_clean.ttl("temp_key")
        assert 0 < ttl <= 1

    async def test_redis_hash_operations(self, redis_clean: redis.Redis):
        """Test Redis hash operations."""
        # Set hash fields
        await redis_clean.hset("user:1", mapping={"name": "John", "age": "30"})

        # Get single field
        name = await redis_clean.hget("user:1", "name")
        assert name == "John"

        # Get all fields
        user = await redis_clean.hgetall("user:1")
        assert user == {"name": "John", "age": "30"}

    async def test_redis_list_operations(self, redis_clean: redis.Redis):
        """Test Redis list operations."""
        # Push items to list
        await redis_clean.lpush("queue", "item1", "item2", "item3")

        # Get list length
        length = await redis_clean.llen("queue")
        assert length == 3

        # Pop item
        item = await redis_clean.rpop("queue")
        assert item == "item1"

        # Check new length
        length = await redis_clean.llen("queue")
        assert length == 2

    async def test_redis_set_operations(self, redis_clean: redis.Redis):
        """Test Redis set operations."""
        # Add members to set
        await redis_clean.sadd("tags", "python", "redis", "testing")

        # Check membership (returns 1 for member, 0 for non-member)
        is_member = await redis_clean.sismember("tags", "python")
        assert is_member == 1

        # Get all members
        members = await redis_clean.smembers("tags")
        assert members == {"python", "redis", "testing"}

        # Get set size
        size = await redis_clean.scard("tags")
        assert size == 3

    async def test_redis_isolation_between_tests(self, redis_clean: redis.Redis):
        """Test that Redis is cleaned between tests."""
        # This test should start with empty database
        keys = await redis_clean.keys("*")
        assert keys == []

        # Set some data
        await redis_clean.set("isolation_test", "value")

        # Verify it's there
        value = await redis_clean.get("isolation_test")
        assert value == "value"

    async def test_redis_transaction(self, redis_clean: redis.Redis):
        """Test Redis transaction (MULTI/EXEC)."""
        # Start transaction
        pipeline = redis_clean.pipeline(transaction=True)

        # Queue commands
        pipeline.set("key1", "value1")
        pipeline.set("key2", "value2")
        pipeline.incr("counter")

        # Execute transaction
        results = await pipeline.execute()

        # Verify results
        assert results == [True, True, 1]

        # Verify values were set
        value1 = await redis_clean.get("key1")
        value2 = await redis_clean.get("key2")
        counter = await redis_clean.get("counter")

        assert value1 == "value1"
        assert value2 == "value2"
        assert counter == "1"

    async def test_redis_pipeline_performance(self, redis_clean: redis.Redis):
        """Test Redis pipeline for batch operations."""
        # Create pipeline (non-transactional)
        pipeline = redis_clean.pipeline(transaction=False)

        # Queue 100 SET commands
        for i in range(100):
            pipeline.set(f"key_{i}", f"value_{i}")

        # Execute all at once
        results = await pipeline.execute()

        # All should succeed
        assert len(results) == 100
        assert all(r is True for r in results)

        # Verify a few values
        value_0 = await redis_clean.get("key_0")
        value_99 = await redis_clean.get("key_99")

        assert value_0 == "value_0"
        assert value_99 == "value_99"
