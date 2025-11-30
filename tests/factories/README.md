# Test Data Factories

Comprehensive guide to test data generation factories for the RealEstatesAntiFraud project.

## Table of Contents

- [Introduction](#introduction)
- [Quick Start](#quick-start)
- [Available Factories](#available-factories)
- [Common Patterns](#common-patterns)
- [Specialized Scenarios](#specialized-scenarios)
- [Best Practices](#best-practices)
- [API Reference](#api-reference)

---

## Introduction

### What are Factories?

Test factories are tools that generate realistic test data automatically. Instead of manually creating complex objects with many fields, factories provide:

- **Realistic Data**: Uses Faker to generate believable property listings
- **Consistency**: All objects follow the same data model (UDM)
- **Flexibility**: Override any field for specific test scenarios
- **Maintainability**: Update data generation in one place
- **Speed**: Generate hundreds of objects quickly

### Why Use Factories?

**❌ Without Factories:**
```python
def test_listing():
    listing = Listing(
        listing_id="test-001",
        title="Test Property",
        description="A nice property for testing...",
        price=Price(amount=1000000, currency="EUR"),
        location=Location(
            city="Lisboa",
            country="Portugal",
            address="Rua Test 123",
            coordinates=Coordinates(lat=38.7223, lon=-9.1393)
        ),
        area=100.0,
        rooms=3,
        # ... 20+ more fields ...
    )
```

**✅ With Factories:**
```python
def test_listing(listing_factory):
    listing = listing_factory.create_listing(
        price={"amount": 1_000_000, "currency": "EUR"},
        location={"city": "Lisboa"}
    )
```

---

## Quick Start

### Basic Usage

```python
import pytest
from tests.factories.listing_factory import ListingFactory

def test_simple_listing():
    """Create a single realistic listing."""
    factory = ListingFactory()
    listing = factory.create_listing()

    assert listing.listing_id is not None
    assert listing.price.amount > 0
    assert listing.location.city is not None
```

### Using Pytest Fixtures

```python
def test_with_fixture(listing_factory):
    """Use pytest fixture for cleaner tests."""
    listing = listing_factory.create_listing()
    assert listing is not None
```

### Creating Multiple Listings

```python
def test_batch_creation(listing_factory):
    """Create multiple listings at once."""
    listings = listing_factory.create_batch(10)
    assert len(listings) == 10
    assert all(isinstance(l, Listing) for l in listings)
```

---

## Available Factories

### 1. ListingFactory

Generates real estate `Listing` objects with realistic data for Portugal 🇵🇹 and Ukraine 🇺🇦 markets.

**Features:**
- Portugal-focused data (Lisboa, Porto districts)
- Ukraine market support (Kyiv, Lviv)
- Realistic price ranges per district
- Fraud detection scenarios
- Edge cases for testing

**Basic Methods:**

```python
# Single listing
listing = factory.create_listing()

# Batch creation
listings = factory.create_batch(10)

# With custom fields
listing = factory.create_listing(
    price={"amount": 500_000, "currency": "EUR"},
    location={"city": "Lisboa", "district": "Baixa"}
)
```

**Specialized Methods:**

```python
# Lisboa apartments (Portugal)
listings = factory.create_lisboa_apartments(count=5)
listings = factory.create_lisboa_apartments(count=3, district="Chiado")

# Porto apartments
listings = factory.create_porto_apartments(count=5)

# Kyiv apartments (Ukraine)
listings = factory.create_kyiv_apartments(count=5)
listings = factory.create_kyiv_apartments(count=3, district="Pechersk")

# Lviv apartments
listings = factory.create_lviv_apartments(count=5)

# Regional Portuguese cities
listings = factory.create_regional_listings(count=10, city="Braga")

# Regional Ukrainian cities
listings = factory.create_regional_listings(count=10, city="Odesa")
```

**Fraud Testing:**

```python
# Fraud candidates
listings = factory.create_fraud_candidates(count=10)
listings = factory.create_fraud_candidates(count=5, fraud_type="unrealistic_price")

# Edge cases
listings = factory.create_edge_cases(count=5)
```

**Supported Cities:**
- **Portugal**: Lisboa, Porto, Braga, Coimbra, Faro, Funchal, Évora, Setúbal
- **Ukraine**: Kyiv, Lviv, Odesa, Kharkiv, Dnipro, Zaporizhzhia

### 2. EventFactory

Generates `ListingEvent` objects for event-driven testing.

**Event Types:**
- `RawListingReceived` - Initial data ingestion
- `ListingNormalized` - After data normalization
- `ListingProcessed` - After enrichment/geocoding
- `FraudDetected` - Fraud detection result

**Basic Usage:**

```python
from tests.factories.event_factory import EventFactory

factory = EventFactory()

# Create single event
event = factory.create_raw_event()

# Create normalized event
event = factory.create_normalized_event()

# Create processed event with fraud score
event = factory.create_processed_event(fraud_score=0.75)

# Create fraud detected event
event = factory.create_fraud_detected_event()
```

**Event Chains:**

```python
# Create complete event chain (raw -> normalized -> processed -> fraud)
events = factory.create_event_chain()

# Without fraud detection
events = factory.create_event_chain(include_fraud=False)
```

**Batch Creation:**

```python
# Create multiple events of same type
events = factory.create_batch(
    count=10,
    event_type="raw",
    platform="cian"
)
```

### 3. ListingBuilder

Fluent API for building complex test scenarios step-by-step.

**When to Use:**
- Complex multi-step configurations
- Readable test scenarios
- Building fraud patterns
- Creating edge cases

**Basic Pattern:**

```python
from tests.factories.listing_builder import ListingBuilder

builder = ListingBuilder()

listing = (builder
    .with_location("Lisboa", lat=38.7223, lon=-9.1393)
    .with_price(500_000)
    .with_area(100.0)
    .with_rooms(3)
    .build())
```

**Fraud Scenarios:**

```python
# Suspiciously cheap
listing = (builder
    .with_location("Lisboa")
    .with_price(50_000)  # Way too cheap
    .as_fraud_candidate(fraud_type="unrealistic_price")
    .build())

# Missing photos
listing = (builder
    .with_location("Porto")
    .as_fraud_candidate(fraud_type="no_photos")
    .build())

# Duplicate
listing = (builder
    .with_location("Kyiv")
    .as_fraud_candidate(fraud_type="duplicate")
    .build())
```

**Edge Cases:**

```python
# Minimal listing
listing = builder.as_edge_case(edge_type="minimal").build()

# Maximal listing
listing = builder.as_edge_case(edge_type="maximal").build()

# Zero price
listing = builder.as_edge_case(edge_type="zero_price").build()

# Negative area
listing = builder.as_edge_case(edge_type="negative_area").build()
```

---

## Common Patterns

### Pattern 1: Single Test Listing

```python
def test_create_listing_api(client, listing_factory):
    """Test API endpoint with factory data."""
    listing = listing_factory.create_listing()
    payload = listing.dict()

    response = client.post("/api/v1/listings/", json=payload)
    assert response.status_code == 201
```

### Pattern 2: Batch Testing

```python
def test_bulk_insert(db_session, listing_factory):
    """Test database with multiple listings."""
    listings = listing_factory.create_batch(100)

    for listing in listings:
        model = listing_to_model(listing)
        db_session.add(model)

    db_session.commit()
    count = db_session.query(ListingModel).count()
    assert count == 100
```

### Pattern 3: Filtered Testing

```python
def test_filter_by_city(db_session, listing_factory):
    """Test filtering with mixed data."""
    # Create listings in different cities
    lisboa = listing_factory.create_lisboa_apartments(5)
    porto = listing_factory.create_porto_apartments(3)

    for listing in lisboa + porto:
        model = listing_to_model(listing)
        db_session.add(model)

    db_session.commit()

    # Filter by city
    results = db_session.query(ListingModel).filter(
        ListingModel.city == "Lisboa"
    ).all()

    assert len(results) == 5
```

### Pattern 4: Custom Override

```python
def test_specific_price(listing_factory):
    """Test with specific price requirement."""
    listing = listing_factory.create_listing(
        price={"amount": 1_500_000, "currency": "EUR"}
    )

    assert listing.price.amount == 1_500_000
    assert listing.price.currency == "EUR"
```

### Pattern 5: Using Fixtures

```python
@pytest.fixture
def lisboa_properties(listing_factory):
    """Reusable Lisboa properties fixture."""
    return listing_factory.create_lisboa_apartments(10)

def test_lisboa_analysis(lisboa_properties):
    """Analyze Lisboa market."""
    avg_price = sum(l.price.amount for l in lisboa_properties) / len(lisboa_properties)
    assert avg_price > 0
```

### Pattern 6: Builder for Complexity

```python
def test_fraud_detection(listing_builder):
    """Test fraud detection with builder."""
    # Create suspicious listing
    listing = (listing_builder
        .with_location("Lisboa", district="Chiado")
        .with_price(50_000)  # Unrealistically low
        .with_area(150.0)
        .as_fraud_candidate(fraud_type="unrealistic_price")
        .build())

    # Calculate price per sqm
    price_per_sqm = listing.price.amount / listing.area
    assert price_per_sqm < 500  # Way below market
```

### Pattern 7: Event Chain Testing

```python
def test_event_pipeline(event_factory):
    """Test event processing pipeline."""
    events = event_factory.create_event_chain()

    assert events["raw"].event_type == "RawListingReceived"
    assert events["normalized"].event_type == "ListingNormalized"
    assert events["processed"].event_type == "ListingProcessed"
    assert events["fraud"].event_type == "FraudDetected"

    # Check correlation
    assert (events["normalized"].correlation_id ==
            events["raw"].correlation_id)
```

---

## Specialized Scenarios

### Fraud Detection Testing

#### Scenario 1: Price Anomalies

```python
def test_price_anomaly_detection(listing_factory):
    """Detect unrealistically low prices."""
    # Normal Lisboa apartment
    normal = listing_factory.create_lisboa_apartments(1)[0]
    normal_price_per_sqm = normal.price.amount / normal.area

    # Fraudulent listing
    fraud_listings = listing_factory.create_fraud_candidates(
        count=1,
        fraud_type="unrealistic_price"
    )
    fraud = fraud_listings[0]
    fraud_price_per_sqm = fraud.price.amount / fraud.area

    # Fraud should be significantly cheaper
    assert fraud_price_per_sqm < normal_price_per_sqm * 0.3
    assert fraud.fraud_score > 0.7
```

#### Scenario 2: Missing Photos

```python
def test_no_photos_detection(listing_factory):
    """Detect listings without photos."""
    fraud_listings = listing_factory.create_fraud_candidates(
        count=5,
        fraud_type="no_photos"
    )

    for listing in fraud_listings:
        assert len(listing.media.photos) == 0
        assert listing.fraud_score > 0.5
```

#### Scenario 3: Duplicates

```python
def test_duplicate_detection(listing_factory):
    """Detect near-duplicate listings."""
    duplicates = listing_factory.create_fraud_candidates(
        count=5,
        fraud_type="duplicate"
    )

    # All should be in same city
    cities = {l.location.city for l in duplicates}
    assert len(cities) == 1

    # Similar prices
    prices = [l.price.amount for l in duplicates]
    price_range = max(prices) - min(prices)
    assert price_range < 50_000
```

### Performance Testing

```python
def test_large_dataset_generation(listing_factory):
    """Generate large dataset for performance testing."""
    import time

    start = time.time()
    listings = listing_factory.create_batch(1000)
    duration = time.time() - start

    assert len(listings) == 1000
    assert duration < 5.0  # Should be fast
```

### Market Analysis Testing

```python
def test_market_price_distribution(listing_factory):
    """Analyze price distribution across districts."""
    # Generate Lisboa data
    listings = listing_factory.create_lisboa_apartments(50)

    # Group by district
    by_district = {}
    for listing in listings:
        district = listing.location.district
        if district not in by_district:
            by_district[district] = []
        by_district[district].append(listing.price.amount / listing.area)

    # Check reasonable distribution
    for district, prices in by_district.items():
        avg_price = sum(prices) / len(prices)
        assert 3000 < avg_price < 10000  # EUR per sqm
```

### Edge Case Testing

```python
def test_edge_cases_handling(listing_factory):
    """Test system with edge case data."""
    edge_cases = listing_factory.create_edge_cases(10)

    # System should handle all edge cases without crashing
    for listing in edge_cases:
        try:
            # Process listing
            result = process_listing(listing)
            assert result is not None
        except Exception as e:
            pytest.fail(f"Failed to handle edge case: {e}")
```

---

## Best Practices

### 1. Use Factories by Default

✅ **DO:**
```python
def test_create(listing_factory):
    listing = listing_factory.create_listing()
```

❌ **DON'T:**
```python
def test_create():
    listing = Listing(
        listing_id="test",
        title="Test",
        # ... 30 more fields ...
    )
```

### 2. Override Only What Matters

✅ **DO:**
```python
# Only override fields relevant to test
listing = factory.create_listing(
    price={"amount": 1_000_000, "currency": "EUR"}
)
```

❌ **DON'T:**
```python
# Don't specify everything
listing = factory.create_listing(
    price={"amount": 1_000_000, "currency": "EUR"},
    title="Test Property",
    description="A test property",
    # ... unnecessary overrides ...
)
```

### 3. Use Specialized Methods

✅ **DO:**
```python
# Use built-in specialization
listings = factory.create_lisboa_apartments(5)
```

❌ **DON'T:**
```python
# Manual filtering
all_listings = factory.create_batch(100)
lisboa = [l for l in all_listings if l.location.city == "Lisboa"][:5]
```

### 4. Leverage Pytest Fixtures

✅ **DO:**
```python
@pytest.fixture
def lisboa_market(listing_factory):
    return listing_factory.create_lisboa_apartments(20)

def test_market_analysis(lisboa_market):
    # Reusable data
    assert len(lisboa_market) == 20
```

❌ **DON'T:**
```python
def test_market_analysis(listing_factory):
    # Recreating same data in each test
    listings = listing_factory.create_lisboa_apartments(20)
```

### 5. Use Builder for Complex Scenarios

✅ **DO:**
```python
# Builder for multi-step construction
listing = (builder
    .with_location("Lisboa")
    .with_price(500_000)
    .as_fraud_candidate()
    .build())
```

❌ **DON'T:**
```python
# Factory override for complex scenarios
listing = factory.create_listing(
    location={...},
    price={...},
    fraud_score=0.9,
    # ... many overrides ...
)
```

### 6. Use Seeding for Reproducibility

✅ **DO:**
```python
# Reproducible tests
factory = ListingFactory(seed=42)
listing1 = factory.create_listing()

factory2 = ListingFactory(seed=42)
listing2 = factory2.create_listing()

assert listing1.title == listing2.title
```

### 7. Batch Creation for Performance

✅ **DO:**
```python
# Single batch call
listings = factory.create_batch(100)
```

❌ **DON'T:**
```python
# Multiple individual calls
listings = [factory.create_listing() for _ in range(100)]
```

### 8. Clear Test Intent

✅ **DO:**
```python
def test_fraud_detection_low_price():
    """Test detects unrealistically low prices."""
    listing = factory.create_fraud_candidates(
        count=1,
        fraud_type="unrealistic_price"
    )[0]

    result = detect_fraud(listing)
    assert result.is_fraud is True
```

❌ **DON'T:**
```python
def test_fraud():
    listing = factory.create_listing(price={"amount": 1000})
    # Unclear why price is 1000
    result = detect_fraud(listing)
    assert result.is_fraud
```

---

## API Reference

### ListingFactory

#### `__init__(self, seed: Optional[int] = None)`

Initialize factory with optional seed for reproducible data.

**Parameters:**
- `seed` (int, optional): Random seed for Faker

**Example:**
```python
factory = ListingFactory(seed=42)
```

#### `create_listing(**kwargs) -> Listing`

Create a single Listing with optional overrides.

**Parameters:**
- `price` (dict, optional): `{"amount": int, "currency": str}`
- `location` (dict, optional): `{"city": str, "district": str, ...}`
- `area` (float, optional): Property area in sqm
- `rooms` (int, optional): Number of rooms
- `fraud_score` (float, optional): Fraud score 0-100

**Returns:** `Listing` object

**Example:**
```python
listing = factory.create_listing(
    price={"amount": 500_000, "currency": "EUR"},
    location={"city": "Lisboa", "district": "Baixa"}
)
```

#### `create_batch(count: int, **kwargs) -> List[Listing]`

Create multiple listings.

**Parameters:**
- `count` (int): Number of listings to create
- `**kwargs`: Common overrides for all listings

**Returns:** List of `Listing` objects

**Example:**
```python
listings = factory.create_batch(10, area=100.0)
```

#### `create_lisboa_apartments(count: int, district: Optional[str] = None) -> List[Listing]`

Create Lisboa apartment listings.

**Parameters:**
- `count` (int): Number of apartments
- `district` (str, optional): Specific district (Baixa, Chiado, Alfama, etc.)

**Returns:** List of `Listing` objects

**Available Districts:**
- Baixa, Chiado, Alfama, Belém, Parque das Nações, Alvalade, Campo de Ourique, Estrela

**Example:**
```python
listings = factory.create_lisboa_apartments(5, district="Chiado")
```

#### `create_porto_apartments(count: int, district: Optional[str] = None) -> List[Listing]`

Create Porto apartment listings.

**Parameters:**
- `count` (int): Number of apartments
- `district` (str, optional): Specific district

**Available Districts:**
- Ribeira, Boavista, Foz do Douro, Cedofeita, Massarelos

#### `create_kyiv_apartments(count: int, district: Optional[str] = None) -> List[Listing]`

Create Kyiv apartment listings.

**Parameters:**
- `count` (int): Number of apartments
- `district` (str, optional): Specific district

**Available Districts:**
- Pechersk, Podil, Shevchenkivskyi, Holosiivskyi, Obolon

#### `create_lviv_apartments(count: int, district: Optional[str] = None) -> List[Listing]`

Create Lviv apartment listings.

**Available Districts:**
- Lychakiv, Halytskyi, Shevchenkivskyi, Sykhiv

#### `create_regional_listings(count: int, city: str) -> List[Listing]`

Create listings for regional cities.

**Supported Cities:**
- **Portugal**: Braga, Coimbra, Faro, Funchal, Évora, Setúbal
- **Ukraine**: Odesa, Kharkiv, Dnipro, Zaporizhzhia

#### `create_fraud_candidates(count: int, fraud_type: Optional[str] = None) -> List[Listing]`

Create listings with fraud indicators.

**Parameters:**
- `count` (int): Number of fraud candidates
- `fraud_type` (str, optional): Specific fraud type

**Fraud Types:**
- `unrealistic_price`: Suspiciously low prices
- `no_photos`: Listings without photos
- `duplicate`: Near-duplicate listings
- `fake_location`: Invalid coordinates
- `too_good_to_be_true`: Perfect listing with red flags

#### `create_edge_cases(count: int) -> List[Listing]`

Create edge case listings for boundary testing.

**Edge Cases:**
- Minimal data
- Maximal data
- Zero/negative prices
- Invalid coordinates
- Empty descriptions
- Oversized areas

### EventFactory

#### `create_raw_event(**kwargs) -> RawListingReceived`

Create raw listing received event.

**Parameters:**
- `listing` (Listing, optional): Listing data
- `platform` (str, optional): Source platform

#### `create_normalized_event(**kwargs) -> ListingNormalized`

Create normalized listing event.

#### `create_processed_event(**kwargs) -> ListingProcessed`

Create processed listing event with enrichments.

**Parameters:**
- `fraud_score` (float, optional): Fraud score 0-1

#### `create_fraud_detected_event(**kwargs) -> FraudDetected`

Create fraud detected event.

#### `create_event_chain(include_fraud: bool = True) -> Dict[str, ListingEvent]`

Create complete event chain.

**Returns:** Dict with keys: `raw`, `normalized`, `processed`, `fraud`

#### `create_batch(count: int, event_type: str, **kwargs) -> List[ListingEvent]`

Create multiple events of same type.

**Event Types:** `raw`, `normalized`, `processed`, `fraud`

### ListingBuilder

#### Method Chaining

All builder methods return `self` for chaining.

#### `with_location(city: str, lat: float = None, lon: float = None) -> Self`

Set location.

#### `with_price(amount: int, currency: str = "EUR") -> Self`

Set price.

#### `with_area(area: float) -> Self`

Set property area.

#### `with_rooms(rooms: int) -> Self`

Set number of rooms.

#### `with_media(photos: List[str] = None, videos: List[str] = None) -> Self`

Set media.

#### `with_source(platform: str, url: str = None) -> Self`

Set source info.

#### `as_fraud_candidate(fraud_type: str = None) -> Self`

Configure as fraud candidate.

#### `as_edge_case(edge_type: str) -> Self`

Configure as edge case.

#### `build() -> Listing`

Build final Listing object.

#### `build_dict() -> Dict[str, Any]`

Build as dictionary (JSON-serializable).

---

## Troubleshooting

### Issue: Faker generates non-deterministic data

**Solution:** Use seed parameter
```python
factory = ListingFactory(seed=42)
```

### Issue: Need specific city that's not supported

**Solution:** Use override
```python
listing = factory.create_listing(
    location={"city": "CustomCity", "country": "Portugal"}
)
```

### Issue: Factory is slow for large datasets

**Solution:** Use batch creation and consider caching
```python
# Fast batch creation
listings = factory.create_batch(1000)

# Cache in fixture
@pytest.fixture(scope="module")
def large_dataset(listing_factory):
    return listing_factory.create_batch(1000)
```

### Issue: Need reproducible test data across runs

**Solution:** Use seeded factory
```python
@pytest.fixture
def seeded_factory():
    return ListingFactory(seed=12345)
```

---

## Further Reading

- [Pytest Fixtures Documentation](https://docs.pytest.org/en/stable/fixture.html)
- [Faker Documentation](https://faker.readthedocs.io/)
- [Factory Pattern](https://refactoring.guru/design-patterns/factory-method)
- [Test Data Builders](https://www.petrikainulainen.net/programming/testing/writing-clean-tests-it-starts-from-the-configuration/)

---

## Contributing

When adding new factory methods:

1. Add comprehensive docstring with examples
2. Update this README
3. Add tests to verify factory output
4. Consider adding to pytest fixtures
5. Update API reference section

---

**Last Updated:** November 30, 2025
**Maintainers:** RealEstatesAntiFraud Team
