"""
Unit tests for ListingFactory.

Tests the factory's ability to generate realistic test data
with proper validation and edge cases.
"""

from core.models.udm import Listing
from tests.factories.listing_factory import ListingFactory


class TestListingFactory:
    """Test basic ListingFactory functionality."""

    def test_create_listing_default(self):
        """Test creating a listing with default values."""
        factory = ListingFactory()
        listing = factory.create_listing()

        # Verify it's a valid Listing instance
        assert isinstance(listing, Listing)
        assert listing.listing_id is not None
        assert listing.source is not None
        assert listing.type in ["sale", "rent"]
        assert listing.property_type in [
            "apartment",
            "house",
            "commercial",
            "land",
        ]
        assert listing.location is not None
        assert listing.price is not None
        assert listing.price.currency == "RUB"

    def test_create_listing_with_overrides(self):
        """Test creating a listing with custom values."""
        factory = ListingFactory()
        listing = factory.create_listing(
            listing_type="sale",
            property_type="apartment",
            price={"amount": 5_000_000, "currency": "RUB"},
            location={"city": "Москва", "country": "Россия"},
        )

        assert listing.type == "sale"
        assert listing.property_type == "apartment"
        assert listing.price.amount == 5_000_000
        assert listing.location.city == "Москва"

    def test_create_listing_with_custom_listing_id(self):
        """Test creating a listing with specific ID."""
        factory = ListingFactory()
        custom_id = "test-listing-001"
        listing = factory.create_listing(listing_id=custom_id)

        assert listing.listing_id == custom_id

    def test_create_listing_reproducible_with_seed(self):
        """Test that listings are reproducible with seed."""
        factory1 = ListingFactory(seed=42)
        listing1 = factory1.create_listing()

        factory2 = ListingFactory(seed=42)
        listing2 = factory2.create_listing()

        # Same seed should produce same data
        assert listing1.listing_id == listing2.listing_id
        assert listing1.price.amount == listing2.price.amount
        assert listing1.location.city == listing2.location.city

    def test_create_batch(self):
        """Test creating multiple listings at once."""
        factory = ListingFactory()
        count = 5
        listings = factory.create_batch(count)

        assert len(listings) == count
        assert all(isinstance(listing, Listing) for listing in listings)

        # All should have unique IDs
        ids = [listing.listing_id for listing in listings]
        assert len(ids) == len(set(ids))

    def test_create_batch_with_common_params(self):
        """Test creating batch with shared parameters."""
        factory = ListingFactory()
        listings = factory.create_batch(
            3, property_type="apartment", listing_type="sale"
        )

        assert all(
            listing.property_type == "apartment" for listing in listings
        )
        assert all(listing.type == "sale" for listing in listings)


class TestMoscowApartments:
    """Test Moscow apartment generation."""

    def test_create_moscow_apartments_default(self):
        """Test creating Moscow apartments with defaults."""
        factory = ListingFactory()
        apartments = factory.create_moscow_apartments(count=3)

        assert len(apartments) == 3
        for apt in apartments:
            assert apt.location.city == "Москва"
            assert apt.property_type == "apartment"
            assert apt.type == "sale"
            assert apt.price.price_per_sqm is not None
            # Moscow latitude range
            assert 55.55 <= apt.location.coordinates.lat <= 55.88
            # Moscow longitude range
            assert 37.37 <= apt.location.coordinates.lng <= 37.84

    def test_create_moscow_apartments_specific_district(self):
        """Test creating apartments in specific Moscow district."""
        factory = ListingFactory()
        district = "Центральный"
        apartments = factory.create_moscow_apartments(
            count=2, district=district
        )

        assert len(apartments) == 2
        for apt in apartments:
            assert district in apt.location.address
            # Central district has higher prices (300k-500k/sqm)
            assert apt.price.price_per_sqm >= 300_000

    def test_moscow_apartments_price_ranges(self):
        """Test that Moscow apartments have realistic price ranges."""
        factory = ListingFactory(seed=42)
        apartments = factory.create_moscow_apartments(count=10)

        for apt in apartments:
            # Typical Moscow apartment prices: 2M - 50M RUB
            assert 1_000_000 <= apt.price.amount <= 100_000_000
            # Price per sqm should be in reasonable range
            assert 100_000 <= apt.price.price_per_sqm <= 600_000


class TestSuspiciousListings:
    """Test fraud scenario listings."""

    def test_create_suspicious_listings(self):
        """Test creating listings with fraud indicators."""
        factory = ListingFactory()
        suspicious = factory.create_suspicious_listings(count=5)

        assert len(suspicious) == 5
        for listing in suspicious:
            # All should have fraud scores
            assert listing.fraud_score is not None
            assert 0 <= listing.fraud_score <= 100
            # Most should have high fraud scores
            assert listing.fraud_score >= 40

    def test_unrealistic_price_scenario(self):
        """Test unrealistic price fraud scenario."""
        factory = ListingFactory(seed=42)
        # Generate enough to likely get unrealistic price scenario
        suspicious = factory.create_suspicious_listings(count=10)

        # At least some should have suspiciously low prices
        low_price_listings = [
            listing
            for listing in suspicious
            if listing.price.amount < 2_000_000
        ]
        assert len(low_price_listings) > 0

    def test_no_photos_scenario(self):
        """Test no photos fraud scenario."""
        factory = ListingFactory(seed=123)
        suspicious = factory.create_suspicious_listings(count=10)

        # At least some should have no photos
        no_photo_listings = [
            listing
            for listing in suspicious
            if listing.media and len(listing.media.images) == 0
        ]
        assert len(no_photo_listings) > 0


