"""
Tests for specialized ListingFactory methods (Issue #139).

This module tests the specialized factory methods for:
- Lisboa apartments
- Porto apartments
- Kyiv apartments
- Lviv apartments
- Regional listings (Portugal/Ukraine cities)
- Fraud candidates
- Edge cases
"""

import pytest

from tests.factories.listing_factory import ListingFactory


class TestLisboaApartments:
    """Tests for Lisboa apartment generation."""

    def test_create_lisboa_apartments_default(self):
        """Test creating Lisboa apartments with default parameters."""
        factory = ListingFactory(seed=42)
        listings = factory.create_lisboa_apartments(5)

        assert len(listings) == 5
        for listing in listings:
            assert listing.location.city == "Lisboa"
            assert listing.location.country == "Portugal"
            assert listing.property_type == "apartment"
            assert listing.type == "sale"
            assert listing.price.currency == "EUR"
            assert 4_000 <= listing.price.price_per_sqm <= 8_000

    def test_create_lisboa_apartments_specific_district(self):
        """Test creating Lisboa apartments in specific district."""
        factory = ListingFactory(seed=42)
        listings = factory.create_lisboa_apartments(3, district="Baixa")

        assert len(listings) == 3
        for listing in listings:
            assert "Baixa" in listing.location.address
            assert listing.location.city == "Lisboa"
            assert 6_000 <= listing.price.price_per_sqm <= 8_000

    def test_create_lisboa_apartments_district_variations(self):
        """Test all Lisboa districts generate valid data."""
        factory = ListingFactory(seed=42)
        districts = [
            "Baixa", "Chiado", "Alfama", "Belém",
            "Parque das Nações", "Alvalade", "Campo de Ourique", "Estrela"
        ]

        for district in districts:
            listings = factory.create_lisboa_apartments(1, district=district)
            listing = listings[0]

            assert listing.location.city == "Lisboa"
            assert district in listing.location.address
            assert listing.price.currency == "EUR"
            assert listing.price.price_per_sqm > 0

    def test_lisboa_apartments_coordinates_in_range(self):
        """Test Lisboa coordinates are within city bounds."""
        factory = ListingFactory(seed=42)
        listings = factory.create_lisboa_apartments(10)

        for listing in listings:
            coords = listing.location.coordinates
            # Lisboa bounds approximately
            assert 38.68 <= coords.lat <= 38.80
            assert -9.25 <= coords.lng <= -9.05

    def test_lisboa_apartments_realistic_prices(self):
        """Test Lisboa apartment prices are realistic."""
        factory = ListingFactory(seed=42)
        listings = factory.create_lisboa_apartments(10)

        for listing in listings:
            # Typical Lisboa apartment: 40-120 sqm
            # Price per sqm: 4,000-8,000 EUR
            # Total: 160,000 - 960,000 EUR
            assert 100_000 <= listing.price.amount <= 1_000_000


class TestPortoApartments:
    """Tests for Porto apartment generation."""

    def test_create_porto_apartments_default(self):
        """Test creating Porto apartments with default parameters."""
        factory = ListingFactory(seed=42)
        listings = factory.create_porto_apartments(5)

        assert len(listings) == 5
        for listing in listings:
            assert listing.location.city == "Porto"
            assert listing.location.country == "Portugal"
            assert listing.property_type == "apartment"
            assert listing.price.currency == "EUR"
            assert 2_500 <= listing.price.price_per_sqm <= 5_000

    def test_create_porto_apartments_specific_district(self):
        """Test creating Porto apartments in specific district."""
        factory = ListingFactory(seed=42)
        listings = factory.create_porto_apartments(2, district="Ribeira")

        assert len(listings) == 2
        for listing in listings:
            assert "Ribeira" in listing.location.address
            assert listing.location.city == "Porto"
            assert 4_000 <= listing.price.price_per_sqm <= 5_000

    def test_create_porto_apartments_all_districts(self):
        """Test all Porto districts generate valid data."""
        factory = ListingFactory(seed=42)
        districts = ["Ribeira", "Boavista", "Foz do Douro", "Cedofeita", "Massarelos"]

        for district in districts:
            listings = factory.create_porto_apartments(1, district=district)
            listing = listings[0]

            assert listing.location.city == "Porto"
            assert district in listing.location.address
            assert listing.price.currency == "EUR"

    def test_porto_apartments_coordinates_in_range(self):
        """Test Porto coordinates are within city bounds."""
        factory = ListingFactory(seed=42)
        listings = factory.create_porto_apartments(10)

        for listing in listings:
            coords = listing.location.coordinates
            # Porto bounds approximately
            assert 41.10 <= coords.lat <= 41.20
            assert -8.70 <= coords.lng <= -8.55


