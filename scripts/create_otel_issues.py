#!/usr/bin/env python3
"""
Script to create GitHub Issues for OpenTelemetry integration tasks.
Creates issues for tasks 3.4-3.8 from CORE_DEVELOPMENT_PLAN.md
"""

import os
import subprocess
import sys
from typing import Dict, List

# OpenTelemetry integration issues
OTEL_ISSUES = [
    {
        "title": "[Core] OpenTelemetry base integration with auto-instrumentation",
        "labels": ["core", "observability", "opentelemetry", "phase:B", "priority:high"],
        "body": """## Overview
Integrate OpenTelemetry with automatic instrumentation for FastAPI, PostgreSQL, Redis, and HTTP clients to enable distributed tracing across the system.

## Related Task
**Task ID**: 3.4
**Dependencies**: #19 (Structured logging), #20 (Request tracing)
**Sprint**: S2 (Phase B)

## Acceptance Criteria
- [x] OpenTelemetry SDK installed and configured
- [x] Auto-instrumentation for FastAPI (HTTP requests/responses)
- [x] Auto-instrumentation for PostgreSQL (database queries)
- [x] Auto-instrumentation for Redis (cache operations)
- [x] Auto-instrumentation for HTTP clients (requests/httpx)
- [x] OTLP exporter configured for Jaeger
- [x] W3C Trace Context propagation enabled
- [x] Traces visible in Jaeger UI locally
- [x] Documentation with setup instructions

## Implementation Details

### 1. Dependencies
```python
# Add to requirements.txt
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-instrumentation-fastapi==0.42b0
opentelemetry-instrumentation-sqlalchemy==0.42b0
opentelemetry-instrumentation-redis==0.42b0
opentelemetry-instrumentation-requests==0.42b0
opentelemetry-instrumentation-httpx==0.42b0
opentelemetry-exporter-otlp==1.21.0
```

### 2. Configuration Module (`core/utils/telemetry.py`)
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

def configure_opentelemetry(
    service_name: str = "real-estates-anti-fraud",
    service_version: str = "0.1.0",
    otlp_endpoint: str = "http://localhost:4317"
):
    \"\"\"Configure OpenTelemetry with auto-instrumentation\"\"\"

    # Create resource
    resource = Resource(attributes={
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
    })

    # Configure tracer provider
    provider = TracerProvider(resource=resource)

    # Add OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Enable auto-instrumentation
    FastAPIInstrumentor.instrument()
    SQLAlchemyInstrumentor().instrument()
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()
```

### 3. FastAPI Integration (`core/api/main.py`)
```python
from core.utils.telemetry import configure_opentelemetry

# Configure OpenTelemetry before creating FastAPI app
if os.getenv("OTEL_ENABLED", "true").lower() == "true":
    configure_opentelemetry(
        service_name=os.getenv("OTEL_SERVICE_NAME", "real-estates-anti-fraud"),
        service_version=os.getenv("OTEL_SERVICE_VERSION", "0.1.0"),
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )

app = FastAPI(title="RealEstatesAntiFraud Core API")
```

### 4. Environment Variables
```bash
# .env
OTEL_ENABLED=true
OTEL_SERVICE_NAME=real-estates-anti-fraud
OTEL_SERVICE_VERSION=0.1.0
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=0.1  # 10% sampling in production
```

### 5. Docker Compose for Jaeger
```yaml
# docker-compose.jaeger.yml
version: '3.8'

services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "4317:4317"    # OTLP gRPC
      - "4318:4318"    # OTLP HTTP
    environment:
      - COLLECTOR_OTLP_ENABLED=true
```

### 6. Testing
- Create integration test with FastAPI TestClient
- Verify traces are exported (use InMemorySpanExporter for tests)
- Test trace context propagation across HTTP calls
- Verify trace_id matches request_id from #20

## Documentation
- Create `docs/OPENTELEMETRY.md` with:
  - Architecture overview
  - Setup instructions
  - Configuration options
  - Jaeger deployment
  - Best practices
  - Troubleshooting

## Testing Checklist
- [ ] Unit tests for telemetry configuration
- [ ] Integration tests with FastAPI endpoints
- [ ] Manual testing with Jaeger UI
- [ ] Verify trace_id correlation with logs (#20)
- [ ] Performance impact measurement (< 5% overhead)

## Success Metrics
- Traces visible in Jaeger for all HTTP requests
- Database queries appear as child spans
- End-to-end latency tracking works
- Trace context propagates correctly
- Zero application errors from OTel

## References
- OpenTelemetry Python: https://opentelemetry.io/docs/instrumentation/python/
- FastAPI Instrumentation: https://opentelemetry-python-contrib.readthedocs.io/en/latest/instrumentation/fastapi/fastapi.html
- OTLP Specification: https://opentelemetry.io/docs/specs/otlp/
""",
        "assignees": [],
        "milestone": None,  # Will be set to "Phase B" later
    },
    {
        "title": "[Core] OpenTelemetry custom spans for plugins and fraud detection",
        "labels": ["core", "observability", "opentelemetry", "phase:B", "priority:high"],
        "body": """## Overview
Add custom OpenTelemetry spans for plugin execution, fraud detection, and other business-critical operations to enable detailed distributed tracing.

## Related Task
**Task ID**: 3.5
**Dependencies**: Task 3.4 (Base OTel integration)
**Sprint**: S2 (Phase B)

## Acceptance Criteria
- [x] Custom spans for plugin lifecycle (load, enable, disable, execute)
- [x] Custom spans for fraud detection operations
- [x] Custom spans for processing pipeline stages
- [x] Span attributes include relevant context (plugin_id, fraud_score, etc.)
- [x] Nested spans for multi-stage operations
- [x] Error handling and span status recording
- [x] Documentation with examples
- [x] Unit tests for span creation

## Implementation Details

### 1. Tracer Setup (`core/utils/telemetry.py`)
```python
from opentelemetry import trace

def get_tracer(name: str = __name__):
    \"\"\"Get tracer for creating custom spans\"\"\"
    return trace.get_tracer(name, version="0.1.0")
```

### 2. Plugin Manager Instrumentation (`core/plugin_manager.py`)
```python
from core.utils.telemetry import get_tracer
from opentelemetry.trace import Status, StatusCode

tracer = get_tracer(__name__)

class PluginManager:
    def register(self, plugin: PluginMetadata):
        with tracer.start_as_current_span("plugin.register") as span:
            span.set_attribute("plugin.id", plugin.id)
            span.set_attribute("plugin.type", plugin.type)
            span.set_attribute("plugin.version", plugin.version)

            try:
                # Registration logic
                ...
                span.set_status(Status(StatusCode.OK))
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise

    def execute_plugin(self, plugin_id: str, data: dict):
        with tracer.start_as_current_span("plugin.execute") as span:
            span.set_attribute("plugin.id", plugin_id)
            span.set_attribute("data.size", len(str(data)))

            # Execution logic
            result = self._run_plugin(plugin_id, data)

            span.set_attribute("result.status", result.get("status"))
            return result
```

### 3. Fraud Detection Instrumentation
```python
# core/fraud/detector.py
from core.utils.telemetry import get_tracer

tracer = get_tracer(__name__)

class FraudDetector:
    def analyze(self, listing: dict):
        with tracer.start_as_current_span("fraud_detection.analyze") as span:
            span.set_attribute("listing.id", listing["id"])

            # Run detection plugins
            signals = []
            for plugin in self.plugins:
                with tracer.start_as_current_span(f"fraud_detection.plugin.{plugin.id}") as plugin_span:
                    plugin_span.set_attribute("plugin.id", plugin.id)
                    plugin_span.set_attribute("plugin.weight", plugin.weight)

                    signal = plugin.analyze(listing)
                    plugin_span.set_attribute("signal.confidence", signal["confidence"])
                    signals.append(signal)

            # Calculate fraud score
            fraud_score = self._aggregate_signals(signals)
            span.set_attribute("fraud_score", fraud_score)
            span.set_attribute("risk_level", self._get_risk_level(fraud_score))

            return {"fraud_score": fraud_score, "signals": signals}
```

### 4. Processing Pipeline Instrumentation
```python
# core/pipeline/orchestrator.py
from core.utils.telemetry import get_tracer

tracer = get_tracer(__name__)

class ProcessingOrchestrator:
    def process(self, listing: dict):
        with tracer.start_as_current_span("pipeline.process") as span:
            span.set_attribute("listing.id", listing["id"])
            span.set_attribute("pipeline.stages", len(self.stages))

            for stage in self.stages:
                with tracer.start_as_current_span(f"pipeline.stage.{stage.name}") as stage_span:
                    stage_span.set_attribute("stage.name", stage.name)
                    stage_span.set_attribute("stage.priority", stage.priority)

                    listing = stage.process(listing)
                    stage_span.set_attribute("stage.status", "completed")

            span.set_status(Status(StatusCode.OK))
            return listing
```

### 5. Helper Decorators
```python
# core/utils/telemetry.py
from functools import wraps

def trace_operation(operation_name: str, attributes: dict = None):
    \"\"\"Decorator to trace function execution\"\"\"
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer(func.__module__)
            with tracer.start_as_current_span(operation_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator

# Usage
@trace_operation("listing.normalize", {"service": "normalizer"})
def normalize_listing(listing: dict) -> dict:
    # Normalization logic
    ...
```

## Testing
- [ ] Unit tests for custom span creation
- [ ] Integration tests for nested spans
- [ ] Verify span attributes are correct
- [ ] Test error handling and exception recording
- [ ] Verify performance impact (< 2% overhead)

## Documentation
- Update `docs/OPENTELEMETRY.md` with:
  - Custom span creation guide
  - Best practices for instrumentation
  - Span naming conventions
  - Attribute naming conventions

## Success Metrics
- Custom spans visible in Jaeger
- Nested span hierarchy correct
- Span attributes provide useful context
- Error tracking works correctly
- Performance overhead acceptable

## References
- OTel Tracing API: https://opentelemetry.io/docs/instrumentation/python/manual/
- Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/
""",
        "assignees": [],
        "milestone": None,
    },
    {
        "title": "[Core] OpenTelemetry custom metrics instrumentation",
        "labels": ["core", "observability", "opentelemetry", "metrics", "phase:C", "priority:medium"],
        "body": """## Overview
Add custom OpenTelemetry metrics for monitoring plugin performance, fraud detection accuracy, and system health.

## Related Task
**Task ID**: 3.6
**Dependencies**: Task 3.4 (Base OTel integration)
**Sprint**: S3 (Phase C)

## Acceptance Criteria
- [x] Metrics provider configured with OTLP exporter
- [x] Custom metrics for plugin execution time
- [x] Custom metrics for fraud detection (accuracy, false positives)
- [x] Custom metrics for pipeline processing (throughput, latency)
- [x] Custom metrics for scraping operations
- [x] Metrics visible in Prometheus/Grafana
- [x] Documentation with metric definitions
- [x] Unit tests for metric recording

## Implementation Details

### 1. Metrics Setup (`core/utils/telemetry.py`)
```python
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

def configure_metrics(
    service_name: str = "real-estates-anti-fraud",
    otlp_endpoint: str = "http://localhost:4317"
):
    \"\"\"Configure OpenTelemetry metrics\"\"\"

    # Create OTLP metric exporter
    metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)

    # Create metric reader with 60s export interval
    metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=60000)

    # Create and set meter provider
    meter_provider = MeterProvider(metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

def get_meter(name: str = __name__):
    \"\"\"Get meter for creating custom metrics\"\"\"
    return metrics.get_meter(name, version="0.1.0")
```

### 2. Plugin Metrics (`core/metrics/plugin_metrics.py`)
```python
from core.utils.telemetry import get_meter

meter = get_meter(__name__)

# Plugin execution time histogram
plugin_execution_time = meter.create_histogram(
    name="plugin.execution.duration",
    description="Plugin execution duration in seconds",
    unit="s"
)

# Plugin execution counter
plugin_executions = meter.create_counter(
    name="plugin.executions.total",
    description="Total number of plugin executions"
)

# Plugin errors counter
plugin_errors = meter.create_counter(
    name="plugin.errors.total",
    description="Total number of plugin errors"
)

# Active plugins gauge
active_plugins = meter.create_up_down_counter(
    name="plugin.active.count",
    description="Number of active plugins"
)

# Usage in PluginManager
class PluginManager:
    def execute_plugin(self, plugin_id: str, data: dict):
        start_time = time.time()
        try:
            result = self._run_plugin(plugin_id, data)

            # Record metrics
            plugin_executions.add(1, {"plugin.id": plugin_id, "status": "success"})
            plugin_execution_time.record(
                time.time() - start_time,
                {"plugin.id": plugin_id, "plugin.type": self.get_type(plugin_id)}
            )
            return result
        except Exception as e:
            plugin_errors.add(1, {"plugin.id": plugin_id, "error.type": type(e).__name__})
            raise
```

### 3. Fraud Detection Metrics (`core/metrics/fraud_metrics.py`)
```python
from core.utils.telemetry import get_meter

meter = get_meter(__name__)

# Fraud score histogram
fraud_score_distribution = meter.create_histogram(
    name="fraud_detection.score.distribution",
    description="Distribution of fraud scores",
    unit="score"
)

# Fraud classifications counter
fraud_classifications = meter.create_counter(
    name="fraud_detection.classifications.total",
    description="Total fraud classifications by risk level"
)

# Detection accuracy gauge (requires ground truth)
detection_accuracy = meter.create_gauge(
    name="fraud_detection.accuracy",
    description="Fraud detection accuracy"
)

# False positive rate
false_positive_rate = meter.create_gauge(
    name="fraud_detection.false_positive_rate",
    description="False positive rate"
)

# Detection latency
detection_latency = meter.create_histogram(
    name="fraud_detection.latency",
    description="Fraud detection latency in seconds",
    unit="s"
)

# Usage
def analyze_listing(listing: dict):
    start_time = time.time()

    fraud_score = calculate_fraud_score(listing)
    risk_level = get_risk_level(fraud_score)

    # Record metrics
    fraud_score_distribution.record(fraud_score, {"listing.type": listing["type"]})
    fraud_classifications.add(1, {"risk_level": risk_level})
    detection_latency.record(time.time() - start_time)

    return {"fraud_score": fraud_score, "risk_level": risk_level}
```

### 4. Pipeline Metrics (`core/metrics/pipeline_metrics.py`)
```python
from core.utils.telemetry import get_meter

meter = get_meter(__name__)

# Pipeline throughput
pipeline_throughput = meter.create_counter(
    name="pipeline.listings.processed.total",
    description="Total listings processed through pipeline"
)

# Pipeline latency
pipeline_latency = meter.create_histogram(
    name="pipeline.processing.duration",
    description="Pipeline processing duration in seconds",
    unit="s"
)

# Pipeline errors
pipeline_errors = meter.create_counter(
    name="pipeline.errors.total",
    description="Total pipeline errors by stage"
)

# Queue size gauge
queue_size = meter.create_up_down_counter(
    name="pipeline.queue.size",
    description="Current pipeline queue size"
)
```

### 5. Scraping Metrics (`core/metrics/scraping_metrics.py`)
```python
from core.utils.telemetry import get_meter

meter = get_meter(__name__)

# Listings scraped
listings_scraped = meter.create_counter(
    name="scraping.listings.scraped.total",
    description="Total listings scraped by source"
)

# Scraping errors
scraping_errors = meter.create_counter(
    name="scraping.errors.total",
    description="Total scraping errors by source and error type"
)

# Scraping duration
scraping_duration = meter.create_histogram(
    name="scraping.duration",
    description="Scraping duration in seconds",
    unit="s"
)

# Rate limit hits
rate_limit_hits = meter.create_counter(
    name="scraping.rate_limit_hits.total",
    description="Total rate limit hits by source"
)
```

## Grafana Dashboards
Create dashboards for:
- Plugin performance (execution time, error rate)
- Fraud detection (score distribution, classifications)
- Pipeline health (throughput, latency, queue size)
- Scraping operations (success rate, duration)

## Testing
- [ ] Unit tests for metric recording
- [ ] Integration tests with OTLP exporter
- [ ] Verify metrics in Prometheus
- [ ] Test metric aggregation
- [ ] Performance overhead measurement

## Documentation
- Update `docs/OPENTELEMETRY.md` with:
  - Metric definitions
  - Usage examples
  - Best practices for custom metrics
  - Grafana dashboard setup

## Success Metrics
- All custom metrics visible in Prometheus
- Grafana dashboards functional
- Metric cardinality acceptable (< 10k unique series)
- Performance overhead < 1%

## References
- OTel Metrics API: https://opentelemetry.io/docs/instrumentation/python/manual/#metrics
- Metric Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/general/metrics/
""",
        "assignees": [],
        "milestone": None,
    },
    {
        "title": "[Core] OpenTelemetry logs integration with unified correlation",
        "labels": ["core", "observability", "opentelemetry", "logging", "phase:C", "priority:medium"],
        "body": """## Overview
Integrate OpenTelemetry with structured logging to include trace_id and span_id in all log entries, enabling unified correlation between traces and logs.

## Related Task
**Task ID**: 3.7
**Dependencies**: #19 (Structured logging), #20 (Request tracing), Task 3.4 (Base OTel integration)
**Sprint**: S3 (Phase C)

## Acceptance Criteria
- [x] Logs include trace_id and span_id from OTel context
- [x] LogRecordExporter configured for OTLP
- [x] Log correlation visible in Jaeger/Grafana
- [x] Backward compatibility with existing logging (#19)
- [x] Documentation with examples
- [x] Unit tests for log correlation

## Implementation Details

### 1. OTel Logging Setup (`core/utils/telemetry.py`)
```python
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter

def configure_logging(
    service_name: str = "real-estates-anti-fraud",
    otlp_endpoint: str = "http://localhost:4317"
):
    \"\"\"Configure OpenTelemetry logging\"\"\"

    # Create logger provider
    logger_provider = LoggerProvider()

    # Add OTLP log exporter
    log_exporter = OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))

    # Set global logger provider
    set_logger_provider(logger_provider)

    # Create logging handler
    handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

    # Attach to root logger
    logging.getLogger().addHandler(handler)
```

### 2. Enhanced JSONFormatter (`core/utils/logging.py`)
```python
from opentelemetry import trace
from opentelemetry.trace import get_current_span

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Get OTel context
        span = get_current_span()
        span_context = span.get_span_context()

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add OTel trace context
        if span_context.is_valid:
            log_data["trace_id"] = format(span_context.trace_id, "032x")
            log_data["span_id"] = format(span_context.span_id, "016x")
            log_data["trace_flags"] = span_context.trace_flags

        # Add request context (from #20)
        from core.utils.context import get_trace_id, get_request_id
        request_trace_id = get_trace_id()
        request_id = get_request_id()

        if request_trace_id:
            log_data["request_trace_id"] = request_trace_id
        if request_id:
            log_data["request_id"] = request_id

        # Add extra context
        if hasattr(record, "context") and record.context:
            log_data["context"] = record.context

        # Add exception info
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data)
```

### 3. Integration Example
```python
# In any instrumented function
from core.utils.logging import get_logger
from core.utils.telemetry import get_tracer

logger = get_logger(__name__)
tracer = get_tracer(__name__)

def process_listing(listing: dict):
    with tracer.start_as_current_span("process_listing") as span:
        span.set_attribute("listing.id", listing["id"])

        # This log will include trace_id and span_id automatically
        logger.info(
            "Processing listing",
            extra={"context": {"listing_id": listing["id"], "source": listing["source"]}}
        )

        try:
            result = do_processing(listing)
            logger.info("Processing completed successfully")
            return result
        except Exception as e:
            logger.error("Processing failed", exc_info=True)
            span.record_exception(e)
            raise
```

### 4. Log Output Example
```json
{
  "timestamp": "2025-11-28T22:30:45.123456+00:00",
  "level": "INFO",
  "message": "Processing listing",
  "logger": "core.pipeline.processor",
  "module": "processor",
  "function": "process_listing",
  "line": 42,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "trace_flags": 1,
  "request_trace_id": "abc123def456...",
  "request_id": "req789abc123...",
  "context": {
    "listing_id": "12345",
    "source": "cian"
  }
}
```

### 5. Grafana Loki Configuration
```yaml
# docker-compose.loki.yml
version: '3.8'

services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_PATHS_PROVISIONING=/etc/grafana/provisioning
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - ./grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
```

## Testing
- [ ] Unit tests for OTel context in logs
- [ ] Integration tests for log correlation
- [ ] Verify trace_id matches between logs and traces
- [ ] Test log export to OTLP endpoint
- [ ] Performance overhead measurement

## Documentation
- Update `docs/OPENTELEMETRY.md` with:
  - Log correlation setup
  - Grafana Loki integration
  - Query examples (find logs by trace_id)
  - Best practices

## Success Metrics
- All logs include trace context
- Logs correlate with traces in Jaeger
- Grafana can query logs by trace_id
- Performance overhead < 2%

## References
- OTel Logs Bridge API: https://opentelemetry.io/docs/instrumentation/python/logging/
- W3C Trace Context: https://www.w3.org/TR/trace-context/
""",
        "assignees": [],
        "milestone": None,
    },
    {
        "title": "[Core] OpenTelemetry Collector deployment and configuration",
        "labels": ["core", "observability", "opentelemetry", "infrastructure", "phase:C", "priority:medium"],
        "body": """## Overview
Deploy and configure OpenTelemetry Collector to centralize telemetry collection, processing, and export to multiple backends (Jaeger, Prometheus, Grafana Cloud, etc.).

## Related Task
**Task ID**: 3.8
**Dependencies**: Task 3.4-3.7 (OTel integration)
**Sprint**: S3 (Phase C)

## Acceptance Criteria
- [x] OTel Collector deployed (Docker/K8s)
- [x] Receivers configured (OTLP, Prometheus)
- [x] Processors configured (batch, resource detection, tail sampling)
- [x] Exporters configured (Jaeger, Prometheus, Loki, Grafana Cloud)
- [x] Health check and monitoring endpoints
- [x] Documentation with deployment guide
- [x] Production-ready configuration

## Implementation Details

### 1. Collector Configuration (`otel-collector-config.yaml`)
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          scrape_interval: 10s
          static_configs:
            - targets: ['localhost:8888']

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

  resource:
    attributes:
      - key: service.namespace
        value: real-estates-anti-fraud
        action: insert
      - key: deployment.environment
        from_attribute: ENVIRONMENT
        action: insert

  memory_limiter:
    check_interval: 1s
    limit_mib: 512

  tail_sampling:
    decision_wait: 10s
    num_traces: 100
    expected_new_traces_per_sec: 10
    policies:
      - name: error-traces
        type: status_code
        status_code:
          status_codes:
            - ERROR
      - name: high-latency
        type: latency
        latency:
          threshold_ms: 1000
      - name: probabilistic
        type: probabilistic
        probabilistic:
          sampling_percentage: 10

exporters:
  otlp/jaeger:
    endpoint: jaeger:4317
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8889"
    namespace: real_estates
    const_labels:
      env: ${ENVIRONMENT}

  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    labels:
      resource:
        service.name: "service_name"
        service.namespace: "service_namespace"

  logging:
    loglevel: info

  # Optional: Grafana Cloud
  otlp/grafana:
    endpoint: ${GRAFANA_CLOUD_ENDPOINT}
    headers:
      authorization: Basic ${GRAFANA_CLOUD_TOKEN}

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource, tail_sampling]
      exporters: [otlp/jaeger, logging]

    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, batch, resource]
      exporters: [prometheus, logging]

    logs:
      receivers: [otlp]
      processors: [memory_limiter, batch, resource]
      exporters: [loki, logging]

  extensions: [health_check, pprof, zpages]
  telemetry:
    logs:
      level: info
    metrics:
      address: 0.0.0.0:8888

extensions:
  health_check:
    endpoint: 0.0.0.0:13133

  pprof:
    endpoint: 0.0.0.0:1777

  zpages:
    endpoint: 0.0.0.0:55679
```

### 2. Docker Compose (`docker-compose.observability.yml`)
```yaml
version: '3.8'

services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Prometheus metrics
      - "8889:8889"   # Prometheus exporter
      - "13133:13133" # Health check
      - "55679:55679" # ZPages
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-development}
    depends_on:
      - jaeger
      - prometheus
      - loki

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14250:14250"  # gRPC
    environment:
      - COLLECTOR_OTLP_ENABLED=true

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - ./grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
      - ./grafana-dashboards.yml:/etc/grafana/provisioning/dashboards/dashboards.yml
    depends_on:
      - prometheus
      - loki
      - jaeger
```

### 3. Kubernetes Deployment (`k8s/otel-collector.yaml`)
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
data:
  otel-collector-config.yaml: |
    # Same configuration as above

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
spec:
  replicas: 2
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector-contrib:latest
        command: ["--config=/etc/otel-collector-config.yaml"]
        volumeMounts:
        - name: config
          mountPath: /etc/otel-collector-config.yaml
          subPath: otel-collector-config.yaml
        ports:
        - containerPort: 4317
          name: otlp-grpc
        - containerPort: 4318
          name: otlp-http
        - containerPort: 8888
          name: metrics
        - containerPort: 13133
          name: health
        resources:
          limits:
            memory: "1Gi"
            cpu: "1000m"
          requests:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /
            port: 13133
        readinessProbe:
          httpGet:
            path: /
            port: 13133
      volumes:
      - name: config
        configMap:
          name: otel-collector-config

---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector
spec:
  selector:
    app: otel-collector
  ports:
  - name: otlp-grpc
    port: 4317
    targetPort: 4317
  - name: otlp-http
    port: 4318
    targetPort: 4318
  - name: metrics
    port: 8888
    targetPort: 8888
```

### 4. Prometheus Configuration (`prometheus.yml`)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8888']

  - job_name: 'otel-metrics'
    static_configs:
      - targets: ['otel-collector:8889']

  - job_name: 'fastapi'
    static_configs:
      - targets: ['api:8000']
```

### 5. Grafana Datasources (`grafana-datasources.yml`)
```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true

  - name: Jaeger
    type: jaeger
    access: proxy
    url: http://jaeger:16686

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
```

## Monitoring & Alerts

### Collector Health Checks
- `/health_check` - Overall health
- `/metrics` - Collector metrics
- `/debug/pprof` - Performance profiling
- `/debug/zpages` - Internal tracing

### Key Metrics to Monitor
- `otelcol_receiver_accepted_spans` - Spans received
- `otelcol_exporter_sent_spans` - Spans exported
- `otelcol_processor_batch_batch_send_size` - Batch sizes
- `otelcol_exporter_send_failed_spans` - Export failures

## Testing
- [ ] Smoke test with test data
- [ ] Verify data flow to all backends
- [ ] Test tail sampling
- [ ] Test resource limits
- [ ] Load testing with realistic traffic

## Documentation
- Create `docs/OTEL_COLLECTOR.md` with:
  - Architecture overview
  - Deployment guide (Docker/K8s)
  - Configuration options
  - Troubleshooting
  - Scaling recommendations

## Success Metrics
- Collector receives telemetry from all services
- Data exported to all backends correctly
- Health checks pass consistently
- Memory usage stays within limits
- No data loss during normal operations

## References
- OTel Collector: https://opentelemetry.io/docs/collector/
- Configuration: https://opentelemetry.io/docs/collector/configuration/
- Deployment: https://opentelemetry.io/docs/collector/deployment/
""",
        "assignees": [],
        "milestone": None,
    },
]


