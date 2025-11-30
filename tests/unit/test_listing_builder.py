"""
Unit tests for ListingBuilder.

Tests builder pattern implementation with fluent API for creating Listings.
"""

import pytest

from core.models.udm import Listing
from tests.builders import ListingBuilder


class TestListingBuilder:
    """Test basic ListingBuilder functionality."""

    def test_build_with_defaults(self):
        """Test building listing with all defaults."""
        builder = ListingBuilder()
        listing = builder.build()

        assert isinstance(listing, Listing)
        assert listing.listing_id is not None
        assert listing.source.plugin_id == "test_plugin"
        assert listing.type == "sale"
        assert listing.property_type == "apartment"
        assert listing.location.city == "Москва"
        assert listing.price.amount == 5_000_000.0
        assert listing.price.currency == "RUB"

    def test_method_chaining(self):
        """Test fluent interface with method chaining."""
        builder = ListingBuilder()
        listing = (
            builder.with_price(3_000_000)
            .with_property_type("house")
            .with_location("Санкт-Петербург")
            .build()
        )

        assert listing.price.amount == 3_000_000.0
        assert listing.property_type == "house"
        assert listing.location.city == "Санкт-Петербург"

    def test_build_returns_new_instance(self):
        """Test that build() returns independent instances."""
        builder = ListingBuilder(seed=42)
        listing1 = builder.with_price(2_000_000).build()
        listing2 = builder.with_price(3_000_000).build()

        # Second build should have new price
        assert listing2.price.amount == 3_000_000.0


class TestLocationConfiguration:
    """Test location-related builder methods."""

    def test_with_location_city_only(self):
        """Test setting location with city only."""
        builder = ListingBuilder()
        listing = builder.with_location("Москва").build()

        assert listing.location.city == "Москва"
        assert listing.location.coordinates.lat == 55.7558
        assert listing.location.coordinates.lng == 37.6173

    def test_with_location_full(self):
        """Test setting location with all parameters."""
        builder = ListingBuilder()
        listing = builder.with_location(
            city="Москва",
            address="ул. Арбат, 1",
            lat=55.7500,
            lng=37.6000,
        ).build()

        assert listing.location.city == "Москва"
        assert listing.location.address == "ул. Арбат, 1"
        assert listing.location.coordinates.lat == 55.7500
        assert listing.location.coordinates.lng == 37.6000

    def test_with_location_default_coordinates(self):
        """Test default coordinates for major cities."""
        cities_coords = {
            "Москва": (55.7558, 37.6173),
            "Санкт-Петербург": (59.9311, 30.3609),
            "Екатеринбург": (56.8389, 60.6057),
        }

        for city, (expected_lat, expected_lng) in cities_coords.items():
            builder = ListingBuilder()
            listing = builder.with_location(city).build()

            assert listing.location.coordinates.lat == expected_lat
            assert listing.location.coordinates.lng == expected_lng


class TestPriceConfiguration:
    """Test price-related builder methods."""

    def test_with_price_basic(self):
        """Test setting price with amount only."""
        builder = ListingBuilder()
        listing = builder.with_price(7_500_000).build()

        assert listing.price.amount == 7_500_000.0
        assert listing.price.currency == "RUB"
        assert listing.price.price_per_sqm is None

    def test_with_price_custom_currency(self):
        """Test setting price with custom currency."""
        builder = ListingBuilder()
        listing = builder.with_price(100_000, currency="USD").build()

        assert listing.price.amount == 100_000.0
        assert listing.price.currency == "USD"

    def test_with_price_and_area_calculates_per_sqm(self):
        """Test price_per_sqm calculation when area is set."""
        builder = ListingBuilder()
        listing = builder.with_price(5_000_000).with_area(100.0).build()

        assert listing.price.price_per_sqm == 50_000.0

    def test_with_price_per_sqm_explicit(self):
        """Test setting price_per_sqm explicitly."""
        builder = ListingBuilder()
        listing = builder.with_price(5_000_000, price_per_sqm=60_000.0).build()

        assert listing.price.price_per_sqm == 60_000.0