class TestKyivApartments:
    """Tests for Kyiv apartment generation."""

    def test_create_kyiv_apartments_default(self):
        """Test creating Kyiv apartments with default parameters."""
        factory = ListingFactory(seed=42)
        listings = factory.create_kyiv_apartments(5)

        assert len(listings) == 5
        for listing in listings:
            assert listing.location.city == "Київ"
            assert listing.location.country == "Ukraine"
            assert listing.property_type == "apartment"
            assert listing.price.currency == "EUR"
            assert 1_000 <= listing.price.price_per_sqm <= 3_500

    def test_create_kyiv_apartments_specific_district(self):
        """Test creating Kyiv apartments in specific district."""
        factory = ListingFactory(seed=42)
        listings = factory.create_kyiv_apartments(3, district="Печерськ")

        assert len(listings) == 3
        for listing in listings:
            assert "Печерськ" in listing.location.address
            assert listing.location.city == "Київ"
            assert 2_500 <= listing.price.price_per_sqm <= 3_500

    def test_create_kyiv_apartments_all_districts(self):
        """Test all Kyiv districts generate valid data."""
        factory = ListingFactory(seed=42)
        districts = ["Печерськ", "Шевченківський", "Подільський", "Оболонський", "Дарницький"]

        for district in districts:
            listings = factory.create_kyiv_apartments(1, district=district)
            listing = listings[0]

            assert listing.location.city == "Київ"
            assert district in listing.location.address

    def test_kyiv_apartments_coordinates_in_range(self):
        """Test Kyiv coordinates are within city bounds."""
        factory = ListingFactory(seed=42)
        listings = factory.create_kyiv_apartments(10)

        for listing in listings:
            coords = listing.location.coordinates
            # Kyiv bounds approximately
            assert 50.35 <= coords.lat <= 50.55
            assert 30.35 <= coords.lng <= 30.75


class TestLvivApartments:
    """Tests for Lviv apartment generation."""

    def test_create_lviv_apartments_default(self):
        """Test creating Lviv apartments with default parameters."""
        factory = ListingFactory(seed=42)
        listings = factory.create_lviv_apartments(3)

        assert len(listings) == 3
        for listing in listings:
            assert listing.location.city == "Львів"
            assert listing.location.country == "Ukraine"
            assert listing.property_type == "apartment"
            assert listing.price.currency == "EUR"
            assert 1_000 <= listing.price.price_per_sqm <= 2_000

    def test_create_lviv_apartments_specific_district(self):
        """Test creating Lviv apartments in specific district."""
        factory = ListingFactory(seed=42)
        listings = factory.create_lviv_apartments(2, district="Центр")

        assert len(listings) == 2
        for listing in listings:
            assert "Центр" in listing.location.address
            assert listing.location.city == "Львів"

    def test_lviv_apartments_coordinates_in_range(self):
        """Test Lviv coordinates are within city bounds."""
        factory = ListingFactory(seed=42)
        listings = factory.create_lviv_apartments(10)

        for listing in listings:
            coords = listing.location.coordinates
            # Lviv bounds approximately
            assert 49.75 <= coords.lat <= 49.90
            assert 23.95 <= coords.lng <= 24.10


class TestRegionalListings:
    """Tests for regional listing generation."""

    def test_create_regional_listings_portuguese_cities(self):
        """Test creating listings for Portuguese cities."""
        factory = ListingFactory(seed=42)
        cities = ["Lisboa", "Porto", "Faro", "Coimbra", "Braga"]

        for city in cities:
            listings = factory.create_regional_listings(city, count=3)
            assert len(listings) == 3

            for listing in listings:
                assert listing.location.city == city
                assert listing.location.country == "Portugal"
                assert listing.price.currency == "EUR"
                assert 2_000 <= listing.price.price_per_sqm <= 4_000

    def test_create_regional_listings_ukrainian_cities(self):
        """Test creating listings for Ukrainian cities."""
        factory = ListingFactory(seed=42)
        cities = ["Київ", "Львів", "Одеса", "Харків", "Дніпро"]

        for city in cities:
            listings = factory.create_regional_listings(city, count=2)
            assert len(listings) == 2

            for listing in listings:
                assert listing.location.city == city
                assert listing.location.country == "Ukraine"
                assert listing.price.currency == "EUR"
                assert 1_000 <= listing.price.price_per_sqm <= 2_000

    def test_create_regional_listings_invalid_city(self):
        """Test error handling for invalid city."""
        factory = ListingFactory(seed=42)

        with pytest.raises(ValueError) as exc_info:
            factory.create_regional_listings("InvalidCity", count=1)

        assert "not supported" in str(exc_info.value)

    def test_regional_listings_coordinates_near_city(self):
        """Test regional listings have coordinates near the city."""
        factory = ListingFactory(seed=42)
        listings = factory.create_regional_listings("Faro", count=5)

        for listing in listings:
            coords = listing.location.coordinates
            # Faro coordinates: (37.0194, -7.9322)
            # Should be within ~2km (roughly ±0.02 degrees)
            assert 36.99 <= coords.lat <= 37.04
            assert -7.96 <= coords.lng <= -7.91


