# Messaging Architecture

This document describes the messaging and event-driven architecture used in the RealEstatesAntiFraud system.

## Overview

The messaging layer provides asynchronous, decoupled communication between system components using a queue-based pub/sub pattern. This enables scalable, distributed processing of listings through multiple pipeline stages.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Scraper   │────>│ Message Queue│────>│ Processing      │
│   Plugins   │     │              │     │ Orchestrator    │
└─────────────┘     └──────────────┘     └─────────────────┘
                            │                      │
                            │                      v
                            │             ┌─────────────────┐
                            │             │ Processing      │
                            │             │ Plugins         │
                            │             └─────────────────┘
                            │                      │
                            v                      v
                    ┌──────────────┐     ┌─────────────────┐
                    │ Dead Letter  │     │ Storage/Index   │
                    │ Queue        │     │                 │
                    └──────────────┘     └─────────────────┘
```

## Core Components

### 1. Queue Plugin Interface

Abstract interface defining the contract for message queue implementations.

**Location**: `core/interfaces/queue_plugin.py`

**Key Methods**:
- `connect()` / `disconnect()` - Connection lifecycle
- `publish(topic, message)` - Send message to topic
- `subscribe(topic, callback)` - Receive messages from topic
- `acknowledge(message_id)` - Confirm message processing
- `reject(message_id, requeue)` - Reject message with optional requeue
- `health_check()` - Monitor queue health

### 2. Queue Implementations

#### InMemory Queue

Thread-safe in-memory queue for development and testing.

**Location**: `core/queue/in_memory_queue.py`

**Features**:
- Thread-safe operations with `threading.RLock`
- Worker threads for each subscription
- Automatic message acknowledgment
- Dead letter queue for failed messages
- Statistics tracking

**Use Cases**:
- Local development
- Unit testing
- CI/CD pipelines
- Prototyping

**Limitations**:
- No persistence (messages lost on restart)
- Single process only (no distributed processing)
- Memory-bound capacity

**Example**:
```python
from core.queue import InMemoryQueuePlugin

# Initialize
queue = InMemoryQueuePlugin()
queue.connect()

# Publish
message = {"listing_id": "123", "data": {...}}
message_id = queue.publish("listings.raw", message)

# Subscribe
def process_listing(message):
    print(f"Processing: {message['listing_id']}")

subscription_id = queue.subscribe("listings.raw", process_listing)

# Cleanup
queue.unsubscribe(subscription_id)
queue.disconnect()
```

#### Redis Queue

Production-ready queue using Redis Streams.

**Location**: `core/queue/redis_queue.py`

**Features**:
- Persistent message storage
- Distributed processing with consumer groups
- `XREADGROUP` for load balancing
- Dead letter queue pattern
- Health checks with latency measurement
- Automatic reconnection

**Configuration**:
```python
from core.queue import RedisQueuePlugin

queue = RedisQueuePlugin(
    host="localhost",
    port=6379,
    db=0,
    password=None,
    consumer_group="processors",
    consumer_name="worker-1",
    max_pending=1000,
    block_ms=5000
)
```

**Use Cases**:
- Production deployments
- Multi-worker processing
- High-throughput systems
- Distributed architectures

**Requirements**:
- Redis Server >= 5.0
- `redis` Python package >= 4.0.0

### 3. Event Models

Standardized event formats for pipeline communication.

**Location**: `core/models/events.py`

#### Event Types

1. **RawListingEvent** - Unparsed data from scraper
   ```python
   {
       "metadata": {...},
       "raw_data": {"html": "...", "json": {...}},
       "source_url": "https://...",
       "scraped_at": "2025-11-28T...",
       "original_id": "listing-123"
   }
   ```

2. **NormalizedListingEvent** - Data mapped to UDM
   ```python
   {
       "metadata": {...},
       "listing_data": {...},  # UDM format
       "validation_errors": [],
       "validation_warnings": [],
       "is_valid": true
   }
   ```

3. **ProcessedListingEvent** - Fully processed with fraud analysis
   ```python
   {
       "metadata": {...},
       "listing_data": {...},
       "fraud_score": 0.35,
       "fraud_signals": ["price_too_low"],
       "risk_level": "medium",
       "processing_stages": ["normalize", "dedupe", "fraud_check"],
       "processing_duration_ms": 125.5
   }
   ```

4. **ProcessingFailedEvent** - Error tracking
   ```python
   {
       "metadata": {...},
       "error_type": "ValidationError",
       "error_message": "...",
       "failed_stage": "normalization",
       "original_event": {...},
       "is_recoverable": true
   }
   ```

5. **FraudDetectedEvent** - Alert events
   ```python
   {
       "metadata": {...},
       "listing_id": "123",
       "fraud_score": 0.85,
       "risk_level": "high",
       "fraud_signals": ["price_anomaly", "duplicate_images"],
       "detected_by": ["fraud_detector_v1"],
       "confidence": 0.92,
       "action": "flag_for_review"
   }
   ```

#### Event Metadata

All events include standard metadata for tracing and tracking:

```python
{
    "event_id": "uuid",
    "event_type": "raw_listing",
    "timestamp": "2025-11-28T...",
    "source_plugin_id": "cian",
    "source_platform": "cian.ru",

    # Tracing (from #20)
    "trace_id": "trace-123",
    "request_id": "req-456",
    "parent_event_id": "uuid",

    # Retry logic
    "retry_count": 0,
    "max_retries": 3,
    "status": "pending",

    # Context
    "tags": {"environment": "production"},
    "version": "1.0"
}
```

### 4. Processing Orchestrator

Coordinates the execution of processing plugins in pipeline stages.

**Location**: `core/pipeline/orchestrator.py`

**Features**:
- Priority-based plugin execution
- Automatic retry with configurable limits
- Error handling and dead letter queue
- Progress tracking and observability
- Graceful startup/shutdown

**Workflow**:
1. Subscribe to `listings.raw` topic
2. For each message:
   - Parse RawListingEvent
   - Execute processing plugins in priority order
   - Handle errors with retry logic
   - Publish ProcessedListingEvent to `listings.processed`
   - Track statistics (duration, plugin count, etc.)

**Example**:
```python
from core.pipeline import ProcessingOrchestrator
from core.plugin_manager import PluginManager
from core.queue import InMemoryQueuePlugin

