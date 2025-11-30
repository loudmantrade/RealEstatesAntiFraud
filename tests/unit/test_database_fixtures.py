"""
Tests for database session fixtures.

Validates that database fixtures work correctly and provide proper isolation.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database.models import ListingModel
from core.models.udm import Listing

pytestmark = pytest.mark.unit


def listing_to_model(listing: Listing) -> ListingModel:
    """Convert Pydantic Listing to SQLAlchemy ListingModel.

    Args:
        listing: Pydantic Listing instance

    Returns:
        ListingModel: SQLAlchemy model instance
    """
    return ListingModel(
        listing_id=listing.listing_id,
        source_plugin_id=listing.source.plugin_id,
        source_platform=listing.source.platform,
        source_original_id=listing.source.original_id,
        source_url=listing.source.url,
        type=listing.type,
        property_type=listing.property_type,
        location_country=listing.location.country,
        location_city=listing.location.city,
        location_address=listing.location.address,
        location_lat=(listing.location.coordinates.lat if listing.location.coordinates else None),
        location_lng=(listing.location.coordinates.lng if listing.location.coordinates else None),
        price_amount=listing.price.amount,
        price_currency=listing.price.currency,
        price_per_sqm=listing.price.price_per_sqm,
        description=listing.description,
        media=listing.media.model_dump() if listing.media else None,
        fraud_score=listing.fraud_score,
    )


class TestDatabaseFixtures:
    """Test database fixture availability and basic functionality."""

    def test_test_database_url_fixture(self, test_database_url):
        """Test test_database_url fixture provides valid URL."""
        assert test_database_url is not None
        assert isinstance(test_database_url, str)
        # Should be either SQLite or PostgreSQL
        assert "sqlite" in test_database_url or "postgresql" in test_database_url

    def test_test_engine_fixture(self, test_engine):
        """Test test_engine fixture is available."""
        assert test_engine is not None
        # Engine should be able to connect
        connection = test_engine.connect()
        assert connection is not None
        connection.close()

    def test_db_session_fixture(self, db_session):
        """Test db_session fixture provides working session."""
        assert db_session is not None
        assert isinstance(db_session, Session)
        # Session should be usable
        result = db_session.execute(text("SELECT 1")).scalar()
        assert result == 1


class TestSessionIsolation:
    """Test transaction isolation between tests."""

    def test_first_session_add_data(self, db_session, listing_factory):
        """First test adds data to database."""
        # Create and add listing
        listing = listing_factory.create_listing()
        listing_model = listing_to_model(listing)

        db_session.add(listing_model)
        db_session.commit()

        # Verify data exists in this session
        count = db_session.query(ListingModel).count()
        assert count == 1

    def test_second_session_isolated(self, db_session):
        """Second test should not see data from first test."""
        # Due to rollback, previous test's data is not visible
        count = db_session.query(ListingModel).count()
        assert count == 0

    def test_third_session_also_isolated(self, db_session, listing_factory):
        """Third test also starts with clean database."""
        count = db_session.query(ListingModel).count()
        assert count == 0

        # Add different amount of data
        for _ in range(3):
            listing = listing_factory.create_listing()
            listing_model = listing_to_model(listing)
            db_session.add(listing_model)

        db_session.commit()
        count = db_session.query(ListingModel).count()
        assert count == 3


class TestCleanDbFixture:
    """Test clean_db fixture provides explicit truncation."""

    def test_clean_db_truncates_tables(self, clean_db):
        """Test clean_db fixture starts with empty tables."""
        # All tables should be empty
        count = clean_db.query(ListingModel).count()
        assert count == 0

    def test_clean_db_is_usable(self, clean_db, listing_factory):
        """Test clean_db fixture can be used for operations."""
        # Add data
        listing = listing_factory.create_listing()
        listing_model = listing_to_model(listing)

        clean_db.add(listing_model)
        clean_db.commit()

        # Verify data exists
        count = clean_db.query(ListingModel).count()
        assert count == 1


class TestSessionFactory:
    """Test session factory fixture."""

    def test_session_factory_creates_sessions(self, db_session_factory):
        """Test session factory can create multiple sessions."""
        session1 = db_session_factory()
        session2 = db_session_factory()

        assert session1 is not None
        assert session2 is not None
        assert session1 is not session2

        session1.close()
        session2.close()

    def test_factory_sessions_work(self, db_session_factory, listing_factory):
        """Test sessions created by factory are functional."""
        session1 = db_session_factory()
        session2 = db_session_factory()

        # Add data in session1
        listing = listing_factory.create_listing()
        listing_model = listing_to_model(listing)
        session1.add(listing_model)
        session1.commit()

        # session2 can see committed data
        count = session2.query(ListingModel).count()
        assert count == 1

        session1.close()
        session2.close()


class TestDatabaseOperations:
    """Test common database operations with fixtures."""

    def test_crud_operations(self, db_session, listing_factory):
        """Test Create, Read, Update, Delete operations."""
        # CREATE
        listing = listing_factory.create_listing()
        listing_model = listing_to_model(listing)
        db_session.add(listing_model)
        db_session.commit()

        # READ
        result = db_session.query(ListingModel).filter_by(listing_id=listing.listing_id).first()
        assert result is not None
        assert result.location_city == listing.location.city

        # UPDATE
        result.location_city = "Updated City"
        db_session.commit()

        updated = db_session.query(ListingModel).filter_by(listing_id=listing.listing_id).first()
        assert updated.location_city == "Updated City"

        # DELETE
        db_session.delete(updated)
        db_session.commit()

        deleted = db_session.query(ListingModel).filter_by(listing_id=listing.listing_id).first()
        assert deleted is None

    def test_bulk_operations(self, clean_db, listing_factory):
        """Test bulk insert operations."""
        # Create multiple listings
        listings = []
        for i in range(10):
            listing = listing_factory.create_listing()
            listing_model = listing_to_model(listing)
            listing_model.listing_id = f"bulk-{i}"  # Override for uniqueness
            listings.append(listing_model)

        # Bulk insert
        clean_db.add_all(listings)
        clean_db.commit()

        # Verify count
        count = clean_db.query(ListingModel).count()
        assert count == 10

    def test_query_filtering(self, clean_db, listing_factory):
        """Test querying with filters."""
        # Add listings with different prices
        for i, price in enumerate([100_000, 200_000, 300_000]):
            listing = listing_factory.create_listing(price={"amount": price, "currency": "EUR"})
            listing_model = listing_to_model(listing)
            listing_model.listing_id = f"filter-{i}"  # Override for uniqueness
            clean_db.add(listing_model)

        clean_db.commit()

        # Filter by price range
        results = (
            clean_db.query(ListingModel)
            .filter(
                ListingModel.price_amount >= 150_000,
                ListingModel.price_amount <= 250_000,
            )
            .all()
        )

        assert len(results) == 1
        assert results[0].price_amount == 200_000


class TestFixtureDocumentation:
    """Test that fixtures are properly documented."""

    def test_fixtures_have_docstrings(self):
        """Test database fixtures have docstrings."""
        import tests.fixtures.database_fixtures as db_fixtures

        # Check main fixtures have docstrings
        assert db_fixtures.test_engine.__doc__ is not None
        assert db_fixtures.db_session.__doc__ is not None
        assert db_fixtures.clean_db.__doc__ is not None
        assert db_fixtures.db_session_factory.__doc__ is not None

    def test_fixture_module_documented(self):
        """Test fixture module has documentation."""
        import tests.fixtures.database_fixtures as db_fixtures

        assert db_fixtures.__doc__ is not None
        assert "Database Session Fixtures" in db_fixtures.__doc__
