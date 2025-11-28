# Database Layer Documentation

## Overview

The database layer provides PostgreSQL integration with SQLAlchemy ORM and Alembic migrations for the Real Estate Anti-Fraud system.

## Components

### Models (`core/database/models.py`)

#### ListingModel
SQLAlchemy model for storing real estate listings based on the Unified Data Model (UDM).

**Fields:**
- `id` - Primary key (auto-increment)
- `listing_id` - Unique listing identifier (indexed)
- `source_*` - Source plugin information
- `type` - Listing type (sale/rent)
- `property_type` - Property category (apartment/house/commercial/land)
- `location_*` - Location details including coordinates
- `price_*` - Price information
- `description` - Listing description
- `media` - JSON/JSONB field for media assets
- `fraud_score` - Fraud detection score (0-100)
- `extra_metadata` - Additional flexible metadata (JSON/JSONB)
- `created_at`, `updated_at` - Timestamps

**Indexes:**
- Unique index on `listing_id`
- Composite index on `(location_city, type)`
- Individual indexes on frequently queried fields

### Repository (`core/database/repository.py`)

#### ListingRepository
Repository pattern for CRUD operations on listings.

**Methods:**

**Create:**
```python
create(listing: Listing) -> ListingModel
```
Creates a new listing from UDM model.

**Read:**
```python
get_by_id(listing_id: str) -> Optional[ListingModel]
get_by_db_id(id: int) -> Optional[ListingModel]
get_all(skip: int = 0, limit: int = 100, city: Optional[str] = None) -> List[ListingModel]
count(city: Optional[str] = None) -> int
```

**Update:**
```python
update(listing_id: str, **kwargs) -> Optional[ListingModel]
```

**Delete:**
```python
delete(listing_id: str) -> bool
```

**Specialized Queries:**
```python
get_by_fraud_score_range(min_score: float, max_score: float, skip: int = 0, limit: int = 100) -> List[ListingModel]
get_by_price_range(min_price: float, max_price: float, skip: int = 0, limit: int = 100, city: Optional[str] = None) -> List[ListingModel]
```

### Session Management (`core/database/session.py`)

Database session configuration:
```python
from core.database import SessionLocal, engine

# Get a session
db = SessionLocal()
try:
    # Use session
    pass
finally:
    db.close()
```

For FastAPI dependency injection:
```python
from core.database import get_db

@app.get("/listings")
def read_listings(db: Session = Depends(get_db)):
    repo = ListingRepository(db)
    return repo.get_all()
```

## Database Setup

### Environment Variables

```bash
# PostgreSQL connection
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

Default (if not set): `postgresql://postgres:postgres@localhost:5432/real_estate_fraud`

### Running PostgreSQL with Docker

**Using docker-compose (recommended):**
```bash
# Start PostgreSQL, Redis, and optional pgAdmin
docker-compose up -d

# Start only PostgreSQL
docker-compose up -d postgres

# Stop all services
docker-compose down

# Stop and remove volumes (clean state)
docker-compose down -v
```

**Using docker run (manual):**
```bash
docker run -d \
  --name real-estate-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=real_estate_fraud \
  -p 5432:5432 \
  postgres:16-alpine
```

**For testing environment:**
```bash
# Start test databases (different ports)
docker-compose -f docker-compose.test.yml up -d

# Environment variables for tests
export DATABASE_URL="postgresql://test_user:test_password@localhost:5433/real_estate_fraud_test"
export REDIS_URL="redis://localhost:6380"

# Run tests
pytest tests/

# Cleanup
docker-compose -f docker-compose.test.yml down
```

### Alembic Migrations

**Initialize (already done):**
```bash
alembic init alembic
```

**Create new migration:**
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations:**
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show history
alembic history
```

**Environment variable support:**
Alembic automatically uses `DATABASE_URL` environment variable if set, overriding `alembic.ini`.

## Testing

Unit tests use in-memory SQLite for speed. The `JSONBType` custom type automatically adapts to the target database.

Run tests:
```bash
pytest tests/unit/test_listing_repository.py -v
```

## Usage Examples

### Basic CRUD Operations

```python
from core.database import SessionLocal, ListingRepository
from core.models.udm import Listing, SourceInfo, Location, Price

db = SessionLocal()
repo = ListingRepository(db)

# Create
listing = Listing(
    listing_id="unique-id-123",
    source=SourceInfo(plugin_id="cian", platform="cian.ru"),
    type="sale",
    property_type="apartment",
    location=Location(city="Moscow"),
    price=Price(amount=5000000.00, currency="RUB")
)
db_listing = repo.create(listing)

# Read
listing = repo.get_by_id("unique-id-123")

# Update
repo.update("unique-id-123", fraud_score=75.0)

# Delete
repo.delete("unique-id-123")

db.close()
```

### Pagination

```python
# Get first page (10 items)
page1 = repo.get_all(skip=0, limit=10)

# Get second page
page2 = repo.get_all(skip=10, limit=10)

# Total count
total = repo.count()
```

### Filtering

```python
# By city
moscow_listings = repo.get_all(city="Moscow", limit=50)

# By fraud score range
suspicious = repo.get_by_fraud_score_range(70.0, 100.0)

# By price range
affordable = repo.get_by_price_range(1000000.0, 3000000.0, city="Moscow")
```

## Schema Versioning

Current schema version tracked in `alembic_version` table.

Migration history in `alembic/versions/`.

## Notes

- **Portable JSON Storage**: Uses custom `JSONBType` that automatically selects JSONB for PostgreSQL and JSON for other databases
- **Timezone Handling**: All timestamps use UTC (`datetime.utcnow()`)
- **Connection Pooling**: Configured with `pool_size=5` and `max_overflow=10`
- **Pre-ping**: Connection validation enabled via `pool_pre_ping=True`

## Docker Compose Services

### Development Environment (`docker-compose.yml`)

**Services:**
- **postgres** - PostgreSQL 16 database (port 5432)
- **redis** - Redis 7 for caching and message queue (port 6379)
- **pgadmin** - Database management UI (port 5050, optional, use `--profile dev`)

**Usage:**
```bash
# Start all services
docker-compose up -d

# Start with pgAdmin
docker-compose --profile dev up -d

# View logs
docker-compose logs -f postgres

# Access pgAdmin
# URL: http://localhost:5050
# Email: admin@realestate.local
# Password: admin
```

### Test Environment (`docker-compose.test.yml`)

**Services:**
- **postgres-test** - PostgreSQL for tests (port 5433)
- **redis-test** - Redis for tests (port 6380)

**Features:**
- Uses tmpfs for faster I/O
- Different ports to avoid conflicts with dev
- Minimal persistence configuration
- Quick startup and teardown

**Usage:**
```bash
# Start test environment
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
docker-compose -f docker-compose.test.yml ps

# Run integration tests
DATABASE_URL="postgresql://test_user:test_password@localhost:5433/real_estate_fraud_test" pytest tests/integration/

# Cleanup
docker-compose -f docker-compose.test.yml down
```

## Future Enhancements

- [ ] Add full-text search indexes for description
- [ ] Implement spatial indexes for location queries
- [ ] Add audit logging for changes
- [ ] Support for read replicas
- [ ] Async database support with SQLAlchemy 2.0