class TestEdgeCases:
    """Test edge case listings."""

    def test_create_edge_cases(self):
        """Test creating edge case listings."""
        factory = ListingFactory()
        edge_cases = factory.create_edge_cases()

        assert len(edge_cases) == 3
        assert all(isinstance(case, Listing) for case in edge_cases)

    def test_minimal_listing(self):
        """Test minimal listing with optional fields missing."""
        factory = ListingFactory()
        edge_cases = factory.create_edge_cases()

        # First edge case is minimal
        minimal = edge_cases[0]
        assert minimal.description is None
        assert minimal.media is None
        assert minimal.fraud_score is None

    def test_maximal_listing(self):
        """Test maximal listing with all fields populated."""
        factory = ListingFactory()
        edge_cases = factory.create_edge_cases()

        # Second edge case is maximal
        maximal = edge_cases[1]
        assert maximal.description is not None
        assert len(maximal.description) > 0
        assert maximal.media is not None
        assert len(maximal.media.images) > 0
        assert maximal.fraud_score is not None

    def test_zero_price_listing(self):
        """Test listing with zero price."""
        factory = ListingFactory()
        edge_cases = factory.create_edge_cases()

        # Third edge case is zero price
        zero_price = edge_cases[2]
        assert zero_price.price.amount == 0.0
        assert zero_price.fraud_score is not None
        assert zero_price.fraud_score >= 80  # High fraud score


class TestDataRealism:
    """Test that generated data is realistic."""

    def test_russian_cities(self):
        """Test that listings use real Russian cities."""
        factory = ListingFactory(seed=42)
        listings = factory.create_batch(20)

        cities = [listing.location.city for listing in listings]
        expected_cities = [
            "Москва",
            "Санкт-Петербург",
            "Екатеринбург",
            "Новосибирск",
            "Казань",
            "Нижний Новгород",
            "Челябинск",
            "Самара",
            "Омск",
            "Ростов-на-Дону",
        ]

        # All cities should be from expected list
        for city in cities:
            assert city in expected_cities

    def test_price_currency_is_rub(self):
        """Test that all prices are in RUB."""
        factory = ListingFactory()
        listings = factory.create_batch(10)

        assert all(
            listing.price.currency == "RUB" for listing in listings
        )

    def test_coordinates_in_russia(self):
        """Test that coordinates are within Russia."""
        factory = ListingFactory()
        listings = factory.create_batch(20)

        for listing in listings:
            if listing.location.coordinates:
                # Rough bounds for European Russia
                assert 50 <= listing.location.coordinates.lat <= 65
                assert 25 <= listing.location.coordinates.lng <= 45

    def test_source_platforms_realistic(self):
        """Test that source platforms are real Russian real estate sites."""
        factory = ListingFactory()
        listings = factory.create_batch(20)

        expected_platforms = [
            "cian.ru",
            "avito.ru",
            "domofond.ru",
            "yandex.ru/realty",
        ]

        for listing in listings:
            assert listing.source.platform in expected_platforms

    def test_media_images_have_urls(self):
        """Test that media images have valid URLs."""
        factory = ListingFactory()
        listings = factory.create_batch(10)

        for listing in listings:
            if listing.media and listing.media.images:
                for image in listing.media.images:
                    assert image.url.startswith("http")


class TestFactoryConsistency:
    """Test factory consistency and validation."""

    def test_all_required_fields_present(self):
        """Test that all required Listing fields are populated."""
        factory = ListingFactory()
        listing = factory.create_listing()

        # Required fields from Listing model
        assert listing.listing_id is not None
        assert listing.source is not None
        assert listing.source.plugin_id is not None
        assert listing.source.platform is not None
        assert listing.type is not None
        assert listing.property_type is not None
        assert listing.location is not None
        assert listing.price is not None
        assert listing.price.amount is not None
        assert listing.price.currency is not None

    def test_fraud_score_range(self):
        """Test that fraud scores are in valid range."""
        factory = ListingFactory()
        suspicious = factory.create_suspicious_listings(count=10)

        for listing in suspicious:
            if listing.fraud_score is not None:
                assert 0 <= listing.fraud_score <= 100

    def test_property_types_valid(self):
        """Test that property types are from valid set."""
        factory = ListingFactory()
        listings = factory.create_batch(20)

        valid_types = ["apartment", "house", "commercial", "land"]
        for listing in listings:
            assert listing.property_type in valid_types

    def test_listing_types_valid(self):
        """Test that listing types are from valid set."""
        factory = ListingFactory()
        listings = factory.create_batch(20)

        valid_types = ["sale", "rent"]
        for listing in listings:
            assert listing.type in valid_types
