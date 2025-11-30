"""
Queue module for message queue abstractions.

Provides unified interface for different message queue backends.
"""

from core.queue.in_memory_queue import InMemoryQueuePlugin

__all__ = ["InMemoryQueuePlugin"]

# Redis queue is optional (requires redis package)
try:
    from core.queue.redis_queue import RedisQueuePlugin  # noqa: F401

    __all__.append("RedisQueuePlugin")
except ImportError:
    pass
