"""
Factory Usage Examples

Practical examples demonstrating how to use test data factories
in various scenarios. These examples can be copied and adapted
for your own tests.

Run with: pytest tests/examples/factory_usage_examples.py -v
"""

import pytest

from core.models.udm import Listing
from tests.factories.event_factory import EventFactory
from tests.factories.listing_factory import ListingFactory

# =============================================================================
# BASIC USAGE EXAMPLES
# =============================================================================


def test_example_01_single_listing(listing_factory):
    """Example 1: Create a single listing with default values."""
    listing = listing_factory.create_listing()

    # Factory generates all required fields automatically
    assert listing.listing_id is not None
    assert listing.description is not None
    assert listing.price.amount > 0
    assert listing.location.city is not None
    print(f"Created listing in {listing.location.city}: {listing.price.amount} {listing.price.currency}")


def test_example_02_batch_creation(listing_factory):
    """Example 2: Create multiple listings at once."""
    listings = listing_factory.create_batch(10)

    assert len(listings) == 10
    assert all(isinstance(listing, Listing) for listing in listings)
    print(f"Created {len(listings)} listings")


def test_example_03_custom_price(listing_factory):
    """Example 3: Override specific fields like price."""
    listing = listing_factory.create_listing(price={"amount": 1_500_000, "currency": "EUR"})

    assert listing.price.amount == 1_500_000
    assert listing.price.currency == "EUR"
    print(f"Listing price: {listing.price.amount} {listing.price.currency}")


def test_example_04_custom_location(listing_factory):
    """Example 4: Override location fields."""
    listing = listing_factory.create_listing(location={"city": "Lisboa", "country": "Portugal", "address": "Chiado"})

    assert listing.location.city == "Lisboa"
    assert listing.location.country == "Portugal"
    assert listing.location.address == "Chiado"
    print(f"Listing location: {listing.location.city}, {listing.location.address}")


# =============================================================================
# REGIONAL EXAMPLES
# =============================================================================


def test_example_05_lisboa_apartments(listing_factory):
    """Example 5: Create Lisboa apartment listings."""
    listings = listing_factory.create_lisboa_apartments(count=5)

    assert len(listings) == 5
    assert all(l.location.city == "Lisboa" for l in listings)

    # Check price distribution
    prices = [l.price.amount for l in listings]
    avg_price = sum(prices) / len(prices)
    print(f"Average Lisboa price: {avg_price:,.2f} EUR")


def test_example_06_specific_district(listing_factory):
    """Example 6: Create listings in specific district."""
    listings = listing_factory.create_lisboa_apartments(count=3, district="Baixa")

    # District is included in the address field
    assert all("Baixa" in l.location.address for l in listings)
    print(f"Created 3 apartments in Baixa district")


def test_example_07_porto_apartments(listing_factory):
    """Example 7: Create Porto apartment listings."""
    listings = listing_factory.create_porto_apartments(count=5)

    assert len(listings) == 5
    assert all(l.location.city == "Porto" for l in listings)


def test_example_08_kyiv_apartments(listing_factory):
    """Example 8: Create Kyiv (Ukraine) apartment listings."""
    listings = listing_factory.create_kyiv_apartments(count=5)

    assert len(listings) == 5
    assert all(l.location.city == "Київ" for l in listings)
    assert all(l.location.country == "Ukraine" for l in listings)


def test_example_09_regional_cities(listing_factory):
    """Example 9: Create listings for regional cities."""
    braga_listings = listing_factory.create_regional_listings(count=3, city="Braga")
    odesa_listings = listing_factory.create_regional_listings(count=3, city="Одеса")

    assert all(l.location.city == "Braga" for l in braga_listings)
    assert all(l.location.city == "Одеса" for l in odesa_listings)


# =============================================================================
# FRAUD DETECTION EXAMPLES
# =============================================================================


def test_example_10_fraud_candidates(listing_factory):
    """Example 10: Create fraud candidate listings."""
    fraud_listings = listing_factory.create_fraud_candidates(count=5)

    # All should have elevated fraud scores
    assert all(l.fraud_score > 0.5 for l in fraud_listings)
    print(f"Average fraud score: {sum(l.fraud_score for l in fraud_listings) / 5:.2f}")


