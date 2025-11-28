"""Unit tests for ListingRepository."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.base import Base
from core.database.models import ListingModel
from core.database.repository import ListingRepository
from core.models.udm import (
    Coordinates,
    Listing,
    Location,
    Media,
    MediaImage,
    Price,
    SourceInfo,
)

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def repository(db_session):
    """Create a ListingRepository instance."""
    return ListingRepository(db_session)


@pytest.fixture
def sample_listing():
    """Create a sample listing for testing."""
    return Listing(
        listing_id="test-listing-1",
        source=SourceInfo(
            plugin_id="test-plugin",
            platform="test-platform",
            original_id="orig-123",
            url="https://example.com/listing/123",
        ),
        type="sale",
        property_type="apartment",
        location=Location(
            country="Russia",
            city="Moscow",
            address="Red Square, 1",
            coordinates=Coordinates(lat=55.7558, lng=37.6173),
        ),
        price=Price(amount=5000000.00, currency="RUB", price_per_sqm=100000.00),
        description="Beautiful apartment in the city center",
        media=Media(
            images=[
                MediaImage(url="https://example.com/img1.jpg", caption="Living room"),
                MediaImage(url="https://example.com/img2.jpg", caption="Bedroom"),
            ]
        ),
        fraud_score=25.5,
    )


def test_create_listing(repository, sample_listing):
    """Test creating a new listing."""
    result = repository.create(sample_listing)

    assert result.listing_id == "test-listing-1"
    assert result.source.plugin_id == "test-plugin"
    assert result.source.platform == "test-platform"
    assert result.type == "sale"
    assert result.property_type == "apartment"
    assert result.location.city == "Moscow"
    assert result.price.amount == 5000000.00
    assert result.fraud_score == 25.5


def test_get_by_id(repository, sample_listing):
    """Test getting listing by listing_id."""
    repository.create(sample_listing)

    result = repository.get_by_id("test-listing-1")

    assert result is not None
    assert result.listing_id == "test-listing-1"
    assert result.location.city == "Moscow"


def test_get_by_id_not_found(repository):
    """Test getting non-existent listing."""
    result = repository.get_by_id("non-existent")

    assert result is None


def test_get_by_db_id(repository, sample_listing, db_session):
    """Test getting listing by database id."""
    created = repository.create(sample_listing)
    
    # Get the database ID from the database directly
    from core.database.models import ListingModel
    db_listing = db_session.query(ListingModel).filter(ListingModel.listing_id == "test-listing-1").first()

    result = repository.get_by_db_id(db_listing.id)

    assert result is not None
    assert result.listing_id == "test-listing-1"


def test_get_all_no_filter(repository, sample_listing):
    """Test getting all listings without filter."""
    # Create multiple listings
    repository.create(sample_listing)

    listing2 = sample_listing.model_copy(update={"listing_id": "test-listing-2"})
    repository.create(listing2)

    listing3 = sample_listing.model_copy(update={"listing_id": "test-listing-3"})
    repository.create(listing3)

    result = repository.get_all()

    assert len(result) == 3


def test_get_all_with_pagination(repository, sample_listing):
    """Test pagination."""
    # Create multiple listings
    for i in range(15):
        listing = sample_listing.model_copy(update={"listing_id": f"test-listing-{i}"})
        repository.create(listing)

    # Get first page
    page1 = repository.get_all(skip=0, limit=10)
    assert len(page1) == 10

    # Get second page
    page2 = repository.get_all(skip=10, limit=10)
    assert len(page2) == 5


def test_get_all_with_city_filter(repository, sample_listing):
    """Test filtering by city."""
    repository.create(sample_listing)

    listing2 = sample_listing.model_copy(
        update={
            "listing_id": "test-listing-2",
            "location": Location(
                country="Russia",
                city="St. Petersburg",
                address="Nevsky Prospect, 1",
            ),
        }
    )
    repository.create(listing2)

    result = repository.get_all(city="Moscow")

    assert len(result) == 1
    assert result[0].location.city == "Moscow"


def test_count_all(repository, sample_listing):
    """Test counting all listings."""
    repository.create(sample_listing)

    listing2 = sample_listing.model_copy(update={"listing_id": "test-listing-2"})
    repository.create(listing2)

    count = repository.count()

    assert count == 2


def test_count_with_city_filter(repository, sample_listing):
    """Test counting with city filter."""
    repository.create(sample_listing)

    listing2 = sample_listing.model_copy(
        update={
            "listing_id": "test-listing-2",
            "location": Location(
                country="Russia",
                city="St. Petersburg",
                address="Nevsky Prospect, 1",
            ),
        }
    )
    repository.create(listing2)

    count = repository.count(city="Moscow")

    assert count == 1


def test_update_listing(repository, sample_listing):
    """Test updating listing."""
    repository.create(sample_listing)

    result = repository.update(
        "test-listing-1", fraud_score=75.0, description="Updated"
    )

    assert result is not None
    assert result.fraud_score == 75.0
    assert result.description == "Updated"


def test_update_non_existent(repository):
    """Test updating non-existent listing."""
    result = repository.update("non-existent", fraud_score=50.0)

    assert result is None


def test_delete_listing(repository, sample_listing):
    """Test deleting listing."""
    repository.create(sample_listing)

    result = repository.delete("test-listing-1")

    assert result is True

    # Verify deletion
    listing = repository.get_by_id("test-listing-1")
    assert listing is None


def test_delete_non_existent(repository):
    """Test deleting non-existent listing."""
    result = repository.delete("non-existent")

    assert result is False


def test_get_by_fraud_score_range(repository, sample_listing):
    """Test getting listings by fraud score range."""
    repository.create(sample_listing)  # fraud_score = 25.5

    listing2 = sample_listing.model_copy(
        update={"listing_id": "test-listing-2", "fraud_score": 50.0}
    )
    repository.create(listing2)

    listing3 = sample_listing.model_copy(
        update={"listing_id": "test-listing-3", "fraud_score": 75.0}
    )
    repository.create(listing3)

    result = repository.get_by_fraud_score_range(20.0, 60.0)

    assert len(result) == 2
    assert all(20.0 <= listing.fraud_score <= 60.0 for listing in result)


def test_get_by_price_range(repository, sample_listing):
    """Test getting listings by price range."""
    repository.create(sample_listing)  # price = 5000000

    listing2 = sample_listing.model_copy(
        update={
            "listing_id": "test-listing-2",
            "price": Price(amount=3000000.00, currency="RUB"),
        }
    )
    repository.create(listing2)

    listing3 = sample_listing.model_copy(
        update={
            "listing_id": "test-listing-3",
            "price": Price(amount=7000000.00, currency="RUB"),
        }
    )
    repository.create(listing3)

    result = repository.get_by_price_range(2000000.00, 6000000.00)

    assert len(result) == 2
    assert all(2000000.00 <= listing.price.amount <= 6000000.00 for listing in result)


def test_get_by_price_range_with_city(repository, sample_listing):
    """Test getting listings by price range and city."""
    repository.create(sample_listing)  # Moscow, 5000000

    listing2 = sample_listing.model_copy(
        update={
            "listing_id": "test-listing-2",
            "location": Location(city="St. Petersburg"),
            "price": Price(amount=4000000.00, currency="RUB"),
        }
    )
    repository.create(listing2)

    result = repository.get_by_price_range(3000000.00, 6000000.00, city="Moscow")

    assert len(result) == 1
    assert result[0].location.city == "Moscow"


def test_create_listing_with_media(repository, sample_listing):
    """Test that media is correctly stored as JSONB."""
    result = repository.create(sample_listing)

    assert result.media is not None
    assert len(result.media.images) == 2
    assert result.media.images[0].url == "https://example.com/img1.jpg"
    assert result.media.images[0].caption == "Living room"
