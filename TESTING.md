# Testing Guide

This guide explains how to set up and run tests for the RealEstatesAntiFraud project.

## Quick Start

### Automated Setup (Recommended)

```bash
# One command to set up everything
bash scripts/setup_test_env.sh
```

This script will:
- ✅ Check prerequisites (Docker, Python 3.11+)
- ✅ Start PostgreSQL and Redis containers
- ✅ Create Python virtual environment
- ✅ Install all dependencies
- ✅ Run database migrations
- ✅ Verify the setup

### Manual Setup

If you prefer manual setup or need to troubleshoot:

```bash
# 1. Start test containers
docker-compose -f docker-compose.test.yml up -d

# 2. Wait for services (optional)
bash scripts/wait_for_services.sh

# 3. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 5. Run migrations
alembic upgrade head

# 6. Verify setup
bash scripts/verify_test_env.sh
```

## Running Tests

### All Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=core --cov-report=term-missing
```

### Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_api_plugins.py

# Specific test function
pytest tests/unit/test_api_plugins.py::test_list_plugins_empty
```

### Test Options

```bash
# Verbose output
pytest tests/ -v

# Show print statements
pytest tests/ -s

# Stop at first failure
pytest tests/ -x

# Run failed tests from last run
pytest tests/ --lf

# Parallel execution (faster)
pytest tests/ -n auto

# Generate HTML coverage report
pytest tests/ --cov=core --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Environment

### Services

The test environment runs the following services:

| Service    | Port  | Container Name          | Purpose                |
|------------|-------|-------------------------|------------------------|
| PostgreSQL | 5433  | realestate-test-db      | Database for tests     |
| Redis      | 6380  | real-estate-redis-test  | Queue & cache for tests|

**Note:** Ports are different from production (5432/6379) to avoid conflicts.

### Environment Variables

Test configuration is in `.env.test`:

```bash
# Database
DATABASE_URL=postgresql://test_user:test_pass@localhost:5433/realestate_test

# Redis
REDIS_HOST=localhost
REDIS_PORT=6380
REDIS_DB=0

# API
API_HOST=0.0.0.0
API_PORT=8001

# Logging
LOG_LEVEL=DEBUG
TESTING=true
```

### Data Isolation

- **Unit tests**: Use mocks and in-memory structures (no external services)
- **Integration tests**: Use real PostgreSQL/Redis but clean up after each test
- **Test database**: Automatically rolled back after each test using fixtures
- **Test Redis**: Uses separate database index, flushed between tests

## Managing Test Environment

### Check Status

```bash
# Verify everything is working
bash scripts/verify_test_env.sh

# Check running containers
docker-compose -f docker-compose.test.yml ps

# View container logs
docker-compose -f docker-compose.test.yml logs postgres-test
docker-compose -f docker-compose.test.yml logs redis-test
```

### Teardown

```bash
# Stop containers only
bash scripts/teardown_test_env.sh

# Stop containers and remove volumes
bash scripts/teardown_test_env.sh --clean-volumes

# Stop containers and clean all caches
bash scripts/teardown_test_env.sh --clean-all
```

### Restart Services

```bash
# Restart all services
docker-compose -f docker-compose.test.yml restart

# Restart specific service
docker-compose -f docker-compose.test.yml restart postgres-test
docker-compose -f docker-compose.test.yml restart redis-test
```

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are in use
lsof -i :5433  # PostgreSQL
lsof -i :6380  # Redis

# Stop conflicting services
docker-compose -f docker-compose.test.yml down

# Remove old containers
docker ps -a | grep realestate
docker rm -f <container_id>
```

### Database Connection Issues

```bash
# Test PostgreSQL connection manually
docker exec realestate-test-db psql -U test_user -d realestate_test -c "SELECT 1;"

# Reset database
docker-compose -f docker-compose.test.yml down -v
bash scripts/setup_test_env.sh
```

### Redis Connection Issues

```bash
# Test Redis connection manually
docker exec real-estate-redis-test redis-cli ping

# Check Redis logs
docker logs real-estate-redis-test
```

### Migration Issues

```bash
# Check current migration version
alembic current

# Reset to clean state
alembic downgrade base
alembic upgrade head

# View migration history
alembic history
```

### Slow Tests

```bash
# Run tests in parallel
pytest tests/ -n auto

# Run only fast unit tests
pytest tests/unit/

# Skip slow integration tests
pytest tests/ -m "not slow"
```

## CI/CD

Our GitHub Actions CI runs the same test environment:

```yaml
# .github/workflows/ci.yml
- name: Start services
  run: docker-compose -f docker-compose.test.yml up -d

- name: Run tests
  run: |
    pytest tests/ --cov=core --cov-report=xml
```

You can reproduce CI behavior locally:

```bash
# Exactly as CI does
bash scripts/setup_test_env.sh
source .venv/bin/activate
pytest tests/ --cov=core --cov-report=xml --cov-report=term
```

## Test Coverage Goals

- **Overall**: 90%+
- **Core business logic**: 95%+
- **API routes**: 90%+
- **Database repositories**: 95%+
- **Plugin interfaces**: 70%+ (abstract methods expected)

Check current coverage:

```bash
pytest tests/ --cov=core --cov-report=term-missing
```

## Writing Tests

### Test Structure

```
tests/
├── unit/              # Fast, isolated tests (mocks)
│   ├── test_api_*.py
│   ├── test_*_orchestrator.py
│   └── ...
├── integration/       # Tests with real services
│   ├── test_listings_*.py
│   ├── test_redis_queue.py
│   └── ...
└── fixtures/          # Shared test data and plugins
    └── plugins/
```

### Unit Test Example

```python
from unittest.mock import MagicMock, patch
import pytest

def test_example_with_mock():
    with patch('core.module.dependency') as mock_dep:
        mock_dep.return_value = "mocked"
        # Test code here
```

### Integration Test Example

```python
import pytest
from sqlalchemy.orm import Session

def test_example_with_db(db_session: Session):
    # Use real database via fixture
    # Automatically rolled back after test
```

## Best Practices

1. **Isolation**: Each test should be independent
2. **Fast**: Unit tests < 100ms, integration tests < 1s
3. **Descriptive**: Test names should explain what they test
4. **Arrange-Act-Assert**: Follow AAA pattern
5. **Fixtures**: Reuse common setup via pytest fixtures
6. **Cleanup**: Always clean up resources (use fixtures with yield)
7. **Coverage**: Aim for high coverage but focus on quality

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [Docker Compose documentation](https://docs.docker.com/compose/)
- [Project Architecture](ARCHITECTURE.md)