def test_example_11_unrealistic_price(listing_factory):
    """Example 11: Create listings with unrealistic prices."""
    fraud_listings = listing_factory.create_fraud_candidates(count=3, fraud_type="unrealistic_price")

    # Check that prices are flagged as fraudulent
    for listing in fraud_listings:
        assert listing.fraud_score > 50  # High fraud score
        if listing.price.price_per_sqm:
            print(
                f"Suspicious: {listing.price.price_per_sqm:.2f} {listing.price.currency}/sqm - Fraud score: {listing.fraud_score:.1f}"
            )
        else:
            print(
                f"Suspicious price: {listing.price.amount:.2f} {listing.price.currency} - Fraud score: {listing.fraud_score:.1f}"
            )


def test_example_12_no_photos(listing_factory):
    """Example 12: Create listings with suspicious characteristics."""
    fraud_listings = listing_factory.create_fraud_candidates(count=3, fraud_type="missing_contact")

    # All fraud candidates should have fraud_score set
    assert all(l.fraud_score is not None for l in fraud_listings)
    avg_score = sum(l.fraud_score for l in fraud_listings) / len(fraud_listings)
    print(f"Fraud candidates created with avg score: {avg_score:.1f}")


def test_example_13_duplicates(listing_factory):
    """Example 13: Create listings with duplicate photos."""
    fraud_listings = listing_factory.create_fraud_candidates(count=5, fraud_type="duplicate_photos")

    # All should have high fraud scores indicating duplicates
    assert all(l.fraud_score > 50 for l in fraud_listings)
    cities = {l.location.city for l in fraud_listings}
    print(f"Created {len(fraud_listings)} fraud candidates across {len(cities)} cities")


# =============================================================================
# EDGE CASE EXAMPLES
# =============================================================================


def test_example_14_edge_cases(listing_factory):
    """Example 14: Create edge case listings."""
    edge_cases = listing_factory.create_edge_cases(count=5)

    # Edge cases have unusual characteristics
    assert len(edge_cases) == 5
    print(f"Created {len(edge_cases)} edge case listings")


# =============================================================================
# ADVANCED PATTERNS
# =============================================================================


def test_example_15_mixed_dataset(listing_factory):
    """Example 15: Create mixed dataset for comprehensive testing."""
    # Combine different types
    lisboa = listing_factory.create_lisboa_apartments(10)
    porto = listing_factory.create_porto_apartments(5)
    fraud = listing_factory.create_fraud_candidates(3)
    edges = listing_factory.create_edge_cases(2)

    all_listings = lisboa + porto + fraud + edges
    assert len(all_listings) == 20

    # Analyze distribution
    cities = {}
    for listing in all_listings:
        city = listing.location.city
        cities[city] = cities.get(city, 0) + 1

    print(f"City distribution: {cities}")


def test_example_16_price_analysis(listing_factory):
    """Example 16: Analyze price distribution."""
    listings = listing_factory.create_lisboa_apartments(20)

    # Calculate statistics from price_per_sqm when available
    prices_per_sqm = [l.price.price_per_sqm for l in listings if l.price.price_per_sqm]

    if prices_per_sqm:
        avg = sum(prices_per_sqm) / len(prices_per_sqm)
        min_price = min(prices_per_sqm)
        max_price = max(prices_per_sqm)
        print(f"Price per sqm: {min_price:.2f} - {max_price:.2f} EUR (avg: {avg:.2f})")
        assert 1000 < avg < 15000  # Reasonable range
    else:
        prices = [l.price.amount for l in listings]
        avg = sum(prices) / len(prices)
        print(f"Average price: {avg:,.2f} EUR")


def test_example_17_filter_by_criteria(listing_factory):
    """Example 17: Filter generated listings by criteria."""
    all_listings = listing_factory.create_batch(50)

    # Filter by price range
    expensive = [l for l in all_listings if l.price.amount > 500_000]
    affordable = [l for l in all_listings if l.price.amount <= 300_000]

    print(f"Expensive (>500K): {len(expensive)}, Affordable (≤300K): {len(affordable)}")


@pytest.fixture
def market_dataset(listing_factory):
    """Example 18: Create reusable fixture with market data."""
    return {
        "lisboa": listing_factory.create_lisboa_apartments(20),
        "porto": listing_factory.create_porto_apartments(15),
        "kyiv": listing_factory.create_kyiv_apartments(10),
    }


def test_example_18_market_comparison(market_dataset):
    """Example 18: Compare markets using fixture."""
    # Calculate average prices by city
    for city, listings in market_dataset.items():
        avg_price = sum(l.price.amount for l in listings) / len(listings)
        print(f"{city.capitalize()} average: {avg_price:,.2f} EUR")