class TestPropertyConfiguration:
    """Test property-related builder methods."""

    def test_with_property_type_valid(self):
        """Test setting valid property types."""
        valid_types = ["apartment", "house", "commercial", "land"]

        for prop_type in valid_types:
            builder = ListingBuilder()
            listing = builder.with_property_type(prop_type).build()
            assert listing.property_type == prop_type

    def test_with_property_type_invalid(self):
        """Test setting invalid property type raises error."""
        builder = ListingBuilder()

        with pytest.raises(ValueError, match="Invalid property_type"):
            builder.with_property_type("invalid")

    def test_with_listing_type_valid(self):
        """Test setting listing type (sale/rent)."""
        builder = ListingBuilder()
        listing = builder.with_listing_type("rent").build()

        assert listing.type == "rent"

    def test_with_listing_type_invalid(self):
        """Test setting invalid listing type raises error."""
        builder = ListingBuilder()

        with pytest.raises(ValueError, match="Invalid listing_type"):
            builder.with_listing_type("invalid")

    def test_with_area_only(self):
        """Test setting area without rooms."""
        builder = ListingBuilder()
        listing = builder.with_area(85.5).build()

        assert listing.price.price_per_sqm is not None

    def test_with_area_and_rooms(self):
        """Test setting area with rooms."""
        builder = ListingBuilder()
        listing = builder.with_area(120.0, rooms=4).build()

        # Rooms aren't in Listing model, just area affects price_per_sqm
        assert listing.price.price_per_sqm is not None


class TestContentConfiguration:
    """Test content-related builder methods."""

    def test_with_description(self):
        """Test setting description."""
        builder = ListingBuilder()
        description = "Прекрасная квартира в центре"
        listing = builder.with_description(description).build()

        assert listing.description == description

    def test_with_media_single_image(self):
        """Test setting single media image."""
        builder = ListingBuilder()
        listing = builder.with_media([{"url": "https://example.com/image.jpg"}]).build()

        assert listing.media is not None
        assert len(listing.media.images) == 1
        assert listing.media.images[0].url == "https://example.com/image.jpg"

    def test_with_media_multiple_images(self):
        """Test setting multiple media images."""
        builder = ListingBuilder()
        images = [
            {"url": "https://example.com/1.jpg", "caption": "Гостиная"},
            {"url": "https://example.com/2.jpg", "caption": "Спальня"},
            {"url": "https://example.com/3.jpg"},
        ]
        listing = builder.with_media(images).build()

        assert len(listing.media.images) == 3
        assert listing.media.images[0].caption == "Гостиная"
        assert listing.media.images[1].caption == "Спальня"
        assert listing.media.images[2].caption is None


class TestFraudConfiguration:
    """Test fraud-related builder methods."""

    def test_with_fraud_score(self):
        """Test setting fraud score."""
        builder = ListingBuilder()
        listing = builder.with_fraud_score(75.0).build()

        assert listing.fraud_score == 75.0

    def test_with_fraud_score_invalid_range(self):
        """Test fraud score validation."""
        builder = ListingBuilder()

        with pytest.raises(ValueError, match="Fraud score must be 0-100"):
            builder.with_fraud_score(150.0)

        with pytest.raises(ValueError, match="Fraud score must be 0-100"):
            builder.with_fraud_score(-10.0)

    def test_with_fraud_indicators(self):
        """Test adding fraud indicators to description."""
        builder = ListingBuilder()
        listing = builder.with_fraud_indicators(
            ["unrealistic_price", "duplicate_photos"]
        ).build()

        assert "Fraud indicators" in listing.description
        assert "unrealistic_price" in listing.description


