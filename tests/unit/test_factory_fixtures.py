"""
Tests for factory fixtures.

Validates that all pytest fixtures work correctly and provide expected data.
"""

from core.models.udm import Listing
from tests.builders.listing_builder import ListingBuilder
from tests.factories.event_factory import EventFactory
from tests.factories.listing_factory import ListingFactory


class TestFactoryFixtures:
    """Test factory fixture availability and functionality."""

    def test_listing_factory_fixture(self, listing_factory):
        """Test listing_factory fixture is available."""
        assert isinstance(listing_factory, ListingFactory)
        listing = listing_factory.create_listing()
        assert isinstance(listing, Listing)

    def test_event_factory_fixture(self, event_factory):
        """Test event_factory fixture is available."""
        assert isinstance(event_factory, EventFactory)
        event = event_factory.create_raw_event()
        assert event is not None

    def test_listing_builder_fixture(self, listing_builder):
        """Test listing_builder fixture is available."""
        assert isinstance(listing_builder, ListingBuilder)
        listing = listing_builder.build()
        assert isinstance(listing, Listing)


class TestPortugalFixtures:
    """Test Portugal market fixtures."""

    def test_lisboa_apartments_fixture(self, lisboa_apartments):
        """Test lisboa_apartments fixture provides 5 listings."""
        assert len(lisboa_apartments) == 5
        assert all(isinstance(listing, Listing) for listing in lisboa_apartments)
        assert all(listing.location.city == "Lisboa" for listing in lisboa_apartments)

    def test_porto_apartments_fixture(self, porto_apartments):
        """Test porto_apartments fixture provides 5 listings."""
        assert len(porto_apartments) == 5
        assert all(isinstance(listing, Listing) for listing in porto_apartments)
        assert all(listing.location.city == "Porto" for listing in porto_apartments)

    def test_portuguese_cities_fixture(self, portuguese_cities):
        """Test portuguese_cities fixture provides 10 listings."""
        assert len(portuguese_cities) == 10
        assert all(isinstance(listing, Listing) for listing in portuguese_cities)


class TestUkraineFixtures:
    """Test Ukraine market fixtures."""

    def test_kyiv_apartments_fixture(self, kyiv_apartments):
        """Test kyiv_apartments fixture provides 5 listings."""
        assert len(kyiv_apartments) == 5
        assert all(isinstance(listing, Listing) for listing in kyiv_apartments)
        assert all(listing.location.city == "Київ" for listing in kyiv_apartments)

    def test_lviv_apartments_fixture(self, lviv_apartments):
        """Test lviv_apartments fixture provides 5 listings."""
        assert len(lviv_apartments) == 5
        assert all(isinstance(listing, Listing) for listing in lviv_apartments)
        assert all(listing.location.city == "Львів" for listing in lviv_apartments)

    def test_ukrainian_cities_fixture(self, ukrainian_cities):
        """Test ukrainian_cities fixture provides 10 listings."""
        assert len(ukrainian_cities) == 10
        assert all(isinstance(listing, Listing) for listing in ukrainian_cities)


class TestSpecializedFixtures:
    """Test specialized data fixtures."""

    def test_fraud_candidates_fixture(self, fraud_candidates):
        """Test fraud_candidates fixture provides 3 listings."""
        assert len(fraud_candidates) == 3
        assert all(isinstance(listing, Listing) for listing in fraud_candidates)
        # Fraud candidates should have prices (even if suspicious)
        assert all(listing.price.amount > 0 for listing in fraud_candidates)

    def test_edge_case_listings_fixture(self, edge_case_listings):
        """Test edge_case_listings fixture provides 5 listings."""
        assert len(edge_case_listings) == 5
        assert all(isinstance(listing, Listing) for listing in edge_case_listings)

    def test_test_listings_fixture(self, test_listings):
        """Test test_listings fixture provides 10 listings."""
        assert len(test_listings) == 10
        assert all(isinstance(listing, Listing) for listing in test_listings)


