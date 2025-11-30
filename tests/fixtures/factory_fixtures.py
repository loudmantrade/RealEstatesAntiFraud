"""
Factory Fixtures for Testing

This module provides pytest fixtures for all factories and builders,
making test data generation convenient and consistent across the test suite.

Usage:
    def test_with_factory(listing_factory):
        listing = listing_factory.create_listing(price=1_000_000)
        assert listing.price.amount == 1_000_000

    def test_with_preset_data(lisboa_apartments):
        assert len(lisboa_apartments) == 5
        assert all(l.location.city == "Lisboa" for l in lisboa_apartments)

    def test_with_builder(listing_builder):
        listing = listing_builder.with_price(500_000).in_city("Porto").build()
        assert listing.price.amount == 500_000
"""

import pytest

from tests.builders.listing_builder import ListingBuilder
from tests.factories.event_factory import EventFactory
from tests.factories.listing_factory import ListingFactory

# ============================================================================
# Factory Fixtures
# ============================================================================


@pytest.fixture
def listing_factory():
    """
    ListingFactory instance for generating real estate listings.

    Returns:
        ListingFactory: Factory with methods for creating listings for
            Portugal (Lisboa, Porto) and Ukraine (Kyiv, Lviv) markets.

    Example:
        def test_price_validation(listing_factory):
            listing = listing_factory.create_listing(price=250_000)
            assert listing.price.amount == 250_000
    """
    return ListingFactory()


@pytest.fixture
def event_factory():
    """
    EventFactory instance for generating listing processing events.

    Returns:
        EventFactory: Factory for creating various event types
            (RawListingEvent, NormalizedListingEvent, etc.)

    Example:
        def test_event_processing(event_factory):
            event = event_factory.create_raw_listing_event()
            assert event.event_type == EventType.RAW_LISTING_RECEIVED
    """
    return EventFactory()


@pytest.fixture
def listing_builder():
    """
    ListingBuilder instance for fluent listing construction.

    Returns:
        ListingBuilder: Builder with chainable methods for
            incrementally constructing complex listings.

    Example:
        def test_builder(listing_builder):
            listing = (
                listing_builder
                .with_price(400_000)
                .in_city("Lisboa")
                .with_area(85)
                .build()
            )
            assert listing.price.amount == 400_000
    """
    return ListingBuilder()


# ============================================================================
# Portugal Market Fixtures
# ============================================================================


@pytest.fixture
def lisboa_apartments(listing_factory):
    """
    5 pre-generated Lisboa apartments for testing.

    Returns:
        List[Listing]: 5 listings from various Lisboa districts
            (Baixa, Chiado, Alfama, Belém, Parque das Nações)

    Example:
        def test_lisboa_data(lisboa_apartments):
            assert len(lisboa_apartments) == 5
            assert all(l.location.city == "Lisboa" for l in lisboa_apartments)
    """
    return listing_factory.create_lisboa_apartments(count=5)


@pytest.fixture
def porto_apartments(listing_factory):
    """
    5 pre-generated Porto apartments for testing.

    Returns:
        List[Listing]: 5 listings from various Porto districts
            (Ribeira, Boavista, Cedofeita, Foz, Matosinhos)

    Example:
        def test_porto_data(porto_apartments):
            assert len(porto_apartments) == 5
            assert all(l.location.city == "Porto" for l in porto_apartments)
    """
    return listing_factory.create_porto_apartments(count=5)


@pytest.fixture
def portuguese_cities(listing_factory):
    """
    10 listings from various Portuguese cities for testing.

    Returns:
        List[Listing]: 10 listings from Lisboa, Porto, Faro, Coimbra, Braga

    Example:
        def test_portuguese_cities(portuguese_cities):
            assert len(portuguese_cities) == 10
            cities = {l.location.city for l in portuguese_cities}
            assert "Lisboa" in cities or "Porto" in cities
    """
    return listing_factory.create_regional_listings(city="Lisboa", count=10)


# ============================================================================
# Ukraine Market Fixtures
# ============================================================================


@pytest.fixture
def kyiv_apartments(listing_factory):
    """
    5 pre-generated Kyiv apartments for testing.

    Returns:
        List[Listing]: 5 listings from various Kyiv districts
            (Печерськ, Поділ, Шевченківський, Оболонь, Дарницький)

    Example:
        def test_kyiv_data(kyiv_apartments):
            assert len(kyiv_apartments) == 5
            assert all(l.location.city == "Київ" for l in kyiv_apartments)
    """
    return listing_factory.create_kyiv_apartments(count=5)


