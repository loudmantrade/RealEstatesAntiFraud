#!/usr/bin/env python3
"""
Script to create GitHub Issues from CORE_DEVELOPMENT_PLAN.md
Requires: pip install PyGithub python-dotenv
Usage: 
  1. Create GitHub Personal Access Token with 'repo' scope
  2. Export token: export GITHUB_TOKEN=your_token_here
  3. Run: python scripts/create_github_issues.py
"""

import os
import sys
from github import Github
from github.GithubException import GithubException

# Configuration
REPO_OWNER = "loudmantrade"
REPO_NAME = "RealEstatesAntiFroud"

# Task definitions from CORE_DEVELOPMENT_PLAN.md
TASKS = {
    # Phase A - Sprint 1
    "1.1": {
        "title": "[Core] Design plugin protocol (manifest spec v1)",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Create comprehensive plugin manifest specification document defining the plugin.yaml schema, required fields, and validation rules.

### Acceptance Criteria
- [ ] `PLUGIN_SPEC.md` document created and reviewed
- [ ] Manifest schema includes: metadata, version, dependencies, config schema
- [ ] Examples for each plugin type provided

### Dependencies
- Completed: 0.x (Bootstrap tasks)

### Related
Part of Sprint 1 deliverables
""",
        "labels": ["core", "documentation", "priority:critical", "phase:A"],
    },
    "1.2": {
        "title": "[Core] Implement manifest validation",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Implement JSON Schema validation for plugin.yaml manifest files with comprehensive error messages.

### Acceptance Criteria
- [ ] JSON Schema created for manifest structure
- [ ] `validate_manifest()` function implemented
- [ ] Unit tests for valid/invalid manifests
- [ ] Clear error messages for validation failures

### Dependencies
- #1 (Task 1.1: Plugin protocol spec)

### Related
Part of Sprint 1 deliverables
""",
        "labels": ["core", "validation", "priority:critical", "phase:A"],
    },
    "1.3": {
        "title": "[Core] Dynamic plugin discovery and loading",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Implement filesystem-based plugin discovery that scans plugins/ directory and dynamically loads plugins based on their manifests.

### Acceptance Criteria
- [ ] Plugin discovery scans `plugins/` directory recursively
- [ ] Plugins loaded via manifest validation
- [ ] Hot-drop: new plugin appears after adding to directory
- [ ] Error handling for malformed plugins
- [ ] Tests for discovery and loading process

### Dependencies
- #2 (Task 1.2: Manifest validation)

### Related
Part of Sprint 1 deliverables
""",
        "labels": ["core", "plugin-system", "priority:critical", "phase:A"],
    },
    "2.1": {
        "title": "[Core] Unified configuration system",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Create unified configuration management system for core and plugin settings using YAML files with environment variable overrides.

### Acceptance Criteria
- [ ] `ConfigManager` class implemented
- [ ] Support for YAML config files in `config/` directory
- [ ] Core and plugin config separation
- [ ] Schema validation for configs
- [ ] Unit tests for config loading and validation

### Dependencies
- #1 (Task 1.1: Plugin manifest spec)

### Related
Part of Sprint 1 deliverables
""",
        "labels": ["core", "configuration", "priority:critical", "phase:A"],
    },
    "2.2": {
        "title": "[Core] Environment variable overrides",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Implement environment variable override mechanism for configuration values with proper precedence handling.

### Acceptance Criteria
- [ ] ENV variables override YAML values
- [ ] Naming convention documented (e.g., CORE_DB_HOST)
- [ ] Nested config support via double underscore
- [ ] Tests for override precedence
- [ ] Documentation in README

### Dependencies
- #4 (Task 2.1: Unified config system)

### Related
Part of Sprint 1 deliverables
""",
        "labels": ["core", "configuration", "priority:critical", "phase:A"],
    },
    "4.1": {
        "title": "[Core] PostgreSQL schema for listings",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Design and create PostgreSQL database schema for storing listings based on Unified Data Model.

### Acceptance Criteria
- [ ] `listings` table created with all UDM fields
- [ ] Proper data types and constraints
- [ ] Foreign key relationships defined
- [ ] Created via Alembic migration
- [ ] Schema documentation

### Dependencies
- Completed: 0.9 (In-memory listings API)

### Related
Part of Sprint 1 deliverables, enables persistence
""",
        "labels": ["core", "database", "priority:critical", "phase:A"],
    },
    "4.2": {
        "title": "[Core] Setup Alembic migrations",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Configure Alembic for database migrations management, create initial migration for listings schema.

### Acceptance Criteria
- [ ] Alembic initialized in project
- [ ] Initial migration created for listings table
- [ ] `alembic upgrade head` runs successfully
- [ ] Downgrade migration tested
- [ ] Migration documentation in README

### Dependencies
- #6 (Task 4.1: PostgreSQL schema)

### Related
Part of Sprint 1 deliverables
""",
        "labels": ["core", "database", "migrations", "priority:critical", "phase:A"],
    },
    "4.3": {
        "title": "[Core] Repository pattern for listings",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Implement repository layer for listings CRUD operations with pagination, replacing in-memory storage.

### Acceptance Criteria
- [ ] `ListingRepository` class with CRUD methods
- [ ] Pagination support (limit/offset)
- [ ] SQLAlchemy ORM models
- [ ] Unit tests for all repository methods
- [ ] Integration tests with test database

### Dependencies
- #7 (Task 4.2: Alembic setup)

### Related
Part of Sprint 1 deliverables
""",
        "labels": ["core", "database", "repository", "priority:critical", "phase:A"],
    },
    "5.1": {
        "title": "[Core] Message queue abstraction layer",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Create unified interface for message queue operations supporting both Kafka and RabbitMQ implementations.

### Acceptance Criteria
- [ ] Abstract `MessageQueue` interface
- [ ] `Producer` and `Consumer` base classes
- [ ] Factory pattern for queue creation
- [ ] Basic Kafka implementation
- [ ] RabbitMQ implementation (optional)
- [ ] Unit tests with mocks

### Dependencies
- #3 (Task 1.3: Dynamic plugin loading)

### Related
Part of Sprint 1 deliverables, enables ETL pipeline
""",
        "labels": ["core", "messaging", "architecture", "priority:critical", "phase:A"],
    },
    "5.2": {
        "title": "[Core] Define raw listing event format",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S1

### Description
Define standardized message format for raw listing events in the processing pipeline with JSON Schema.

### Acceptance Criteria
- [ ] JSON Schema for `raw_listing_event` message
- [ ] Event includes: listing data, metadata, trace_id
- [ ] Serialization/deserialization helpers
- [ ] Versioning support (v1)
- [ ] Documentation with examples
- [ ] Tests for serialization

### Dependencies
- #9 (Task 5.1: Queue abstraction)

### Related
Part of Sprint 1 deliverables
""",
        "labels": ["core", "data-model", "messaging", "priority:critical", "phase:A"],
    },
    "5.3": {
        "title": "[Core] Processing pipeline orchestrator",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Implement orchestrator that executes processing plugins in priority order for each listing.

### Acceptance Criteria
- [ ] `ProcessingOrchestrator` class
- [ ] Executes plugins by priority (ascending)
- [ ] Error handling and retry logic
- [ ] Logging for each processing step
- [ ] Integration tests with mock plugins
- [ ] Metrics for processing time

### Dependencies
- #10 (Task 5.2: Event format)

### Related
Part of Sprint 2 deliverables, core ETL component
""",
        "labels": ["core", "pipeline", "orchestration", "priority:critical", "phase:A"],
    },
    "6.1": {
        "title": "[Core] Risk scoring orchestrator interface",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Create orchestrator for fraud detection plugins that aggregates risk signals and computes final fraud score.

### Acceptance Criteria
- [ ] `RiskScoringOrchestrator` class
- [ ] `run(listing)` method returns fraud_score
- [ ] Aggregates signals from all detection plugins
- [ ] Weighted scoring formula implemented
- [ ] Unit tests with mock detection plugins

### Dependencies
- Completed: 0.6 (Plugin manager)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "fraud-detection", "orchestration", "priority:critical", "phase:A"],
    },
    "6.2": {
        "title": "[Core] Detection plugins registry integration",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Connect detection plugins to risk scoring orchestrator with metadata and enable/disable capabilities.

### Acceptance Criteria
- [ ] List active detection plugins via plugin manager
- [ ] Plugin weights configurable
- [ ] Enable/disable affects scoring
- [ ] Tests for plugin activation states

### Dependencies
- #12 (Task 6.1: Risk scoring orchestrator)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "fraud-detection", "plugin-system", "priority:critical", "phase:A"],
    },
    "6.3": {
        "title": "[Core] Fraud score aggregation formula",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Implement weighted aggregation formula for fraud signals as specified in architecture.

### Acceptance Criteria
- [ ] Formula matches architecture specification
- [ ] Weights normalized correctly
- [ ] Risk level classification (safe/suspicious/fraud)
- [ ] Edge cases handled (no plugins, all plugins disabled)
- [ ] Unit tests for scoring scenarios
- [ ] Performance benchmarks

### Dependencies
- #13 (Task 6.2: Detection plugins registry)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "fraud-detection", "algorithm", "priority:critical", "phase:A"],
    },
    "8.1": {
        "title": "[Core] API versioning (v1 prefix)",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Implement API versioning by moving all routes under `/api/v1/` prefix for future compatibility.

### Acceptance Criteria
- [ ] All routes prefixed with `/api/v1/`
- [ ] Health endpoint remains at `/health`
- [ ] Documentation updated
- [ ] Tests updated for new paths
- [ ] Version strategy documented

### Dependencies
- Completed: 0.7 (FastAPI app)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "api", "versioning", "priority:critical", "phase:A"],
    },
    "8.4": {
        "title": "[Core] Listings API pagination and filters",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Add pagination (limit/offset) and filtering capabilities to listings endpoints.

### Acceptance Criteria
- [ ] Query parameters: limit, offset, sort
- [ ] Filters: price_min, price_max, location, type
- [ ] Response includes pagination metadata (total, pages)
- [ ] Tests for pagination edge cases
- [ ] Performance tested with large datasets

### Dependencies
- #8 (Task 4.3: Repository layer)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "api", "features", "priority:critical", "phase:A"],
    },
    "11.1": {
        "title": "[Core] GitHub Actions CI pipeline",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Setup GitHub Actions workflow for continuous integration with tests and linting.

### Acceptance Criteria
- [ ] `.github/workflows/ci.yml` created
- [ ] Runs on push and PR
- [ ] Executes: pytest, flake8, black, mypy
- [ ] Matrix for multiple Python versions (3.11, 3.12, 3.13)
- [ ] Coverage report uploaded
- [ ] Badge added to README

### Dependencies
- Completed: 10.1 (Unit tests)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "ci-cd", "automation", "priority:critical", "phase:A"],
    },
    "11.2": {
        "title": "[Core] Docker image build",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Create optimized Dockerfile for core API service with multi-stage build.

### Acceptance Criteria
- [ ] Multi-stage Dockerfile (build + runtime)
- [ ] Image size optimized (<200MB)
- [ ] Non-root user
- [ ] Health check configured
- [ ] docker-compose.yml for local dev
- [ ] Build succeeds in CI

### Dependencies
- #18 (Task 11.1: CI pipeline)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "docker", "deployment", "priority:critical", "phase:A"],
    },
    "3.1": {
        "title": "[Core] Structured JSON logging",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Implement structured logging system with JSON output for better observability.

### Acceptance Criteria
- [ ] Logger available via `core.utils.logging`
- [ ] JSON format for all log entries
- [ ] Standard fields: timestamp, level, message, context
- [ ] Configurable log levels
- [ ] Tests for logger functionality

### Dependencies
- Completed: 0.x (Bootstrap)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "logging", "observability", "priority:critical", "phase:A"],
    },
    "3.2": {
        "title": "[Core] Request tracing with correlation IDs",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S2

### Description
Add middleware for correlation IDs (trace_id, request_id) to track requests across services.

### Acceptance Criteria
- [ ] Middleware generates/propagates trace_id
- [ ] All logs include trace_id
- [ ] HTTP headers: X-Trace-ID, X-Request-ID
- [ ] Works with message queue events
- [ ] Tests for ID propagation

### Dependencies
- #20 (Task 3.1: Structured logging)

### Related
Part of Sprint 2 deliverables
""",
        "labels": ["core", "observability", "tracing", "priority:critical", "phase:A"],
    },
    "7.1": {
        "title": "[Core] Index manager for search plugins",
        "body": """**Priority:** P1 (Critical)
**Phase:** B - Functional Enrichment
**Sprint:** S3

### Description
Create index manager that routes indexing and search requests to appropriate search plugins.

### Acceptance Criteria
- [ ] `IndexManager` class with index()/search() methods
- [ ] Routes to active search plugins
- [ ] Fallback strategy if primary search fails
- [ ] Unit tests with mock search plugins

### Dependencies
- Completed: 0.6 (Plugin manager)

### Related
Part of Sprint 3 deliverables
""",
        "labels": ["core", "search", "plugin-system", "priority:critical", "phase:B"],
    },
    "7.2": {
        "title": "[Core] Auto-indexing after processing",
        "body": """**Priority:** P1 (Critical)
**Phase:** B - Functional Enrichment
**Sprint:** S3

### Description
Integrate index manager with processing pipeline to automatically index listings after finalization.

### Acceptance Criteria
- [ ] Index called after pipeline completion
- [ ] Error handling for indexing failures
- [ ] Retry logic for transient errors
- [ ] Tests for indexing flow

### Dependencies
- #11 (Task 5.3: Processing orchestrator)
- #23 (Task 7.1: Index manager)

### Related
Part of Sprint 3 deliverables
""",
        "labels": ["core", "search", "pipeline", "priority:critical", "phase:B"],
    },
    "10.1": {
        "title": "[Core] Expand unit test coverage to ≥70%",
        "body": """**Priority:** P1 (Critical)
**Phase:** A - Technical Foundation
**Sprint:** S3

### Description
Write comprehensive unit tests for all core modules to achieve at least 70% code coverage.

### Acceptance Criteria
- [ ] Coverage ≥ 70% for core package
- [ ] All critical paths tested
- [ ] Edge cases covered
- [ ] Coverage report generated in CI
- [ ] Coverage badge in README

### Dependencies
- Completed: 0.x (Bootstrap tests)

### Related
Part of Sprint 3 deliverables, quality gate
""",
        "labels": ["core", "testing", "quality", "priority:critical", "phase:A"],
    },
    "1.5": {
        "title": "[Core] Plugin dependency graph",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment
**Sprint:** S4

### Description
Implement dependency resolution for plugins using DAG with cycle detection.

### Acceptance Criteria
- [ ] DAG computed from plugin dependencies
- [ ] Cycle detection prevents registration
- [ ] Load order determined by dependencies
- [ ] Visualization of dependency graph
- [ ] Tests for various dependency scenarios

### Dependencies
- #2 (Task 1.2: Manifest validation)

### Related
Part of Sprint 4 deliverables
""",
        "labels": ["core", "plugin-system", "algorithm", "priority:important", "phase:B"],
    },
    "1.6": {
        "title": "[Core] Semver version compatibility",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment
**Sprint:** S4

### Description
Implement semantic versioning checks for plugin compatibility with core and dependencies.

### Acceptance Criteria
- [ ] Semver constraint parsing
- [ ] Version compatibility validation
- [ ] Rejection of incompatible versions
- [ ] Clear error messages
- [ ] Tests for version scenarios

### Dependencies
- #26 (Task 1.5: Dependency graph)

### Related
Part of Sprint 4 deliverables
""",
        "labels": ["core", "plugin-system", "versioning", "priority:important", "phase:B"],
    },
    "5.6": {
        "title": "[Core] Processing state logging",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment
**Sprint:** S4

### Description
Add processing_log table to track each processing step with timestamps for debugging and auditing.

### Acceptance Criteria
- [ ] `processing_log` table with listing_id, plugin_id, status, timestamp
- [ ] Log entries created for each plugin execution
- [ ] Queryable via API for debugging
- [ ] Migration created
- [ ] Tests for log persistence

### Dependencies
- #11 (Task 5.3: Processing orchestrator)

### Related
Part of Sprint 4 deliverables
""",
        "labels": ["core", "pipeline", "logging", "database", "priority:important", "phase:B"],
    },
    "9.1": {
        "title": "[Core] Input validation security audit",
        "body": """**Priority:** P1 (Critical)
**Phase:** B - Functional Enrichment
**Sprint:** S4

### Description
Comprehensive security audit of all API endpoints and input validation points.

### Acceptance Criteria
- [ ] All endpoints reviewed for input validation
- [ ] Pydantic models cover all inputs
- [ ] Report documenting findings
- [ ] No critical validation gaps
- [ ] Recommendations implemented

### Dependencies
- #15 (Task 8.1: API versioning)

### Related
Part of Sprint 4 deliverables, security critical
""",
        "labels": ["core", "security", "audit", "priority:critical", "phase:B"],
    },
    "9.2": {
        "title": "[Core] SQL injection protection audit",
        "body": """**Priority:** P1 (Critical)
**Phase:** B - Functional Enrichment
**Sprint:** S4

### Description
Audit all database queries to ensure no SQL injection vulnerabilities exist.

### Acceptance Criteria
- [ ] All queries use ORM or parameterized statements
- [ ] No raw SQL concatenation found
- [ ] Dynamic filters validated
- [ ] Code review checklist created
- [ ] Automated scanner (bandit) configured

### Dependencies
- #8 (Task 4.3: Repository layer)

### Related
Part of Sprint 4 deliverables, security critical
""",
        "labels": ["core", "security", "database", "priority:critical", "phase:B"],
    },
    "13.1": {
        "title": "[Core] API documentation examples",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment
**Sprint:** S4

### Description
Enhance OpenAPI documentation with comprehensive examples for all key endpoints.

### Acceptance Criteria
- [ ] Request/response examples for all CRUD operations
- [ ] Error response examples
- [ ] Query parameter examples
- [ ] Authentication examples (when implemented)
- [ ] Rendered in Swagger UI

### Dependencies
- #17 (Task 8.7: OpenAPI extensions) or #15 (Task 8.1: API versioning)

### Related
Part of Sprint 4 deliverables
""",
        "labels": ["core", "documentation", "api", "priority:important", "phase:B"],
    },
    "13.2": {
        "title": "[Core] Developer guide documentation",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment
**Sprint:** S4

### Description
Create comprehensive developer guide for core system development and contribution.

### Acceptance Criteria
- [ ] `CORE_DEVELOPER_GUIDE.md` created
- [ ] Architecture overview
- [ ] Setup instructions
- [ ] Code organization explained
- [ ] Contribution guidelines
- [ ] Testing strategies

### Dependencies
- #3 (Task 1.3: Dynamic loading) and other core features

### Related
Part of Sprint 4 deliverables
""",
        "labels": ["core", "documentation", "priority:important", "phase:B"],
    },
}

# Additional important tasks for later phases
ADDITIONAL_TASKS = {
    "1.4": {
        "title": "[Core] Hot reload for plugin updates",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment

### Description
Implement hot reload capability for updating plugins without restarting the core service.

### Acceptance Criteria
- [ ] API endpoint `/api/v1/plugins/{id}/reload`
- [ ] Plugin metadata updated without restart
- [ ] Active instances gracefully transitioned
- [ ] Tests for reload scenarios
- [ ] Documentation for reload process

### Dependencies
- #3 (Task 1.3: Dynamic plugin loading)
""",
        "labels": ["core", "plugin-system", "priority:important", "phase:B"],
    },
    "1.8": {
        "title": "[Core] Plugin lifecycle hooks",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment

### Description
Add lifecycle hooks (on_enable, on_disable, on_remove) that plugins can implement.

### Acceptance Criteria
- [ ] Hook methods defined in plugin interfaces
- [ ] Called at appropriate lifecycle points
- [ ] Error handling for hook failures
- [ ] Tests with mock plugins implementing hooks
- [ ] Documentation for plugin authors

### Dependencies
- #3 (Task 1.3: Dynamic loading)
""",
        "labels": ["core", "plugin-system", "priority:important", "phase:B"],
    },
    "1.9": {
        "title": "[Core] Persist plugin registry to PostgreSQL",
        "body": """**Priority:** P1 (Critical)
**Phase:** B - Functional Enrichment

### Description
Replace in-memory plugin registry with PostgreSQL persistence to maintain state across restarts.

### Acceptance Criteria
- [ ] `plugins` table with metadata and enabled state
- [ ] Migration created
- [ ] PluginManager uses database
- [ ] State preserved across restarts
- [ ] Tests for persistence

### Dependencies
- Completed: 0.6 (Plugin manager)
- #7 (Task 4.2: Alembic setup)
""",
        "labels": ["core", "plugin-system", "database", "priority:critical", "phase:B"],
    },
    "2.3": {
        "title": "[Core] Secure secrets management",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment

### Description
Implement secure storage for secrets using environment variables with optional Vault integration.

### Acceptance Criteria
- [ ] Secrets not logged or exposed
- [ ] dotenv support for local development
- [ ] Vault integration placeholder
- [ ] API to retrieve secrets for plugins
- [ ] Documentation on secret management

### Dependencies
- #4 (Task 2.1: Unified config)
""",
        "labels": ["core", "security", "configuration", "priority:important", "phase:B"],
    },
    "3.3": {
        "title": "[Core] Prometheus metrics endpoint",
        "body": """**Priority:** P2 (Important)
**Phase:** C - Reliability & Scale

### Description
Expose Prometheus-compatible metrics endpoint for monitoring core system.

### Acceptance Criteria
- [ ] `/metrics` endpoint implemented
- [ ] Metrics: plugin count, errors, latency, throughput
- [ ] Counter/Gauge/Histogram types used appropriately
- [ ] Grafana dashboard example
- [ ] Documentation for metrics

### Dependencies
- #20 (Task 3.1: Structured logging)
""",
        "labels": ["core", "monitoring", "observability", "priority:important", "phase:C"],
    },
    "4.4": {
        "title": "[Core] Database indexes optimization",
        "body": """**Priority:** P2 (Important)
**Phase:** C - Reliability & Scale

### Description
Create indexes on frequently queried columns for performance optimization.

### Acceptance Criteria
- [ ] Indexes on: platform, price range, location, created_at
- [ ] Composite indexes for common filters
- [ ] EXPLAIN plans show index usage
- [ ] Migration with indexes
- [ ] Performance benchmarks

### Dependencies
- #6 (Task 4.1: PostgreSQL schema)
""",
        "labels": ["core", "database", "performance", "priority:important", "phase:C"],
    },
    "8.2": {
        "title": "[Core] Standardized API response envelope",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment

### Description
Implement consistent response format with data and meta fields across all endpoints.

### Acceptance Criteria
- [ ] Response format: `{data: ..., meta: {timestamp, trace_id, ...}}`
- [ ] Applied to all endpoints
- [ ] Pydantic response models
- [ ] Tests verify format
- [ ] Documentation updated

### Dependencies
- #15 (Task 8.1: API versioning)
""",
        "labels": ["core", "api", "standards", "priority:important", "phase:B"],
    },
    "8.3": {
        "title": "[Core] Global error handling",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment

### Description
Implement global exception handler for consistent error responses across API.

### Acceptance Criteria
- [ ] Exception handler for all error types
- [ ] Standardized error JSON format
- [ ] HTTP status codes mapped correctly
- [ ] Sensitive info not leaked in errors
- [ ] Tests for error scenarios

### Dependencies
- #15 (Task 8.1: API versioning)
""",
        "labels": ["core", "api", "error-handling", "priority:important", "phase:B"],
    },
    "8.7": {
        "title": "[Core] OpenAPI enhancements (tags, examples)",
        "body": """**Priority:** P3 (Nice to have)
**Phase:** B - Functional Enrichment

### Description
Enhance OpenAPI schema with tags, descriptions, and examples for better documentation.

### Acceptance Criteria
- [ ] Logical tag grouping (Plugins, Listings, etc.)
- [ ] Endpoint descriptions comprehensive
- [ ] Request/response examples
- [ ] Security schemes documented
- [ ] Swagger UI enhanced

### Dependencies
- #15 (Task 8.1: API versioning)
""",
        "labels": ["core", "api", "documentation", "priority:nice-to-have", "phase:B"],
    },
    "9.5": {
        "title": "[Core] CI security scanning (safety, bandit)",
        "body": """**Priority:** P2 (Important)
**Phase:** C - Reliability & Scale

### Description
Add automated security scanning to CI pipeline for dependency vulnerabilities and code issues.

### Acceptance Criteria
- [ ] Safety checks for vulnerable dependencies
- [ ] Bandit scans Python code
- [ ] CI fails on HIGH/CRITICAL findings
- [ ] Reports accessible in CI logs
- [ ] Scheduled weekly scans

### Dependencies
- Completed: 0.2 (requirements-dev.txt)
- #18 (Task 11.1: CI pipeline)
""",
        "labels": ["core", "security", "ci-cd", "priority:important", "phase:C"],
    },
    "10.2": {
        "title": "[Core] Integration tests for pipeline",
        "body": """**Priority:** P1 (Critical)
**Phase:** B - Functional Enrichment

### Description
Create end-to-end integration tests for the full processing pipeline with mock queue.

### Acceptance Criteria
- [ ] Tests cover full pipeline flow
- [ ] Mock message queue implementation
- [ ] Test database for integration tests
- [ ] Multiple plugin scenarios tested
- [ ] CI runs integration tests

### Dependencies
- #11 (Task 5.3: Processing orchestrator)
""",
        "labels": ["core", "testing", "integration", "priority:critical", "phase:B"],
    },
    "10.3": {
        "title": "[Core] Negative test cases",
        "body": """**Priority:** P2 (Important)
**Phase:** B - Functional Enrichment

### Description
Create comprehensive test suite for error conditions and edge cases.

### Acceptance Criteria
- [ ] Invalid inputs tested
- [ ] Error conditions covered
- [ ] Edge cases documented
- [ ] Catalog of error scenarios
- [ ] Tests pass consistently

### Dependencies
- #25 (Task 10.1: 70% coverage)
""",
        "labels": ["core", "testing", "quality", "priority:important", "phase:B"],
    },
}