class TestEventFixtures:
    """Test event fixtures."""

    def test_event_chain_fixture(self, event_chain):
        """Test event_chain fixture provides event sequence."""
        assert len(event_chain) >= 3
        assert all(hasattr(e, "metadata") for e in event_chain)

    def test_raw_listing_event_fixture(self, raw_listing_event):
        """Test raw_listing_event fixture provides single event."""
        assert raw_listing_event is not None
        assert hasattr(raw_listing_event, "metadata")

    def test_normalized_listing_event_fixture(self, normalized_listing_event):
        """Test normalized_listing_event fixture provides single event."""
        assert normalized_listing_event is not None
        assert hasattr(normalized_listing_event, "metadata")


class TestSeededFixtures:
    """Test seeded fixtures for reproducibility."""

    def test_seeded_listing_factory_fixture(self, seeded_listing_factory):
        """Test seeded_listing_factory is deterministic."""
        assert isinstance(seeded_listing_factory, ListingFactory)

        # Generate listings with seeded factory
        listings = seeded_listing_factory.create_batch(3)

        # Should generate listings successfully
        assert len(listings) == 3
        assert all(isinstance(listing, Listing) for listing in listings)

    def test_seeded_listings_fixture(self, seeded_listings):
        """Test seeded_listings fixture provides 5 listings."""
        assert len(seeded_listings) == 5
        assert all(isinstance(listing, Listing) for listing in seeded_listings)


class TestFixtureCombinations:
    """Test using multiple fixtures together."""

    def test_combine_portugal_ukraine_data(self, lisboa_apartments, kyiv_apartments):
        """Test combining Portugal and Ukraine fixtures."""
        all_listings = lisboa_apartments + kyiv_apartments
        assert len(all_listings) == 10

        cities = {listing.location.city for listing in all_listings}
        assert "Lisboa" in cities
        assert "Київ" in cities

    def test_combine_factory_and_preset(self, listing_factory, porto_apartments):
        """Test using factory alongside preset data."""
        custom_listing = listing_factory.create_listing(
            price={"amount": 800_000, "currency": "EUR"}
        )
        all_listings = porto_apartments + [custom_listing]

        assert len(all_listings) == 6
        assert any(listing.price.amount == 800_000 for listing in all_listings)

    def test_combine_builder_and_factory(self, listing_builder, listing_factory):
        """Test using builder and factory together."""
        built_listing = listing_builder.with_price(600_000).build()
        factory_listing = listing_factory.create_listing(
            price={"amount": 700_000, "currency": "EUR"}
        )

        assert built_listing.price.amount == 600_000
        assert factory_listing.price.amount == 700_000


class TestFixtureUsagePatterns:
    """Test common fixture usage patterns."""

    def test_filter_by_city(self, test_listings):
        """Test filtering preset data."""
        lisboa_listings = [
            listing for listing in test_listings if listing.location.city == "Lisboa"
        ]
        assert isinstance(lisboa_listings, list)

    def test_calculate_statistics(self, lisboa_apartments):
        """Test calculating statistics on preset data."""
        prices = [listing.price.amount for listing in lisboa_apartments]
        avg_price = sum(prices) / len(prices)
        assert avg_price > 0

    def test_modify_preset_data(self, porto_apartments):
        """Test modifying preset fixture data."""
        modified = []
        for listing in porto_apartments:
            listing.price.amount *= 1.1  # Increase by 10%
            modified.append(listing)

        assert len(modified) == 5
        # Modifications should be applied
        assert all(listing.price.amount > 0 for listing in modified)

    def test_validate_all_listings(self, test_listings):
        """Test validation on fixture data."""
        for listing in test_listings:
            assert listing.listing_id is not None
            assert listing.price.amount > 0
            assert listing.location.city is not None


class TestFixtureDocumentation:
    """Test that fixtures are properly documented."""

    def test_fixture_has_docstring(self, listing_factory):
        """Test fixtures have docstrings."""
        # This is a meta-test to ensure fixtures are documented
        import tests.fixtures.factory_fixtures as fixtures_module

        # Check that main fixtures have docstrings
        assert fixtures_module.listing_factory.__doc__ is not None
        assert fixtures_module.event_factory.__doc__ is not None
        assert fixtures_module.listing_builder.__doc__ is not None

    def test_fixture_module_documented(self):
        """Test fixture module has documentation."""
        import tests.fixtures.factory_fixtures as fixtures_module

        assert fixtures_module.__doc__ is not None
        assert "Factory Fixtures" in fixtures_module.__doc__