# =============================================================================
# EVENT FACTORY EXAMPLES
# =============================================================================


def test_example_19_raw_event(event_factory):
    """Example 19: Create raw listing event."""
    event = event_factory.create_raw_event(platform="cian")

    assert event.metadata.event_type == "raw_listing"
    assert event.metadata.source_platform is not None
    print(f"Event: {event.metadata.event_type} from {event.metadata.source_platform}")


def test_example_20_event_chain(event_factory):
    """Example 20: Create complete event chain."""
    events = event_factory.create_event_chain()

    # Verify chain (returns list of 4 events)
    assert len(events) == 4
    assert events[0].metadata.event_type == "raw_listing"
    assert events[1].metadata.event_type == "normalized_listing"
    assert events[2].metadata.event_type == "processed_listing"
    assert events[3].metadata.event_type == "fraud_detected"

    # Check trace_id correlation
    trace_ids = [e.metadata.trace_id for e in events]
    assert len(set(trace_ids)) == 1, "All events should share the same trace_id"

    print(f"Event chain created with trace_id: {trace_ids[0]}")


def test_example_21_batch_events(event_factory):
    """Example 21: Create batch of events."""
    events = event_factory.create_batch(count=10, event_type="raw", platform="avito")

    assert len(events) == 10
    assert all(e.metadata.event_type == "raw_listing" for e in events)
    # Verify all events have platforms set
    assert all(e.metadata.source_platform is not None for e in events)


# =============================================================================
# SEEDED GENERATION EXAMPLES
# =============================================================================


def test_example_22_reproducible_data():
    """Example 22: Generate reproducible data with seed."""
    # Same seed = same data
    factory1 = ListingFactory(seed=42)
    listing1 = factory1.create_listing()

    factory2 = ListingFactory(seed=42)
    listing2 = factory2.create_listing()

    # Should generate identical listings
    assert listing1.listing_id == listing2.listing_id
    assert listing1.price.amount == listing2.price.amount
    print("Reproducible generation verified!")


def test_example_23_different_seeds():
    """Example 23: Different seeds produce different data."""
    factory1 = ListingFactory(seed=1)
    factory2 = ListingFactory(seed=2)

    listing1 = factory1.create_listing()
    listing2 = factory2.create_listing()

    # Different seeds = different data
    assert listing1.listing_id != listing2.listing_id or listing1.price.amount != listing2.price.amount
    print("Different seeds produce different data")


# =============================================================================
# PERFORMANCE EXAMPLES
# =============================================================================


def test_example_24_large_dataset_performance(listing_factory):
    """Example 24: Generate large dataset efficiently."""
    import time

    start = time.time()
    listings = listing_factory.create_batch(1000)
    duration = time.time() - start

    assert len(listings) == 1000
    print(f"Generated 1000 listings in {duration:.2f} seconds")
    assert duration < 5.0  # Should be fast


# =============================================================================
# INTEGRATION EXAMPLES
# =============================================================================


@pytest.fixture
def sample_database(db_session, listing_factory):
    """Example 25: Populate database for testing."""
    # NOTE: This example requires database infrastructure that's not yet implemented
    pytest.skip("Database integration not yet available")

    # Create diverse dataset
    listings = listing_factory.create_batch(50)

    # Add to database (implementation pending)
    db_session.commit()
    yield db_session

    # Cleanup
    from core.database.models import ListingModel

    db_session.query(ListingModel).delete()
    db_session.commit()


def test_example_25_database_query(sample_database):
    """Example 25: Query factory-generated data from database."""
    from core.database.models import ListingModel

    # Query all listings
    count = sample_database.query(ListingModel).count()
    assert count == 50

    # Query by price range
    expensive = sample_database.query(ListingModel).filter(ListingModel.price_amount > 500_000).all()

    print(f"Found {len(expensive)} expensive listings (>500K EUR)")


# =============================================================================
# BEST PRACTICES EXAMPLES
# =============================================================================


def test_example_26_clear_test_intent(listing_factory):
    """
    Example 26: Write tests with clear intent.

    Good practice: Test name and implementation clearly show what's being tested.
    """
    # Create luxury Lisboa apartment
    luxury_apartment = listing_factory.create_listing(
        price={"amount": 2_000_000, "currency": "EUR", "price_per_sqm": 10000.0},
        location={"city": "Lisboa", "country": "Portugal", "address": "Chiado"},
        property_type="apartment",
    )

    # Luxury apartments should be expensive per sqm
    if luxury_apartment.price.price_per_sqm:
        assert luxury_apartment.price.price_per_sqm > 8_000, "Luxury apartments should exceed 8K EUR/sqm"
        print(f"Luxury apartment: {luxury_apartment.price.price_per_sqm:.2f} EUR/sqm")
    else:
        assert luxury_apartment.price.amount >= 2_000_000
        print(f"Luxury apartment: {luxury_apartment.price.amount:,.0f} EUR")


