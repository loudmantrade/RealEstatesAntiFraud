"""Unit tests for listings API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.api.main import app
from core.database import Base, get_db
from core.models.udm import Listing

# Test database setup - use unique in-memory DB per test module
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="module")
def TestingSessionLocal(test_engine):
    """Create a session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_database(test_engine, TestingSessionLocal):
    """Create tables before each test and drop after."""
    # Clean all data before each test
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    # Override the dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    # Clean up after test
    Base.metadata.drop_all(bind=test_engine)

    # Remove override
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


@pytest.fixture
def client(setup_database):
    """Create a test client."""
    return TestClient(app)


def make_listing_data(
    listing_id: str,
    city: str = "TestCity",
    price: float = 100000.0,
    fraud_score: float = None,
) -> dict:
    """Helper to create test listing data."""
    data = {
        "listing": {
            "listing_id": listing_id,
            "source": {
                "plugin_id": "test_plugin",
                "platform": "test_platform",
                "url": f"https://example.com/listing/{listing_id}",
            },
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": city, "country": "TestCountry"},
            "price": {"amount": price, "currency": "USD"},
            "description": f"Test listing {listing_id}",
        }
    }
    if fraud_score is not None:
        data["listing"]["fraud_score"] = fraud_score
    return data


def test_health_endpoint(client):
    """Test health check endpoint is not versioned."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


def test_openapi_docs_at_v1_path(client):
    """Test OpenAPI docs are available at /api/v1/docs."""
    response = client.get("/api/v1/docs")
    assert response.status_code == 200


def test_create_listing(client):
    """Test creating a new listing via API."""
    listing_data = {
        "listing": {
            "listing_id": "test-001",
            "source": {
                "plugin_id": "test_plugin",
                "platform": "test_platform",
                "url": "https://example.com/listing/001",
            },
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": "TestCity", "country": "TestCountry"},
            "price": {"amount": 100000.0, "currency": "USD"},
            "description": "A test apartment",
        }
    }

    response = client.post("/api/v1/listings/", json=listing_data)
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["listing_id"] == "test-001"
    assert data["data"]["description"] == "A test apartment"


def test_create_duplicate_listing(client):
    """Test creating a duplicate listing returns 400."""
    listing_data = make_listing_data("test-002")

    # Create first listing
    response = client.post("/api/v1/listings/", json=listing_data)
    assert response.status_code == 201

    # Try to create duplicate
    response = client.post("/api/v1/listings/", json=listing_data)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_get_listing(client):
    """Test retrieving a listing by ID."""
    # Create a listing first
    listing_data = make_listing_data("test-003", price=200000.0)
    client.post("/api/v1/listings/", json=listing_data)

    # Retrieve it
    response = client.get("/api/v1/listings/test-003")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["listing_id"] == "test-003"
    assert data["data"]["description"] == "Test listing test-003"


def test_get_nonexistent_listing(client):
    """Test retrieving a non-existent listing returns 404."""
    response = client.get("/api/v1/listings/nonexistent")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_delete_listing(client):
    """Test deleting a listing."""
    # Create a listing first
    listing_data = make_listing_data("test-004", price=500000.0)
    client.post("/api/v1/listings/", json=listing_data)

    # Delete it
    response = client.delete("/api/v1/listings/test-004")
    assert response.status_code == 200
    data = response.json()
    assert data["listing_id"] == "test-004"
    assert data["deleted"] is True

    # Verify it's gone
    response = client.get("/api/v1/listings/test-004")
    assert response.status_code == 404


def test_list_listings_empty(client):
    """Test listing when no listings exist."""
    response = client.get("/api/v1/listings/")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["total_pages"] == 0


def test_list_listings_with_data(client):
    """Test listing with multiple listings."""
    # Create some listings
    for i in range(5):
        listing_data = make_listing_data(f"test-{i:03d}", price=100000.0 + (i * 10000))
        client.post("/api/v1/listings/", json=listing_data)

    # List all
    response = client.get("/api/v1/listings/")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["total_pages"] == 1


def test_pagination(client):
    """Test pagination with page and page_size parameters."""
    # Create 25 listings
    for i in range(25):
        listing_data = make_listing_data(f"test-{i:03d}")
        client.post("/api/v1/listings/", json=listing_data)

    # Get first page (default 20 items)
    response = client.get("/api/v1/listings/?page=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["total_pages"] == 2

    # Get second page
    response = client.get("/api/v1/listings/?page=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2

    # Test custom page size
    response = client.get("/api/v1/listings/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 10
    assert data["total_pages"] == 3


def test_filter_by_city(client):
    """Test filtering listings by city."""
    # Create listings in different cities
    cities = ["CityA", "CityB", "CityA", "CityC", "CityA"]
    for i, city in enumerate(cities):
        listing_data = make_listing_data(f"test-{i:03d}", city=city)
        client.post("/api/v1/listings/", json=listing_data)

    # Filter by CityA
    response = client.get("/api/v1/listings/?city=CityA")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert all(item["location"]["city"] == "CityA" for item in data["items"])


def test_filter_by_price_range(client):
    """Test filtering listings by price range."""
    # Create listings with different prices
    prices = [50000, 100000, 150000, 200000, 250000]
    for i, price in enumerate(prices):
        listing_data = make_listing_data(f"test-{i:03d}", price=float(price))
        client.post("/api/v1/listings/", json=listing_data)

    # Filter by price range
    response = client.get("/api/v1/listings/?price_min=100000&price_max=200000")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    for item in data["items"]:
        assert 100000 <= item["price"]["amount"] <= 200000


def test_filter_by_fraud_score_range(client):
    """Test filtering listings by fraud score range."""
    # Create listings with different fraud scores
    scores = [0.1, 0.3, 0.5, 0.7, 0.9]
    for i, score in enumerate(scores):
        listing_data = make_listing_data(f"test-{i:03d}", fraud_score=score)
        client.post("/api/v1/listings/", json=listing_data)

    # Filter by fraud score range
    response = client.get("/api/v1/listings/?fraud_score_min=0.3&fraud_score_max=0.7")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    for item in data["items"]:
        assert 0.3 <= item["fraud_score"] <= 0.7


def test_combined_filters(client):
    """Test combining multiple filters."""
    # Create listings with varied properties
    for i in range(10):
        city = "CityA" if i % 2 == 0 else "CityB"
        price = 100000.0 + (i * 20000)
        listing_data = make_listing_data(f"test-{i:03d}", city=city, price=price)
        client.post("/api/v1/listings/", json=listing_data)

    # Filter by city and price
    response = client.get(
        "/api/v1/listings/?city=CityA&price_min=100000&price_max=150000"
    )
    assert response.status_code == 200
    data = response.json()
    # CityA listings: 0, 2, 4, 6, 8
    # Prices: 100k, 140k, 180k, 220k, 260k
    # In range 100k-150k: 0 (100k), 2 (140k)
    assert data["total"] == 2
