# Factory Fixtures Documentation

This document describes the pytest fixtures available for test data generation.

## Overview

All fixtures are automatically available in your tests without manual imports. Just add them as function parameters.

## Factory Fixtures

### `listing_factory`

Main factory for creating real estate listings.

```python
def test_with_factory(listing_factory):
    listing = listing_factory.create_listing(price=1_000_000)
    assert listing.price.amount == 1_000_000
```

**Methods:**
- `create_listing(**kwargs)` - Create single listing
- `create_batch(count, **kwargs)` - Create multiple listings
- `create_lisboa_apartments(count, district)` - Lisboa-specific listings
- `create_porto_apartments(count, district)` - Porto-specific listings
- `create_kyiv_apartments(count, district)` - Kyiv-specific listings
- `create_lviv_apartments(count, district)` - Lviv-specific listings
- `create_regional_listings(city, count)` - Regional listings
- `create_fraud_candidates(count, fraud_type)` - Fraud test data
- `create_edge_cases(count)` - Edge case test data

### `event_factory`

Factory for creating listing processing events.

```python
def test_events(event_factory):
    event = event_factory.create_raw_listing_event()
    assert event.event_type == EventType.RAW_LISTING_RECEIVED
```

**Methods:**
- `create_raw_listing_event()` - Raw listing event
- `create_normalized_listing_event()` - Normalized event
- `create_processed_listing_event()` - Processed event
- `create_event_chain()` - Complete event chain

### `listing_builder`

Fluent builder for constructing complex listings.

```python
def test_builder(listing_builder):
    listing = (
        listing_builder
        .with_price(500_000)
        .in_city("Lisboa")
        .with_area(85)
        .with_rooms(3)
        .build()
    )
    assert listing.price.amount == 500_000
```

## Portugal Market Fixtures

### `lisboa_apartments`

5 pre-generated Lisboa apartments.

```python
def test_lisboa(lisboa_apartments):
    assert len(lisboa_apartments) == 5
    assert all(l.location.city == "Lisboa" for l in lisboa_apartments)

    # Districts: Baixa, Chiado, Alfama, Belém, Parque das Nações
    districts = {l.location.district for l in lisboa_apartments}
    assert len(districts) >= 3
```

### `porto_apartments`

5 pre-generated Porto apartments.

```python
def test_porto(porto_apartments):
    assert len(porto_apartments) == 5
    assert all(l.location.city == "Porto" for l in porto_apartments)

    # Districts: Ribeira, Boavista, Cedofeita, Foz, Matosinhos
```

### `portuguese_cities`

10 listings from various Portuguese cities.

```python
def test_portugal(portuguese_cities):
    assert len(portuguese_cities) == 10
    cities = {l.location.city for l in portuguese_cities}
    # Cities: Lisboa, Porto, Faro, Coimbra, Braga
```

## Ukraine Market Fixtures

### `kyiv_apartments`

5 pre-generated Kyiv apartments.

```python
def test_kyiv(kyiv_apartments):
    assert len(kyiv_apartments) == 5
    assert all(l.location.city == "Київ" for l in kyiv_apartments)

    # Districts: Печерськ, Поділ, Шевченківський, Оболонь, Дарницький
```

### `lviv_apartments`

5 pre-generated Lviv apartments.

```python
def test_lviv(lviv_apartments):
    assert len(lviv_apartments) == 5
    assert all(l.location.city == "Львів" for l in lviv_apartments)

    # Districts: Личаківський, Галицький, Франківський
```

### `ukrainian_cities`

10 listings from various Ukrainian cities.

```python
def test_ukraine(ukrainian_cities):
    assert len(ukrainian_cities) == 10
    cities = {l.location.city for l in ukrainian_cities}
    # Cities: Київ, Львів, Одеса, Харків, Дніпро
```

## Specialized Fixtures

### `fraud_candidates`

3 listings with fraud patterns.

```python
def test_fraud_detection(fraud_candidates):
    assert len(fraud_candidates) == 3
    # All have suspicious characteristics
    for listing in fraud_candidates:
        # Test fraud detection algorithms
        pass
```

**Fraud Types:**
- `price_too_low` - Suspiciously low prices
- `price_too_high` - Suspiciously high prices
- `duplicate` - Duplicate listings
- `missing_data` - Incomplete information
- `inconsistent` - Inconsistent data

### `edge_case_listings`

5 edge case listings for boundary testing.

```python
def test_edge_cases(edge_case_listings):
    assert len(edge_case_listings) == 5
    # Contains: min price, max price, empty fields, extreme values
```

### `test_listings`

10 generic listings for general testing.

```python
def test_generic(test_listings):
    assert len(test_listings) == 10
    # Mixed Portugal/Ukraine data
```

## Event Fixtures

### `event_chain`

Complete event processing chain.

