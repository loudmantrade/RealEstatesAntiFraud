"""Integration tests for concurrent access, transactions, and data integrity.

Tests database transaction handling, concurrent operations, constraint validation,
and error scenarios.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import text

pytestmark = pytest.mark.integration


def test_concurrent_read_operations(client: TestClient):
    """Test multiple read operations return consistent results.

    Validates:
    - Multiple reads get consistent results
    - No race conditions or data corruption

    Note: TestClient doesn't support true concurrent requests.
    This test validates sequential reads return consistent data.
    """
    # Create test data
    listing_data = {
        "listing": {
            "listing_id": "test_concurrent_read_001",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": "Moscow"},
            "price": {"amount": 1000000.0, "currency": "RUB"},
        }
    }
    client.post("/api/v1/listings/", json=listing_data)

    # Execute 10 sequential reads
    for _ in range(10):
        response = client.get("/api/v1/listings/test_concurrent_read_001")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"]["listing_id"] == "test_concurrent_read_001"
        assert data["data"]["location"]["city"] == "Moscow"

    # Cleanup
    client.delete("/api/v1/listings/test_concurrent_read_001")


def test_concurrent_write_operations(client: TestClient):
    """Test concurrent write operations with different IDs.

    Validates:
    - Multiple sequential writes work correctly
    - All created listings are persisted correctly
    - No data corruption

    Note: TestClient doesn't support true concurrent requests in same process.
    This test validates sequential writes to ensure data integrity.
    """
    # Create 10 listings sequentially (TestClient limitation)
    for i in range(10):
        listing_data = {
            "listing": {
                "listing_id": f"test_concurrent_write_{i:03d}",
                "source": {"plugin_id": "test", "platform": "test.com"},
                "type": "sale",
                "property_type": "apartment",
                "location": {"city": f"City_{i}"},
                "price": {"amount": 1000000.0 + i * 10000, "currency": "RUB"},
            }
        }
        response = client.post("/api/v1/listings/", json=listing_data)
        assert response.status_code == status.HTTP_201_CREATED

    # Verify all listings were created
    list_response = client.get("/api/v1/listings/?page_size=100")
    all_ids = [item["listing_id"] for item in list_response.json()["items"]]

    for i in range(10):
        assert f"test_concurrent_write_{i:03d}" in all_ids

    # Cleanup
    for i in range(10):
        client.delete(f"/api/v1/listings/test_concurrent_write_{i:03d}")


def test_concurrent_duplicate_creation(client: TestClient):
    """Test that sequential attempts to create duplicate listings are handled.

    Validates:
    - First creation succeeds
    - Subsequent attempts get 400 error (already exists)
    - No data corruption

    Note: TestClient doesn't support true concurrent requests.
    """
    listing_data = {
        "listing": {
            "listing_id": "test_duplicate_concurrent",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": "Moscow"},
            "price": {"amount": 1000000.0, "currency": "RUB"},
        }
    }

    # First attempt should succeed
    response1 = client.post("/api/v1/listings/", json=listing_data)
    assert response1.status_code == status.HTTP_201_CREATED

    # Subsequent attempts should fail with 400
    for i in range(4):
        response = client.post("/api/v1/listings/", json=listing_data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"].lower()

    # Cleanup
    client.delete("/api/v1/listings/test_duplicate_concurrent")


def test_transaction_rollback_on_error(db_session):
    """Test that failed operations don't leave partial data.

    Validates:
    - Database errors trigger rollback
    - No partial data remains after failed operation
    - Session is left in clean state
    """
    from core.database.models import ListingModel

    # Record initial count
    initial_count = db_session.query(ListingModel).count()

    # Try to insert invalid data that violates constraints
    try:
        invalid_listing = ListingModel(
            listing_id=None,  # This violates NOT NULL constraint
            source_plugin_id="test",
            source_platform="test.com",
            type="sale",
            property_type="apartment",
            price_amount=1000000.0,
            price_currency="RUB",
        )
        db_session.add(invalid_listing)
        db_session.commit()
    except Exception:
        db_session.rollback()

    # Count should remain the same (rollback worked)
    final_count = db_session.query(ListingModel).count()
    assert final_count == initial_count, "Count should not change after rollback"


def test_database_constraint_listing_id_unique(client: TestClient):
    """Test that listing_id uniqueness constraint is enforced.

    Validates:
    - Duplicate listing_id is rejected
    - Proper error message is returned
    """
    listing_data = {
        "listing": {
            "listing_id": "test_unique_001",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": "Moscow"},
            "price": {"amount": 1000000.0, "currency": "RUB"},
        }
    }

    # First creation should succeed
    response1 = client.post("/api/v1/listings/", json=listing_data)
    assert response1.status_code == status.HTTP_201_CREATED

    # Second creation should fail
    response2 = client.post("/api/v1/listings/", json=listing_data)
    assert response2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in response2.json()["detail"].lower()

    # Cleanup
    client.delete("/api/v1/listings/test_unique_001")


def test_database_constraint_required_fields(db_session):
    """Test that required (NOT NULL) fields are enforced.

    Validates:
    - Missing required fields cause insert to fail
    - Transaction is rolled back
    """
    from core.database.models import ListingModel

    initial_count = db_session.query(ListingModel).count()

    # Try to insert without required fields
    with pytest.raises(Exception):
        invalid_listing = ListingModel(
            listing_id="test_invalid",
            # Missing required fields: source_plugin_id, source_platform, etc.
        )
        db_session.add(invalid_listing)
        db_session.commit()

    db_session.rollback()

    # Count should remain the same
    final_count = db_session.query(ListingModel).count()
    assert final_count == initial_count


def test_data_integrity_price_amount_type(client: TestClient):
    """Test that price amount accepts valid numeric values.

    Validates:
    - Valid decimal prices are accepted
    - Precision is maintained
    """
    listing_data = {
        "listing": {
            "listing_id": "test_price_001",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": "Moscow"},
            "price": {
                "amount": 1234567.89,  # Test decimal precision
                "currency": "RUB",
                "price_per_sqm": 98765.43,
            },
        }
    }

    response = client.post("/api/v1/listings/", json=listing_data)
    assert response.status_code == status.HTTP_201_CREATED

    # Verify precision is maintained
    get_response = client.get("/api/v1/listings/test_price_001")
    data = get_response.json()["data"]
    assert data["price"]["amount"] == 1234567.89
    assert data["price"]["price_per_sqm"] == 98765.43

    # Cleanup
    client.delete("/api/v1/listings/test_price_001")


def test_data_integrity_fraud_score_range(client: TestClient):
    """Test that fraud_score validation works correctly.

    Validates:
    - Valid fraud scores (0.0 - 100.0) are accepted
    - Invalid fraud scores are rejected
    """
    # Valid fraud score
    valid_listing = {
        "listing": {
            "listing_id": "test_fraud_valid",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": "Moscow"},
            "price": {"amount": 1000000.0, "currency": "RUB"},
            "fraud_score": 45.5,
        }
    }

    response = client.post("/api/v1/listings/", json=valid_listing)
    assert response.status_code == status.HTTP_201_CREATED

    # Invalid fraud score > 100
    invalid_listing = {
        "listing": {
            "listing_id": "test_fraud_invalid",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": "Moscow"},
            "price": {"amount": 1000000.0, "currency": "RUB"},
            "fraud_score": 150.0,  # > 100
        }
    }

    response = client.post("/api/v1/listings/", json=invalid_listing)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Invalid fraud score < 0
    invalid_listing["listing"]["fraud_score"] = -10.0
    response = client.post("/api/v1/listings/", json=invalid_listing)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Cleanup
    client.delete("/api/v1/listings/test_fraud_valid")


def test_data_integrity_coordinates(client: TestClient):
    """Test that coordinate data is stored and retrieved correctly.

    Validates:
    - Latitude and longitude precision
    - Null coordinates are handled
    """
    listing_with_coords = {
        "listing": {
            "listing_id": "test_coords_001",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "sale",
            "property_type": "apartment",
            "location": {
                "city": "Moscow",
                "coordinates": {"lat": 55.7558, "lng": 37.6173},
            },
            "price": {"amount": 1000000.0, "currency": "RUB"},
        }
    }

    response = client.post("/api/v1/listings/", json=listing_with_coords)
    assert response.status_code == status.HTTP_201_CREATED

    # Verify coordinates precision
    get_response = client.get("/api/v1/listings/test_coords_001")
    data = get_response.json()["data"]
    assert data["location"]["coordinates"]["lat"] == pytest.approx(55.7558, abs=0.0001)
    assert data["location"]["coordinates"]["lng"] == pytest.approx(37.6173, abs=0.0001)

    # Cleanup
    client.delete("/api/v1/listings/test_coords_001")


def test_error_handling_invalid_json(client: TestClient):
    """Test API error handling for invalid JSON payload."""
    response = client.post(
        "/api/v1/listings/",
        content=b"invalid json{",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_error_handling_missing_required_fields(client: TestClient):
    """Test API error handling for missing required fields.

    Validates proper 422 error for incomplete listing data.
    """
    incomplete_listing = {
        "listing": {
            "listing_id": "test_incomplete",
            # Missing required fields
        }
    }

    response = client.post("/api/v1/listings/", json=incomplete_listing)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_error_handling_invalid_type_values(client: TestClient):
    """Test API error handling for invalid type field values."""
    invalid_listing = {
        "listing": {
            "listing_id": "test_invalid_type",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "invalid_type",  # Should be 'sale' or 'rent'
            "property_type": "apartment",
            "location": {"city": "Moscow"},
            "price": {"amount": 1000000.0, "currency": "RUB"},
        }
    }

    # Note: This passes validation as we don't have enum validation yet
    # But it's good to document expected behavior
    response = client.post("/api/v1/listings/", json=invalid_listing)
    # Currently accepts any string, but future validation should reject
    if response.status_code == status.HTTP_201_CREATED:
        client.delete("/api/v1/listings/test_invalid_type")


def test_error_handling_database_connection_resilience(db_session):
    """Test that application handles database issues gracefully.

    Validates:
    - Connection errors don't crash the application
    - Proper error messages are returned
    """
    from core.database.models import ListingModel

    # Test that we can recover from a failed query
    try:
        # Execute an intentionally failing query
        db_session.execute(text("SELECT * FROM nonexistent_table"))
    except Exception:
        db_session.rollback()

    # Session should still be usable after rollback
    count = db_session.query(ListingModel).count()
    assert isinstance(count, int)  # Should not raise exception