class TestFraudCandidates:
    """Tests for fraud candidate generation."""

    def test_create_fraud_candidates_default(self):
        """Test creating fraud candidates with random types."""
        factory = ListingFactory(seed=42)
        listings = factory.create_fraud_candidates(5)

        assert len(listings) == 5
        for listing in listings:
            assert listing.fraud_score is not None
            assert listing.fraud_score >= 40

    def test_create_fraud_candidates_unrealistic_price(self):
        """Test fraud candidate with unrealistic price."""
        factory = ListingFactory(seed=42)
        listings = factory.create_fraud_candidates(3, fraud_type="unrealistic_price")

        assert len(listings) == 3
        for listing in listings:
            assert listing.fraud_score >= 70
            # Price should be very low (20% of normal)
            assert listing.price.amount < 150_000

    def test_create_fraud_candidates_duplicate_photos(self):
        """Test fraud candidate with no/duplicate photos."""
        factory = ListingFactory(seed=42)
        listings = factory.create_fraud_candidates(2, fraud_type="duplicate_photos")

        assert len(listings) == 2
        for listing in listings:
            assert listing.fraud_score >= 50
            assert listing.media is None or len(listing.media.images) == 0

    def test_create_fraud_candidates_fake_location(self):
        """Test fraud candidate with fake location."""
        factory = ListingFactory(seed=42)
        listings = factory.create_fraud_candidates(2, fraud_type="fake_location")

        assert len(listings) == 2
        for listing in listings:
            assert listing.fraud_score >= 60
            # Coordinates should be invalid (0, 0)
            assert listing.location.coordinates.lat == 0.0
            assert listing.location.coordinates.lng == 0.0

    def test_create_fraud_candidates_too_good_to_be_true(self):
        """Test fraud candidate with too good description."""
        factory = ListingFactory(seed=42)
        listings = factory.create_fraud_candidates(2, fraud_type="too_good_to_be_true")

        assert len(listings) == 2
        for listing in listings:
            assert listing.fraud_score >= 75
            assert "URGENT" in listing.description or "cheap" in listing.description.lower()
            # Price should be suspiciously low (30% of normal)
            assert listing.price.amount < 200_000

    def test_create_fraud_candidates_invalid_type(self):
        """Test error handling for invalid fraud type."""
        factory = ListingFactory(seed=42)

        with pytest.raises(ValueError) as exc_info:
            factory.create_fraud_candidates(1, fraud_type="invalid_type")

        assert "Invalid fraud_type" in str(exc_info.value)

    def test_create_fraud_candidates_all_types(self):
        """Test all fraud types generate different scenarios."""
        factory = ListingFactory(seed=42)
        fraud_types = [
            "unrealistic_price",
            "duplicate_photos",
            "fake_location",
            "missing_contact",
            "too_good_to_be_true"
        ]

        for fraud_type in fraud_types:
            listings = factory.create_fraud_candidates(1, fraud_type=fraud_type)
            assert len(listings) == 1
            assert listings[0].fraud_score >= 40


