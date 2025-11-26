#!/usr/bin/env python3
"""Create GitHub Issues for completed bootstrap tasks"""

import os
import sys
from github import Github
from datetime import datetime

REPO_OWNER = "loudmantrade"
REPO_NAME = "RealEstatesAntiFroud"

COMPLETED_TASKS = {
    "bootstrap-structure": {
        "title": "[Bootstrap] Core directory structure",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Created base directory hierarchy for core system.

### What was completed
- Directories: `core/`, `core/api/`, `core/api/routes/`, `core/interfaces/`, `core/models/`, `core/utils/`, `tests/unit/core/`
- All directories with proper `__init__.py` files
- Structure follows architecture document

### Files
- `core/__init__.py`
- `core/api/__init__.py`
- `core/interfaces/`
- `core/models/`
- `tests/unit/core/`

### Acceptance Criteria
- [x] Directories exist in repository
- [x] Proper Python package structure
- [x] Follows project conventions

**Related:** Task 0.1 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-dependencies": {
        "title": "[Bootstrap] Dependencies and requirements",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Added runtime and development dependencies.

### What was completed
**Runtime dependencies** (`requirements.txt`):
- fastapi 0.115.5
- uvicorn 0.32.0
- pydantic 2.9.2

**Development dependencies** (`requirements-dev.txt`):
- pytest 8.3.3
- pytest-cov 6.0.0
- black 24.10.0
- flake8 7.1.1
- isort 5.13.2
- mypy 1.14.0
- bandit 1.8.0
- safety 3.2.10

### Files
- `requirements.txt`
- `requirements-dev.txt`

### Acceptance Criteria
- [x] Installation succeeds without errors
- [x] All packages compatible with Python 3.13
- [x] Dev tools ready for use

**Related:** Task 0.2 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["dependencies", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-plugin-models": {
        "title": "[Bootstrap] Pydantic plugin models",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Created Pydantic models for plugin metadata and registration.

### What was completed
File: `core/models/plugin.py`

**Classes:**
- `PluginMetadata`: id, name, version, type, enabled, config
- `PluginRegistrationRequest`: metadata wrapper

### Features
- Type validation
- Optional config dict
- Enable/disable state tracking
- Version tracking

### Files
- `core/models/plugin.py`

### Acceptance Criteria
- [x] Models can be imported
- [x] Validation works correctly
- [x] Used in API endpoints

**Related:** Task 0.3 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "models", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-udm-models": {
        "title": "[Bootstrap] Unified Data Model (UDM) basics",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Created basic Unified Data Model for listings (minimal MVP subset).

### What was completed
File: `core/models/udm.py`

**Models:**
- `SourceInfo`: plugin_id, platform, original_id, url
- `Price`: amount, currency
- `Location`: city, address, coordinates (optional)
- `Media`: images, videos (URLs)
- `Listing`: Main listing model with all fields

### Fields
- id, source, type (sale/rent)
- location, price
- title, description
- media
- created_at timestamp

### Files
- `core/models/udm.py`

### Acceptance Criteria
- [x] API accepts the model
- [x] JSON serialization works
- [x] Basic fields for MVP

**Related:** Task 0.4 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "models", "data-model", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-plugin-interfaces": {
        "title": "[Bootstrap] Plugin interfaces (ABC)",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Created abstract base classes for all plugin types.

### What was completed
Files in `core/interfaces/`:

1. **`source_plugin.py`** - `SourcePlugin`
   - Methods: `scrape()`, `validate()`, `get_metadata()`, `configure()`

2. **`processing_plugin.py`** - `ProcessingPlugin`
   - Methods: `process()`, `get_priority()`

3. **`detection_plugin.py`** - `DetectionPlugin`
   - Methods: `analyze()`, `get_weight()`

4. **`search_plugin.py`** - `SearchPlugin`
   - Methods: `index()`, `search()`, `suggest()`

5. **`display_plugin.py`** - `DisplayPlugin`
   - Methods: `format_listing()`, `get_template()`

### Files
- `core/interfaces/source_plugin.py`
- `core/interfaces/processing_plugin.py`
- `core/interfaces/detection_plugin.py`
- `core/interfaces/search_plugin.py`
- `core/interfaces/display_plugin.py`

### Acceptance Criteria
- [x] All interfaces defined with ABC
- [x] Abstract methods documented
- [x] Ready for plugin implementations

**Related:** Task 0.5 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "plugin-system", "architecture", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-plugin-manager": {
        "title": "[Bootstrap] Plugin Manager (in-memory)",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Implemented in-memory plugin registry with lifecycle management.

### What was completed
File: `core/plugin_manager.py`

**Class: `PluginManager`**
- `register(metadata)`: Register new plugin
- `get(plugin_id)`: Retrieve plugin by ID
- `list_plugins()`: List all registered plugins
- `enable(plugin_id)`: Enable plugin
- `disable(plugin_id)`: Disable plugin
- `remove(plugin_id)`: Remove plugin

**Features:**
- Thread-safe (uses Lock)
- Singleton instance `plugin_manager`
- In-memory dictionary storage
- Validation on operations

### Files
- `core/plugin_manager.py`

### Acceptance Criteria
- [x] Unit test passed (test_plugin_manager.py)
- [x] Thread-safe operations
- [x] API integration working

**Related:** Task 0.6 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "plugin-system", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-fastapi-app": {
        "title": "[Bootstrap] FastAPI application setup",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Set up FastAPI application with CORS, health check, and route integration.

### What was completed
File: `core/api/main.py`

**Features:**
- FastAPI app instance
- CORS middleware (allow all origins for dev)
- Health endpoint: `GET /health`
- Routers included:
  - `/api/plugins` (plugin management)
  - `/api/listings` (listings CRUD)

### Endpoints
- `GET /health` → `{"status": "healthy"}`
- `GET /docs` → Swagger UI
- `GET /redoc` → ReDoc

### Files
- `core/api/main.py`

### Acceptance Criteria
- [x] Application starts successfully
- [x] Health endpoint returns 200
- [x] Swagger docs accessible
- [x] CORS configured

**Related:** Task 0.7 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "api", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-plugins-routes": {
        "title": "[Bootstrap] Plugin management API routes",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Created REST API endpoints for plugin management (CRUD operations).

### What was completed
File: `core/api/routes/plugins.py`

**Endpoints:**
- `POST /api/plugins/register` - Register new plugin
- `GET /api/plugins/` - List all plugins
- `GET /api/plugins/{plugin_id}` - Get plugin details
- `PUT /api/plugins/{plugin_id}/enable` - Enable plugin
- `PUT /api/plugins/{plugin_id}/disable` - Disable plugin
- `DELETE /api/plugins/{plugin_id}` - Remove plugin

**Features:**
- Pydantic request/response models
- Error handling (404 for not found)
- Integration with PluginManager

### Files
- `core/api/routes/plugins.py`

### Acceptance Criteria
- [x] All CRUD operations work
- [x] curl responses valid
- [x] Error handling in place

**Related:** Task 0.8 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "api", "plugin-system", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-listings-routes": {
        "title": "[Bootstrap] Listings API routes (in-memory)",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Created REST API endpoints for listings management with in-memory storage.

### What was completed
File: `core/api/routes/listings.py`

**Endpoints:**
- `POST /api/listings/` - Create listing
- `GET /api/listings/` - List all listings
- `GET /api/listings/{listing_id}` - Get listing by ID
- `DELETE /api/listings/{listing_id}` - Delete listing

**Storage:**
- In-memory dictionary (temporary MVP solution)
- UUID generation for listing IDs

**Models:**
- Uses `Listing` from `core.models.udm`

### Files
- `core/api/routes/listings.py`

### Acceptance Criteria
- [x] Create/read/delete work
- [x] Test listing can be created
- [x] JSON responses valid

**Note:** Will be replaced with PostgreSQL persistence in Sprint 1 (Task 4.3)

**Related:** Task 0.9 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "api", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-unit-tests": {
        "title": "[Bootstrap] Unit tests for plugin manager",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P1 (Critical)
**Phase:** Bootstrap

### Description
Created unit tests for plugin manager lifecycle operations.

### What was completed
File: `tests/unit/core/test_plugin_manager.py`

**Test: `test_plugin_lifecycle`**
- Register plugin
- Verify retrieval
- Enable plugin
- Verify enabled state
- Disable plugin
- Verify disabled state
- Remove plugin
- Verify removal

**Results:**
- ✅ 1 passed in 0.24s
- Coverage: plugin_manager.py main scenarios

### Files
- `tests/unit/core/test_plugin_manager.py`

### Acceptance Criteria
- [x] All tests pass
- [x] Lifecycle operations covered
- [x] Can be run in CI

**Related:** Task 0.10 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["core", "testing", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-development-plan": {
        "title": "[Bootstrap] Core development plan documentation",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P2 (Important)
**Phase:** Bootstrap

### Description
Created comprehensive development plan with tasks, phases, sprints, and acceptance criteria.

### What was completed
File: `docs/CORE_DEVELOPMENT_PLAN.md`

**Contains:**
- 21 sections covering all aspects
- Task breakdown (1.x - 13.x) by modules
- Phase definitions (A, B, C, D)
- Sprint backlog recommendations (S1-S4)
- Acceptance criteria for each task
- Dependencies mapping
- Risk assessment
- Success metrics
- Changelog

**Total tasks:** 80+ planned tasks organized by priority

### Files
- `docs/CORE_DEVELOPMENT_PLAN.md`

### Acceptance Criteria
- [x] Document created and structured
- [x] All planned tasks documented
- [x] Roadmap clear
- [x] Ready for team use

**Related:** Task 0.11 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["documentation", "planning", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-github-automation": {
        "title": "[Bootstrap] GitHub Issues automation scripts",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P2 (Important)
**Phase:** Bootstrap

### Description
Created automation scripts for generating GitHub Issues from development plan.

### What was completed
**Files:**
- `scripts/create_github_issues.py` - Main script (42 issues)
- `scripts/run_create_issues.py` - Interactive wrapper
- `scripts/README.md` - Usage documentation
- `docs/GITHUB_ISSUES_SETUP.md` - Detailed setup guide

**Results:**
- ✅ 42 GitHub Issues created
- ✅ 14 labels created (component, priority, phase)
- ✅ Milestone "Phase A - Technical Foundation" created
- ✅ Cross-references and dependencies set

**Issues by sprint:**
- S1: 10 issues (foundation)
- S2: 10 issues (core features)
- S3: 5 issues (search, tests)
- S4: 7 issues (extensions, security)
- Future: 10+ additional

### Files
- `scripts/create_github_issues.py`
- `scripts/run_create_issues.py`
- `scripts/README.md`
- `docs/GITHUB_ISSUES_SETUP.md`

### Acceptance Criteria
- [x] Script executed successfully
- [x] All issues created with labels
- [x] Dependencies linked
- [x] Milestone set

**Related:** Task 0.12 in CORE_DEVELOPMENT_PLAN.md
**Issues:** https://github.com/loudmantrade/RealEstatesAntiFroud/issues
""",
        "labels": ["automation", "ci-cd", "completed", "bootstrap"],
        "state": "closed",
    },
    "bootstrap-makefile": {
        "title": "[Bootstrap] Makefile for development automation",
        "body": """**Status:** ✅ Completed on 2025-11-25
**Priority:** P2 (Important)
**Phase:** Bootstrap

### Description
Created Makefile with targets for common development tasks.

### What was completed
File: `Makefile`

**Targets:**
- `make setup` - Initialize project (venv, deps)
- `make dev` - Run dev server
- `make test` - Run all tests
- `make test-unit` - Run unit tests only
- `make test-cov` - Tests with coverage
- `make lint` - Run linters (flake8, black, mypy)
- `make format` - Format code (black, isort)
- `make security` - Security scan (bandit, safety)
- `make clean` - Clean temporary files
- `make build` - Build Docker image
- `make deploy` - Deploy commands (placeholder)

**Plugin operations:**
- `make plugin-validate` - Validate plugin manifest
- `make plugin-install` - Install plugin
- `make plugin-test` - Test plugin

### Files
- `Makefile`

### Acceptance Criteria
- [x] Make targets work correctly
- [x] Documentation in comments
- [x] Ready for CI/CD use

**Related:** Task 0.13 in CORE_DEVELOPMENT_PLAN.md
""",
        "labels": ["automation", "developer-experience", "completed", "bootstrap"],
        "state": "closed",
    },
}

def create_completed_issues():
    """Create closed issues for completed bootstrap tasks"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("❌ Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    try:
        g = Github(token)
        repo = g.get_repo(f"{REPO_OWNER}/{REPO_NAME}")
        print(f"✓ Connected to repository: {repo.full_name}\n")

        # Create issues
        created = 0
        for task_id, task_data in COMPLETED_TASKS.items():
            try:
                issue = repo.create_issue(
                    title=task_data["title"],
                    body=task_data["body"],
                    labels=task_data["labels"],
                )
                # Close the issue since it's already completed
                issue.edit(state="closed")
                
                created += 1
                print(f"✓ Created & closed issue #{issue.number}: {task_data['title']}")
            except Exception as e:
                print(f"❌ Error creating issue {task_id}: {e}")

        print(f"\n✅ Successfully created {created} completed bootstrap issues!")
        print(f"\nView all issues at: https://github.com/{REPO_OWNER}/{REPO_NAME}/issues?q=is%3Aissue+label%3Acompleted")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_completed_issues()