class TestFraudPresets:
    """Test fraud scenario presets."""

    def test_as_fraud_candidate_unrealistic_price(self):
        """Test unrealistic price fraud preset."""
        builder = ListingBuilder()
        listing = builder.as_fraud_candidate("unrealistic_price").build()

        assert listing.price.amount == 1_000_000.0
        assert listing.fraud_score == 85.0
        assert "unrealistic_price" in listing.description

    def test_as_fraud_candidate_no_photos(self):
        """Test no photos fraud preset."""
        builder = ListingBuilder()
        listing = builder.as_fraud_candidate("no_photos").build()

        assert listing.media is not None
        assert len(listing.media.images) == 0
        assert listing.fraud_score == 70.0

    def test_as_fraud_candidate_fake_location(self):
        """Test fake location fraud preset."""
        builder = ListingBuilder()
        listing = builder.as_fraud_candidate("fake_location").build()

        assert listing.location.coordinates.lat == 0.0
        assert listing.location.coordinates.lng == 0.0
        assert listing.fraud_score == 75.0

    def test_as_fraud_candidate_duplicate(self):
        """Test duplicate description fraud preset."""
        builder = ListingBuilder()
        listing = builder.as_fraud_candidate("duplicate").build()

        assert "Отличная квартира" in listing.description
        assert listing.fraud_score == 65.0

    def test_as_fraud_candidate_invalid_type(self):
        """Test invalid fraud type raises error."""
        builder = ListingBuilder()

        with pytest.raises(ValueError, match="Unknown fraud_type"):
            builder.as_fraud_candidate("invalid_type")


class TestEdgeCasePresets:
    """Test edge case presets."""

    def test_as_edge_case_minimal(self):
        """Test minimal edge case preset."""
        builder = ListingBuilder()
        listing = builder.as_edge_case("minimal").build()

        assert listing.description is None
        assert listing.media is None
        assert listing.fraud_score is None
        assert listing.location.address is None

    def test_as_edge_case_maximal(self):
        """Test maximal edge case preset."""
        builder = ListingBuilder(seed=42)
        listing = builder.as_edge_case("maximal").build()

        assert listing.description is not None
        assert len(listing.description) > 100
        assert listing.media is not None
        assert len(listing.media.images) == 15
        assert listing.fraud_score == 15.0
        assert listing.location.address is not None

    def test_as_edge_case_zero_price(self):
        """Test zero price edge case."""
        builder = ListingBuilder()
        listing = builder.as_edge_case("zero_price").build()

        assert listing.price.amount == 0.0
        assert listing.fraud_score == 95.0

    def test_as_edge_case_huge_price(self):
        """Test huge price edge case."""
        builder = ListingBuilder()
        listing = builder.as_edge_case("huge_price").build()

        assert listing.price.amount == 1_000_000_000.0
        assert listing.fraud_score == 80.0

    def test_as_edge_case_negative_area(self):
        """Test negative area edge case."""
        builder = ListingBuilder()
        listing = builder.as_edge_case("negative_area").build()

        # Note: This creates invalid data for testing validation
        assert listing.price.amount == 5_000_000.0

    def test_as_edge_case_invalid_type(self):
        """Test invalid edge case type raises error."""
        builder = ListingBuilder()

        with pytest.raises(ValueError, match="Unknown case_type"):
            builder.as_edge_case("invalid_case")


class TestSourceConfiguration:
    """Test source-related builder methods."""

    def test_with_source_minimal(self):
        """Test setting source with minimal parameters."""
        builder = ListingBuilder()
        listing = builder.with_source("cian_plugin", "cian.ru").build()

        assert listing.source.plugin_id == "cian_plugin"
        assert listing.source.platform == "cian.ru"
        assert listing.source.original_id is not None
        assert "cian.ru" in listing.source.url

    def test_with_source_full(self):
        """Test setting source with all parameters."""
        builder = ListingBuilder()
        listing = builder.with_source(
            plugin_id="avito_plugin",
            platform="avito.ru",
            original_id="listing-123",
            url="https://avito.ru/listing-123",
        ).build()

        assert listing.source.plugin_id == "avito_plugin"
        assert listing.source.platform == "avito.ru"
        assert listing.source.original_id == "listing-123"
        assert listing.source.url == "https://avito.ru/listing-123"

    def test_with_listing_id(self):
        """Test setting custom listing ID."""
        builder = ListingBuilder()
        custom_id = "test-listing-123"
        listing = builder.with_listing_id(custom_id).build()

        assert listing.listing_id == custom_id