def test_example_27_minimal_overrides(listing_factory):
    """
    Example 27: Override only what's necessary for the test.

    Good practice: Let factory handle defaults, override only test-specific values.
    """
    # Only specify the price we're testing
    listing = listing_factory.create_listing(price={"amount": 750_000, "currency": "EUR"})

    # Factory handles all other fields realistically
    assert listing.price.amount == 750_000
    assert listing.location.city is not None  # Generated
    assert listing.property_type is not None  # Generated
    assert listing.listing_id is not None  # Generated


def test_example_28_use_appropriate_method(listing_factory):
    """
    Example 28: Use specialized methods when available.

    Good practice: Use create_lisboa_apartments() instead of
    create_listing() with Lisboa overrides.
    """
    # ✅ Better: Use specialized method
    listings = listing_factory.create_lisboa_apartments(count=5)

    # All are in Lisboa with realistic prices
    assert all(l.location.city == "Lisboa" for l in listings)

    # Prices are in realistic range for Lisboa
    for listing in listings:
        if listing.price.price_per_sqm:
            assert 3000 < listing.price.price_per_sqm < 10000
        else:
            # Check total price is reasonable for Lisboa
            assert 100_000 < listing.price.amount < 2_000_000


# =============================================================================
# HELPER EXAMPLES
# =============================================================================


def print_listing_summary(listing: Listing):
    """Helper: Print readable listing summary."""
    print(f"\n{'=' * 60}")
    print(f"ID: {listing.listing_id}")
    print(f"Location: {listing.location.city}, {listing.location.country}")
    if listing.location.address:
        print(f"Address: {listing.location.address}")
    print(f"Price: {listing.price.amount:,.2f} {listing.price.currency}")
    if listing.price.price_per_sqm:
        print(f"Price/sqm: {listing.price.price_per_sqm:,.2f} {listing.price.currency}")
    print(f"Type: {listing.type} - {listing.property_type}")
    if listing.fraud_score is not None:
        print(f"Fraud Score: {listing.fraud_score:.2f}")
    if listing.media and listing.media.images:
        print(f"Images: {len(listing.media.images)}")
    if listing.description:
        print(f"Description: {listing.description[:80]}...")
    print(f"{'=' * 60}")


def test_example_29_visual_inspection(listing_factory):
    """Example 29: Generate listing for manual inspection."""
    listing = listing_factory.create_listing(
        location={"city": "Lisboa", "country": "Portugal", "address": "Baixa"},
        price={"amount": 500_000, "currency": "EUR", "price_per_sqm": 5000.0},
        property_type="apartment",
    )

    print_listing_summary(listing)


if __name__ == "__main__":
    """
    Run examples directly for quick testing:
    python tests/examples/factory_usage_examples.py
    """
    print("=" * 70)
    print("Factory Usage Examples - Quick Test")
    print("=" * 70)

    factory = ListingFactory()

    # Example 1: Basic listing
    print("\n1. Basic Listing:")
    listing = factory.create_listing()
    print(
        f"   Created: {listing.property_type} in {listing.location.city} - {listing.price.amount:,.0f} {listing.price.currency}"
    )

    # Example 2: Batch creation
    print("\n2. Batch Creation:")
    listings = factory.create_batch(5)
    print(f"   Created {len(listings)} listings")

    # Example 3: Lisboa apartments
    print("\n3. Lisboa Apartments:")
    lisboa = factory.create_lisboa_apartments(3)
    print(f"   Created {len(lisboa)} Lisboa apartments")
    for l in lisboa:
        address = l.location.address.split(",")[0] if l.location.address else "Unknown"
        print(f"   - {address}: {l.price.amount:,.0f} EUR")

    # Example 4: Fraud candidates
    print("\n4. Fraud Candidates:")
    fraud = factory.create_fraud_candidates(2)
    for l in fraud:
        print(f"   - Fraud score: {l.fraud_score:.2f}")

    print("\n" + "=" * 70)
    print("Run full test suite with: pytest tests/examples/factory_usage_examples.py -v")
    print("=" * 70)