def create_issues():
    """Create GitHub Issues from task definitions"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        print("\nPlease:")
        print("1. Create a GitHub Personal Access Token with 'repo' scope")
        print("2. Export it: export GITHUB_TOKEN=your_token_here")
        print("3. Run this script again")
        sys.exit(1)

    try:
        g = Github(token)
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        print(f"✓ Connected to repository: {repo.full_name}\n")

        # Create labels if they don't exist
        labels_to_create = {
            "core": "0366d6",
            "plugin-system": "1d76db",
            "database": "d4c5f9",
            "api": "0e8a16",
            "documentation": "0075ca",
            "testing": "fbca04",
            "security": "d93f0b",
            "ci-cd": "5319e7",
            "priority:critical": "b60205",
            "priority:important": "d93f0b",
            "priority:nice-to-have": "0e8a16",
            "phase:A": "c2e0c6",
            "phase:B": "bfd4f2",
            "phase:C": "f9d0c4",
            "phase:D": "fef2c0",
        }

        existing_labels = {label.name for label in repo.get_labels()}
        for label_name, color in labels_to_create.items():
            if label_name not in existing_labels:
                try:
                    repo.create_label(label_name, color)
                    print(f"✓ Created label: {label_name}")
                except GithubException as e:
                    print(f"⚠ Warning: Could not create label {label_name}: {e}")

        print()

        # Combine all tasks
        all_tasks = {**TASKS, **ADDITIONAL_TASKS}

        # Create issues
        created_issues = {}
        for task_id, task_data in sorted(all_tasks.items()):
            try:
                issue = repo.create_issue(
                    title=task_data["title"],
                    body=task_data["body"],
                    labels=task_data["labels"],
                )
                created_issues[task_id] = issue
                print(f"✓ Created issue #{issue.number}: {task_data['title']}")
            except GithubException as e:
                print(f"❌ Error creating issue {task_id}: {e}")

        print(f"\n✅ Successfully created {len(created_issues)} issues!")
        print(f"\nView issues at: https://github.com/{REPO_OWNER}/{REPO_NAME}/issues")

        # Create milestone for Phase A
        try:
            milestone = repo.create_milestone(
                "Phase A - Technical Foundation",
                description="Core infrastructure setup: plugin system, persistence, ETL pipeline basics, API foundation",
            )
            print(f"\n✓ Created milestone: {milestone.title}")
        except GithubException as e:
            print(f"\n⚠ Note: Could not create milestone: {e}")

    except GithubException as e:
        print(f"❌ GitHub API Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    create_issues()