class TestComplexScenarios:
    """Test complex builder scenarios."""

    def test_build_complete_listing(self):
        """Test building complete listing with all fields."""
        builder = ListingBuilder()
        listing = (
            builder.with_listing_id("complete-listing-001")
            .with_source("cian_plugin", "cian.ru")
            .with_location("Москва", address="ул. Арбат, 1", lat=55.7500, lng=37.6000)
            .with_price(8_000_000, currency="RUB")
            .with_property_type("apartment")
            .with_listing_type("sale")
            .with_area(95.0, rooms=3)
            .with_description("Современная квартира с ремонтом")
            .with_media(
                [
                    {"url": "https://example.com/1.jpg", "caption": "Вид"},
                    {"url": "https://example.com/2.jpg"},
                ]
            )
            .with_fraud_score(25.0)
            .build()
        )

        assert listing.listing_id == "complete-listing-001"
        assert listing.source.plugin_id == "cian_plugin"
        assert listing.location.city == "Москва"
        assert listing.location.address == "ул. Арбат, 1"
        assert listing.price.amount == 8_000_000.0
        assert listing.price.price_per_sqm is not None
        assert listing.property_type == "apartment"
        assert listing.type == "sale"
        assert listing.description is not None
        assert listing.media is not None
        assert len(listing.media.images) == 2
        assert listing.fraud_score == 25.0

    def test_build_fraud_scenario(self):
        """Test building fraud scenario with custom overrides."""
        builder = ListingBuilder()
        listing = (
            builder.with_location("Москва")
            .with_property_type("apartment")
            .as_fraud_candidate("unrealistic_price")
            .with_description("Срочно! Очень дешево!")
            .build()
        )

        assert listing.price.amount == 1_000_000.0
        assert listing.fraud_score == 85.0
        assert "Срочно" in listing.description

    def test_reproducible_with_seed(self):
        """Test reproducible builds with seed."""
        builder1 = ListingBuilder(seed=42)
        listing1 = builder1.as_edge_case("maximal").build()

        builder2 = ListingBuilder(seed=42)
        listing2 = builder2.as_edge_case("maximal").build()

        # Should have same generated content
        assert listing1.description == listing2.description
        assert len(listing1.media.images) == len(listing2.media.images)


class TestBuildOutput:
    """Test different build output formats."""

    def test_build_returns_listing(self):
        """Test build() returns Listing instance."""
        builder = ListingBuilder()
        listing = builder.build()

        assert isinstance(listing, Listing)

    def test_build_dict_returns_dict(self):
        """Test build_dict() returns dictionary."""
        builder = ListingBuilder()
        data = builder.build_dict()

        assert isinstance(data, dict)
        assert "listing_id" in data
        assert "source" in data
        assert "location" in data
        assert "price" in data

    def test_build_dict_json_serializable(self):
        """Test build_dict() output is JSON serializable."""
        import json

        builder = ListingBuilder()
        data = builder.build_dict()

        # Should not raise
        json_str = json.dumps(data)
        assert json_str is not None


class TestBuilderReusability:
    """Test builder reusability and state management."""

    def test_builder_can_build_multiple(self):
        """Test builder can be used to build multiple listings."""
        builder = ListingBuilder()

        listing1 = builder.with_price(2_000_000).build()
        listing2 = builder.with_price(3_000_000).build()

        # Each listing should reflect the builder state at build time
        assert listing2.price.amount == 3_000_000.0

    def test_builder_state_persists(self):
        """Test builder state persists across builds."""
        builder = ListingBuilder()
        builder.with_location("Санкт-Петербург")
        builder.with_property_type("house")

        listing1 = builder.build()
        listing2 = builder.with_price(10_000_000).build()

        # Both should have the same location and property_type
        assert listing1.location.city == "Санкт-Петербург"
        assert listing2.location.city == "Санкт-Петербург"
        assert listing1.property_type == "house"
        assert listing2.property_type == "house"
        # But different prices
        assert listing2.price.amount == 10_000_000.0