class TestEdgeCases:
    """Tests for edge case generation."""

    def test_create_edge_cases_default_count(self):
        """Test creating default number of edge cases."""
        factory = ListingFactory(seed=42)
        listings = factory.create_edge_cases(5)

        assert len(listings) == 5

    def test_create_edge_cases_custom_count(self):
        """Test creating custom number of edge cases."""
        factory = ListingFactory(seed=42)
        listings = factory.create_edge_cases(10)

        assert len(listings) == 10

    def test_edge_case_minimal_listing(self):
        """Test minimal listing has only required fields."""
        factory = ListingFactory(seed=42)
        listing = factory._create_minimal_listing()

        assert listing.description is None
        assert listing.media is None
        assert listing.fraud_score is None
        assert listing.listing_id is not None
        assert listing.source is not None
        assert listing.location is not None
        assert listing.price is not None

    def test_edge_case_maximal_listing(self):
        """Test maximal listing has all fields populated."""
        factory = ListingFactory(seed=42)
        listing = factory._create_maximal_listing()

        assert listing.description is not None
        assert len(listing.description) > 0
        assert listing.media is not None
        assert len(listing.media.images) == 15
        assert listing.fraud_score is not None

    def test_edge_case_zero_price(self):
        """Test zero price edge case."""
        factory = ListingFactory(seed=42)
        listing = factory._create_zero_price_listing()

        assert listing.price.amount == 0.0
        assert listing.price.price_per_sqm == 0.0
        assert listing.fraud_score >= 80

    def test_edge_case_negative_price(self):
        """Test negative price edge case."""
        factory = ListingFactory(seed=42)
        listing = factory._create_negative_price_listing()

        assert listing.price.amount < 0
        assert listing.price.price_per_sqm < 0
        assert listing.fraud_score >= 90

    def test_edge_case_invalid_coordinates(self):
        """Test invalid coordinates edge case."""
        factory = ListingFactory(seed=42)
        listing = factory._create_invalid_coordinates_listing()

        assert listing.location.coordinates.lat == 0.0
        assert listing.location.coordinates.lng == 0.0
        assert listing.fraud_score >= 70

    def test_edge_case_empty_description(self):
        """Test empty description edge case."""
        factory = ListingFactory(seed=42)
        listing = factory._create_empty_description_listing()

        assert listing.description == ""
        assert listing.fraud_score >= 40

    def test_edge_case_oversized_area(self):
        """Test oversized area edge case."""
        factory = ListingFactory(seed=42)
        listing = factory._create_oversized_area_listing()

        assert listing.property_type == "apartment"
        # Price per sqm should be very low due to huge area
        assert listing.price.price_per_sqm < 1_000
        assert listing.fraud_score >= 60


class TestBackwardCompatibility:
    """Tests for backward compatibility with existing methods."""

    def test_create_suspicious_listings_still_works(self):
        """Test that old create_suspicious_listings method still works."""
        factory = ListingFactory(seed=42)
        listings = factory.create_suspicious_listings(3)

        assert len(listings) == 3
        for listing in listings:
            assert listing.fraud_score >= 40

    def test_create_listing_uses_portugal_ukraine_data(self):
        """Test that default create_listing uses Portugal/Ukraine markets."""
        factory = ListingFactory(seed=42)
        listings = factory.create_batch(20)

        countries = [listing.location.country for listing in listings]
        # Should only contain Portugal or Ukraine
        assert all(c in ["Portugal", "Ukraine"] for c in countries)

        # Should have both countries represented (with Portugal more common)
        assert "Portugal" in countries
        assert "Ukraine" in countries

    def test_all_listings_use_eur_currency(self):
        """Test that all generated listings use EUR currency."""
        factory = ListingFactory(seed=42)

        # Test various generation methods
        test_listings = []
        test_listings.extend(factory.create_batch(5))
        test_listings.extend(factory.create_lisboa_apartments(2))
        test_listings.extend(factory.create_kyiv_apartments(2))
        test_listings.extend(factory.create_regional_listings("Porto", 2))
        test_listings.extend(factory.create_fraud_candidates(2))

        for listing in test_listings:
            assert listing.price.currency == "EUR"


class TestSeededGeneration:
    """Tests for reproducible generation with seeds."""

    def test_seeded_factory_same_faker_data(self):
        """Test that seeded factories generate consistent faker data."""
        factory1 = ListingFactory(seed=123)
        factory2 = ListingFactory(seed=123)

        # Generate basic listings without randomized choices
        listing1 = factory1.create_listing(
            property_type="apartment",
            listing_type="sale",
            location={"city": "Lisboa", "country": "Portugal"}
        )
        listing2 = factory2.create_listing(
            property_type="apartment",
            listing_type="sale",
            location={"city": "Lisboa", "country": "Portugal"}
        )

        # Basic fields should match with same seed
        assert listing1.location.city == listing2.location.city
        assert listing1.property_type == listing2.property_type