```python
def test_pipeline(event_chain):
    assert len(event_chain) >= 3
    assert event_chain[0].event_type == EventType.RAW_LISTING_RECEIVED
    assert event_chain[-1].event_type == EventType.LISTING_PROCESSED
```

### `raw_listing_event`

Single raw listing event.

```python
def test_raw_processing(raw_listing_event):
    assert raw_listing_event.event_type == EventType.RAW_LISTING_RECEIVED
    assert raw_listing_event.listing_data is not None
```

### `normalized_listing_event`

Single normalized listing event.

```python
def test_normalization(normalized_listing_event):
    assert normalized_listing_event.event_type == EventType.LISTING_NORMALIZED
    assert normalized_listing_event.listing is not None
```

## Seeded Fixtures

For reproducible tests with deterministic data.

### `seeded_listing_factory`

Factory with fixed seed (42).

```python
def test_reproducible(seeded_listing_factory):
    listings1 = seeded_listing_factory.create_batch(5)
    # Re-run will produce identical data
```

### `seeded_listings`

5 pre-generated listings with fixed seed.

```python
def test_deterministic(seeded_listings):
    # Always the same 5 listings
    assert len(seeded_listings) == 5
    assert seeded_listings[0].listing_id == seeded_listings[0].listing_id
```

## Usage Patterns

### Test with Custom Data

```python
def test_custom_price(listing_factory):
    listing = listing_factory.create_listing(
        price=750_000,
        currency="EUR",
        city="Lisboa"
    )
    assert listing.price.amount == 750_000
```

### Test with Preset Data

```python
def test_lisboa_processing(lisboa_apartments):
    for listing in lisboa_apartments:
        # Process each listing
        result = process_listing(listing)
        assert result.status == "success"
```

### Test with Builder

```python
def test_complex_listing(listing_builder):
    listing = (
        listing_builder
        .with_price(1_200_000)
        .in_city("Porto")
        .in_district("Ribeira")
        .with_area(120)
        .with_rooms(4)
        .with_bathrooms(2)
        .with_parking(True)
        .build()
    )
    assert listing.features.parking is True
```

### Test Event Processing

```python
def test_event_flow(event_chain):
    raw, normalized, processed = event_chain[:3]

    assert raw.event_type == EventType.RAW_LISTING_RECEIVED
    assert normalized.event_type == EventType.LISTING_NORMALIZED
    assert processed.event_type == EventType.LISTING_PROCESSED
```

### Test Fraud Detection

```python
def test_fraud_algorithm(fraud_candidates, listing_factory):
    normal_listings = listing_factory.create_batch(10)

    for fraud in fraud_candidates:
        score = calculate_fraud_score(fraud)
        assert score > 0.7  # High fraud score

    for normal in normal_listings:
        score = calculate_fraud_score(normal)
        assert score < 0.3  # Low fraud score
```

## Fixture Composition

Combine multiple fixtures:

```python
def test_market_comparison(lisboa_apartments, kyiv_apartments):
    lisboa_avg = sum(l.price.amount for l in lisboa_apartments) / len(lisboa_apartments)
    kyiv_avg = sum(l.price.amount for l in kyiv_apartments) / len(kyiv_apartments)

    # Portugal market typically more expensive
    assert lisboa_avg > kyiv_avg
```

## Parametrized Tests with Fixtures

```python
@pytest.mark.parametrize("city,expected_count", [
    ("Lisboa", 5),
    ("Porto", 5),
    ("Київ", 5),
    ("Львів", 5),
])
def test_city_apartments(listing_factory, city, expected_count):
    if city in ["Lisboa", "Porto"]:
        method_name = f"create_{city.lower()}_apartments"
    else:
        method_name = f"create_{city.lower()}_apartments"

    method = getattr(listing_factory, method_name)
    listings = method(count=expected_count)
    assert len(listings) == expected_count
```

## Best Practices

1. **Use preset fixtures for common scenarios**
   ```python
   def test_common_case(lisboa_apartments):
       # Fast and convenient
       pass
   ```

2. **Use factory for custom data**
   ```python
   def test_specific_case(listing_factory):
       listing = listing_factory.create_listing(price=1_000_000)
       pass
   ```

3. **Use builder for complex objects**
   ```python
   def test_complex_case(listing_builder):
       listing = listing_builder.with_price(500_000).with_area(100).build()
       pass
   ```

4. **Use seeded fixtures for reproducibility**
   ```python
   def test_regression(seeded_listings):
       # Always same data for regression testing
       pass
   ```

5. **Combine fixtures when needed**
   ```python
   def test_comparison(lisboa_apartments, porto_apartments):
       # Compare two datasets
       pass
   ```

## Configuration

Fixtures are automatically loaded via `conftest.py`:

```python
pytest_plugins = [
    "tests.fixtures.factory_fixtures",
]
```

No manual imports needed! Just add fixtures as test parameters.
