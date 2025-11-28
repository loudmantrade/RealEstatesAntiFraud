"""Integration tests for Listings API CRUD operations.

This module tests the full lifecycle of listings including create, read, update,
delete operations with real database transactions.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_full_crud_lifecycle(client: TestClient):
    """Test complete CRUD lifecycle: create → read → delete.

    Validates:
    - Creating a new listing
    - Reading the created listing by ID
    - Listing all listings includes the created one
    - Deleting the listing
    - Confirming deletion (404 on subsequent read)
    """
    # Step 1: Create a new listing
    listing_data = {
        "listing": {
            "listing_id": "test_crud_001",
            "source": {
                "plugin_id": "cian_plugin",
                "platform": "cian.ru",
                "original_id": "12345",
                "url": "https://cian.ru/sale/flat/12345/",
            },
            "type": "sale",
            "property_type": "apartment",
            "location": {
                "country": "Russia",
                "city": "Moscow",
                "address": "Tverskaya str. 1",
                "coordinates": {"lat": 55.7558, "lng": 37.6173},
            },
            "price": {
                "amount": 10000000.0,
                "currency": "RUB",
                "price_per_sqm": 150000.0,
            },
            "description": "Beautiful apartment in city center",
            "media": {
                "images": [
                    {"url": "https://example.com/img1.jpg", "caption": "Living room"}
                ]
            },
            "fraud_score": 0.15,
        }
    }

    create_response = client.post("/api/v1/listings/", json=listing_data)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_listing = create_response.json()["data"]
    assert created_listing["listing_id"] == "test_crud_001"
    assert created_listing["location"]["city"] == "Moscow"
    assert created_listing["price"]["amount"] == 10000000.0

    # Step 2: Read the created listing
    get_response = client.get("/api/v1/listings/test_crud_001")
    assert get_response.status_code == status.HTTP_200_OK
    retrieved_listing = get_response.json()["data"]
    assert retrieved_listing["listing_id"] == "test_crud_001"
    assert retrieved_listing["description"] == "Beautiful apartment in city center"
    assert retrieved_listing["fraud_score"] == 0.15

    # Step 3: Verify listing appears in list
    list_response = client.get("/api/v1/listings/")
    assert list_response.status_code == status.HTTP_200_OK
    listings_data = list_response.json()
    assert listings_data["total"] >= 1
    listing_ids = [listing["listing_id"] for listing in listings_data["items"]]
    assert "test_crud_001" in listing_ids

    # Step 4: Delete the listing
    delete_response = client.delete("/api/v1/listings/test_crud_001")
    assert delete_response.status_code == status.HTTP_200_OK
    delete_data = delete_response.json()
    assert delete_data["listing_id"] == "test_crud_001"
    assert delete_data["deleted"] is True

    # Step 5: Confirm deletion (should return 404)
    get_after_delete = client.get("/api/v1/listings/test_crud_001")
    assert get_after_delete.status_code == status.HTTP_404_NOT_FOUND


def test_create_duplicate_listing(client: TestClient):
    """Test that creating a duplicate listing returns 400 error.

    Validates:
    - Creating a listing succeeds
    - Attempting to create the same listing again fails with 400
    """
    listing_data = {
        "listing": {
            "listing_id": "test_duplicate_001",
            "source": {
                "plugin_id": "cian_plugin",
                "platform": "cian.ru",
            },
            "type": "rent",
            "property_type": "house",
            "location": {"city": "Saint Petersburg"},
            "price": {"amount": 50000.0, "currency": "RUB"},
        }
    }

    # First creation should succeed
    first_response = client.post("/api/v1/listings/", json=listing_data)
    assert first_response.status_code == status.HTTP_201_CREATED

    # Second creation should fail
    second_response = client.post("/api/v1/listings/", json=listing_data)
    assert second_response.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in second_response.json()["detail"].lower()

    # Cleanup
    client.delete("/api/v1/listings/test_duplicate_001")


def test_get_nonexistent_listing(client: TestClient):
    """Test that getting a non-existent listing returns 404."""
    response = client.get("/api/v1/listings/nonexistent_id_999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_delete_nonexistent_listing(client: TestClient):
    """Test that deleting a non-existent listing returns 404."""
    response = client.delete("/api/v1/listings/nonexistent_id_999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_create_multiple_listings(client: TestClient):
    """Test creating multiple listings in sequence.

    Validates:
    - Multiple listings can be created
    - Each has unique ID
    - All appear in listings list
    """
    listing_ids = []

    for i in range(5):
        listing_data = {
            "listing": {
                "listing_id": f"test_multi_{i:03d}",
                "source": {
                    "plugin_id": "test_plugin",
                    "platform": "test.com",
                },
                "type": "sale" if i % 2 == 0 else "rent",
                "property_type": "apartment",
                "location": {"city": f"City_{i}"},
                "price": {"amount": 1000000.0 + i * 100000, "currency": "RUB"},
                "fraud_score": i * 0.1,
            }
        }

        response = client.post("/api/v1/listings/", json=listing_data)
        assert response.status_code == status.HTTP_201_CREATED
        listing_ids.append(f"test_multi_{i:03d}")

    # Verify all created listings appear in the list
    list_response = client.get("/api/v1/listings/?page_size=100")
    assert list_response.status_code == status.HTTP_200_OK
    all_listing_ids = [
        listing["listing_id"] for listing in list_response.json()["items"]
    ]

    for listing_id in listing_ids:
        assert listing_id in all_listing_ids

    # Cleanup
    for listing_id in listing_ids:
        client.delete(f"/api/v1/listings/{listing_id}")