# Initialize
plugin_manager = PluginManager()
queue = InMemoryQueuePlugin()
queue.connect()

orchestrator = ProcessingOrchestrator(
    plugin_manager=plugin_manager,
    queue=queue,
    max_retries=3
)

# Start processing
orchestrator.start()

# Monitor
stats = orchestrator.get_statistics()
print(f"Processed: {stats['events_processed']}")
print(f"Failed: {stats['events_failed']}")

# Stop
orchestrator.stop()
```

## Topic Naming Convention

Standard topic names for routing:

```python
from core.models.events import Topics

Topics.RAW_LISTINGS          # "listings.raw"
Topics.NORMALIZED_LISTINGS   # "listings.normalized"
Topics.PROCESSED_LISTINGS    # "listings.processed"
Topics.FRAUD_DETECTED        # "fraud.detected"
Topics.PROCESSING_FAILED     # "processing.failed"
Topics.DEAD_LETTER           # "dead_letter"
```

## Message Flow

### Successful Processing

```
Scraper Plugin
    │
    v
[RAW_LISTINGS] ─────> Processing Orchestrator
                            │
                            ├─> Normalization Plugin
                            ├─> Deduplication Plugin
                            ├─> Fraud Detection Plugin
                            │
                            v
                      [PROCESSED_LISTINGS] ─────> Storage/Index
```

### Failed Processing

```
[RAW_LISTINGS] ─────> Processing Orchestrator
                            │
                            X (Error)
                            │
                     Retry Count < Max?
                      /          \
                    Yes           No
                     │             │
                     v             v
              [RAW_LISTINGS]  [PROCESSING_FAILED]
              (retry_count++)       │
                                    v
                              Dead Letter Queue
```

## Error Handling

### Retry Strategy

1. **Transient Errors** - Automatically retried:
   - Network timeouts
   - Temporary service unavailability
   - Rate limiting

2. **Permanent Errors** - Sent to failed queue:
   - Validation errors
   - Data corruption
   - Plugin crashes

### Retry Configuration

```python
orchestrator = ProcessingOrchestrator(
    plugin_manager=plugin_manager,
    queue=queue,
    max_retries=3  # Retry up to 3 times before giving up
)
```

### Dead Letter Queue

Failed messages (after max retries) are:
1. Published to `processing.failed` topic
2. Stored in dead letter queue
3. Include full error details and original event
4. Can be manually reviewed and reprocessed

## Observability

### Tracing Integration

Events propagate tracing context from request tracing (#20):

```python
# Trace context flows through events
raw_event = RawListingEvent(
    metadata=EventMetadata(
        trace_id="trace-123",      # From incoming request
        request_id="req-456",       # From incoming request
        event_id="event-789"        # New event ID
    ),
    ...
)

# Child events maintain trace context
normalized_event = NormalizedListingEvent(
    metadata=EventMetadata(
        trace_id="trace-123",           # Same trace
        request_id="req-456",            # Same request
        parent_event_id="event-789",     # Parent event
        event_id="event-abc"             # New child event
    ),
    ...
)
```

This enables:
- End-to-end request tracing
- Distributed transaction tracking
- Performance profiling across services
- Error correlation

### Health Checks

Both queue and orchestrator provide health check endpoints:

```python
# Queue health
health = queue.health_check()
# {
#     "status": "healthy",
#     "connected": true,
#     "latency_ms": 2.5,
#     "details": {
#         "active_workers": 3,
#         "statistics": {...}
#     }
# }