def create_issue(issue_data: Dict) -> None:
    """Create a single GitHub issue using gh CLI"""
    cmd = ["gh", "issue", "create"]
    cmd.extend(["--title", issue_data["title"]])
    cmd.extend(["--body", issue_data["body"]])

    for label in issue_data["labels"]:
        cmd.extend(["--label", label])

    if issue_data["milestone"]:
        cmd.extend(["--milestone", issue_data["milestone"]])

    for assignee in issue_data["assignees"]:
        cmd.extend(["--assignee", assignee])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issue_url = result.stdout.strip()
        print(f"✅ Created: {issue_data['title']}")
        print(f"   URL: {issue_url}\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create issue: {issue_data['title']}")
        print(f"   Error: {e.stderr}\n")
        sys.exit(1)


def main():
    """Create all OpenTelemetry integration issues"""
    print("🚀 Creating OpenTelemetry Integration GitHub Issues\n")
    print("=" * 70)
    print(f"Total issues to create: {len(OTEL_ISSUES)}\n")

    for i, issue in enumerate(OTEL_ISSUES, 1):
        print(f"[{i}/{len(OTEL_ISSUES)}] Creating issue...")
        create_issue(issue)

    print("=" * 70)
    print(f"\n✅ Successfully created {len(OTEL_ISSUES)} issues!")
    print("\n📋 Summary:")
    print(f"   - Base integration (auto-instrumentation)")
    print(f"   - Custom spans (plugins, fraud detection)")
    print(f"   - Custom metrics (performance, accuracy)")
    print(f"   - Logs integration (unified correlation)")
    print(f"   - Collector deployment (centralized telemetry)")
    print(
        "\n🔗 View all issues: https://github.com/loudmantrade/RealEstatesAntiFraud/issues?q=is%3Aissue+label%3Aopentelemetry"
    )


if __name__ == "__main__":
    main()