@pytest.fixture
def lviv_apartments(listing_factory):
    """
    5 pre-generated Lviv apartments for testing.

    Returns:
        List[Listing]: 5 listings from various Lviv districts
            (Личаківський, Галицький, Франківський)

    Example:
        def test_lviv_data(lviv_apartments):
            assert len(lviv_apartments) == 5
            assert all(l.location.city == "Львів" for l in lviv_apartments)
    """
    return listing_factory.create_lviv_apartments(count=5)


@pytest.fixture
def ukrainian_cities(listing_factory):
    """
    10 listings from various Ukrainian cities for testing.

    Returns:
        List[Listing]: 10 listings from Київ, Львів, Одеса, Харків, Дніпро

    Example:
        def test_ukrainian_cities(ukrainian_cities):
            assert len(ukrainian_cities) == 10
            cities = {l.location.city for l in ukrainian_cities}
            assert "Київ" in cities or "Львів" in cities
    """
    return listing_factory.create_regional_listings(city="Київ", count=10)


# ============================================================================
# Specialized Test Data Fixtures
# ============================================================================


@pytest.fixture
def fraud_candidates(listing_factory):
    """
    3 pre-generated fraud candidate listings for fraud detection testing.

    Returns:
        List[Listing]: 3 listings with fraud patterns (unrealistic_price type)

    Example:
        def test_fraud_detection(fraud_candidates):
            assert len(fraud_candidates) == 3
            # All should have suspicious characteristics
    """
    return listing_factory.create_fraud_candidates(count=3, fraud_type="unrealistic_price")


@pytest.fixture
def edge_case_listings(listing_factory):
    """
    5 edge case listings for boundary testing.

    Returns:
        List[Listing]: 5 listings with edge cases
            (minimum price, maximum price, empty fields, etc.)

    Example:
        def test_edge_cases(edge_case_listings):
            assert len(edge_case_listings) == 5
            # Should handle extreme values gracefully
    """
    return listing_factory.create_edge_cases(count=5)


@pytest.fixture
def test_listings(listing_factory):
    """
    10 generic test listings with diverse characteristics.

    Returns:
        List[Listing]: 10 listings with varied properties for general testing

    Example:
        def test_generic_processing(test_listings):
            assert len(test_listings) == 10
            # Mixed Portugal/Ukraine data
    """
    return listing_factory.create_batch(count=10)


# ============================================================================
# Event Fixtures
# ============================================================================


@pytest.fixture
def event_chain(event_factory):
    """
    Complete event chain for testing event processing pipelines.

    Returns:
        List[Event]: Chain of events from raw to processed
            (RawListingEvent → NormalizedListingEvent → ProcessedListingEvent)

    Example:
        def test_event_pipeline(event_chain):
            assert len(event_chain) >= 3
            assert event_chain[0].event_type == EventType.RAW_LISTING_RECEIVED
    """
    return event_factory.create_event_chain()


@pytest.fixture
def raw_listing_event(event_factory):
    """
    Single raw listing event for testing initial processing.

    Returns:
        RawListingEvent: Event representing a newly received listing

    Example:
        def test_raw_event(raw_listing_event):
            assert raw_listing_event.metadata.event_type == 'raw_listing'
    """
    return event_factory.create_raw_event()


@pytest.fixture
def normalized_listing_event(event_factory):
    """
    Single normalized listing event for testing normalization.

    Returns:
        NormalizedListingEvent: Event with normalized listing data

    Example:
        def test_normalized_event(normalized_listing_event):
            assert normalized_listing_event.metadata.event_type == 'normalized_listing'
    """
    return event_factory.create_normalized_event()


# ============================================================================
# Seeded Fixtures for Reproducible Tests
# ============================================================================


@pytest.fixture
def seeded_listing_factory():
    """
    ListingFactory with fixed seed for reproducible tests.

    Returns:
        ListingFactory: Factory that generates identical data on each run

    Example:
        def test_reproducible(seeded_listing_factory):
            listings1 = seeded_listing_factory.create_batch(5)
            # Re-run will produce same data
    """
    return ListingFactory(seed=42)


@pytest.fixture
def seeded_listings(seeded_listing_factory):
    """
    5 pre-generated listings with fixed seed for reproducible tests.

    Returns:
        List[Listing]: Always the same 5 listings for deterministic testing

    Example:
        def test_deterministic(seeded_listings):
            # This test will always see the same data
            assert len(seeded_listings) == 5
    """
    return seeded_listing_factory.create_batch(count=5)