# Orchestrator health
health = orchestrator.health_check()
# {
#     "status": "healthy",
#     "running": true,
#     "queue_health": {...},
#     "statistics": {...}
# }
```

### Statistics

Track processing metrics:

```python
stats = orchestrator.get_statistics()
# {
#     "events_processed": 1523,
#     "events_failed": 12,
#     "total_processing_time_ms": 45230.5,
#     "avg_processing_time_ms": 29.7,
#     "plugins_executed": 4569
# }

queue_stats = queue.get_statistics()
# {
#     "messages_published": 1535,
#     "messages_consumed": 1523,
#     "messages_acked": 1511,
#     "messages_rejected": 12,
#     "active_subscriptions": 3,
#     "errors": 0
# }
```

## Best Practices

### 1. Message Design

- **Keep messages small** - Large payloads slow down queue
- **Use references** - Store large data elsewhere, pass IDs
- **Include context** - Add enough metadata for processing
- **Version events** - Include schema version for compatibility

### 2. Error Handling

- **Idempotent processing** - Handle duplicate messages gracefully
- **Explicit retries** - Use retry_count to prevent infinite loops
- **Log failures** - Include full context for debugging
- **Monitor DLQ** - Set up alerts for dead letter queue growth

### 3. Performance

- **Batch where possible** - Process multiple messages together
- **Parallel subscriptions** - Scale with multiple workers
- **Tune block_ms** - Balance latency vs CPU usage (Redis)
- **Monitor queue depth** - Prevent backlog growth

### 4. Testing

- **Use InMemory queue** - Fast, isolated tests
- **Mock plugin manager** - Control plugin behavior
- **Test error paths** - Verify retry and DLQ logic
- **Integration tests** - Validate end-to-end flow

### 5. Production Deployment

- **Use Redis queue** - Persistence and distribution
- **Multiple workers** - Scale horizontally with consumer groups
- **Health monitoring** - Regular health checks and alerting
- **Backup strategy** - Redis persistence configuration
- **Capacity planning** - Monitor queue depth and processing rate

## Configuration Examples

### Development

```python
# Use in-memory queue
queue = InMemoryQueuePlugin()
queue.connect()

orchestrator = ProcessingOrchestrator(
    plugin_manager=plugin_manager,
    queue=queue,
    max_retries=1  # Fast failure in dev
)
```

### Production

```python
# Use Redis with consumer group
queue = RedisQueuePlugin(
    host="redis.prod.example.com",
    port=6379,
    password=os.getenv("REDIS_PASSWORD"),
    consumer_group="processors",
    consumer_name=f"worker-{os.getpid()}",
    max_pending=5000,
    block_ms=5000
)
queue.connect()

orchestrator = ProcessingOrchestrator(
    plugin_manager=plugin_manager,
    queue=queue,
    max_retries=3,
    enable_parallel=False  # Sequential for now
)
```

## Troubleshooting

### Queue Connection Issues

```python
# Check connection
if not queue.is_connected():
    queue.connect()

# Verify health
health = queue.health_check()
if health["status"] != "healthy":
    logger.error(f"Queue unhealthy: {health}")
```

### Message Processing Failures

1. Check orchestrator logs for errors
2. Review dead letter queue (`processing.failed` topic)
3. Verify plugin configurations
4. Check resource availability (CPU, memory)

### High Queue Depth

1. Check processing rate: `stats['events_processed']`
2. Scale up workers (add more consumer instances)
3. Optimize plugin performance
4. Review retry configuration (too aggressive?)

### Redis Specific Issues

- **Connection timeouts**: Increase `block_ms`
- **Consumer lag**: Check `max_pending` vs actual pending
- **Memory issues**: Monitor Redis memory usage
- **Redelivery storms**: Verify acknowledgment logic

## Future Enhancements

Planned improvements (see CORE_DEVELOPMENT_PLAN.md):

1. **Parallel processing** - Execute independent plugins concurrently
2. **Priority queues** - Process high-priority listings first
3. **Message batching** - Process multiple messages together
4. **Circuit breakers** - Prevent cascade failures
5. **Metrics integration** - OpenTelemetry metrics (Issue #100)
6. **Message schemas** - Enforce event format validation
7. **Compression** - Reduce message size for large payloads

## Related Documentation

- [Plugin Development](PLUGIN_DEVELOPMENT.md) - Creating processing plugins
- [Unified Data Model](UNIFIED_DATA_MODEL.md) - Standard listing format
- [Architecture Overview](../ARCHITECTURE.md) - System design
- [Core Development Plan](CORE_DEVELOPMENT_PLAN.md) - Roadmap

## See Also

- Queue Plugin Interface: `core/interfaces/queue_plugin.py`
- Event Models: `core/models/events.py`
- Processing Orchestrator: `core/pipeline/orchestrator.py`
- Tests: `tests/unit/test_queue_plugin.py`
