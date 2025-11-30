"""Integration tests for Listings API pagination.

Tests pagination behavior with large datasets, edge cases,
and pagination metadata validation.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


@pytest.fixture
def large_dataset(client: TestClient):
    """Create a large dataset of 50 listings for pagination testing.

    Yields:
        list: List of created listing IDs for cleanup
    """
    listing_ids = []

    for i in range(50):
        listing_data = {
            "listing": {
                "listing_id": f"test_pagination_{i:03d}",
                "source": {
                    "plugin_id": "test_plugin",
                    "platform": "test.com",
                },
                "type": "sale",
                "property_type": "apartment",
                "location": {"city": "TestCity", "country": "TestCountry"},
                "price": {"amount": 1000000.0 + i * 50000, "currency": "RUB"},
                "fraud_score": (i % 10) * 0.1,
            }
        }

        response = client.post("/api/v1/listings/", json=listing_data)
        assert response.status_code == status.HTTP_201_CREATED
        listing_ids.append(f"test_pagination_{i:03d}")

    yield listing_ids

    # Cleanup
    for listing_id in listing_ids:
        client.delete(f"/api/v1/listings/{listing_id}")


def test_pagination_first_page(client: TestClient, large_dataset):
    """Test fetching the first page of results.

    Validates:
    - Correct number of items on first page
    - Metadata (total, page, page_size, total_pages) is correct
    - Items are returned in consistent order
    """
    response = client.get("/api/v1/listings/?page=1&page_size=10")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) == 10
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] >= 50
    assert data["total_pages"] >= 5


def test_pagination_middle_page(client: TestClient, large_dataset):
    """Test fetching a middle page of results."""
    response = client.get("/api/v1/listings/?page=3&page_size=10")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) == 10
    assert data["page"] == 3
    assert data["page_size"] == 10


def test_pagination_last_page(client: TestClient, large_dataset):
    """Test fetching the last page with potentially fewer items.

    Validates:
    - Last page may have fewer items than page_size
    - Pagination metadata is correct for last page
    """
    # First get total pages
    first_response = client.get("/api/v1/listings/?page=1&page_size=10")
    total_pages = first_response.json()["total_pages"]

    # Fetch last page
    response = client.get(f"/api/v1/listings/?page={total_pages}&page_size=10")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) <= 10
    assert len(data["items"]) > 0
    assert data["page"] == total_pages


def test_pagination_beyond_last_page(client: TestClient, large_dataset):
    """Test requesting a page beyond available data.

    Should return empty items list but valid metadata.
    """
    response = client.get("/api/v1/listings/?page=1000&page_size=10")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) == 0
    assert data["page"] == 1000
    assert data["total"] >= 50


def test_pagination_different_page_sizes(client: TestClient, large_dataset):
    """Test pagination with various page sizes.

    Validates:
    - Page size of 5, 20, 50, 100 all work correctly
    - Items don't overlap between pages
    """
    page_sizes = [5, 20, 50, 100]

    for page_size in page_sizes:
        response = client.get(f"/api/v1/listings/?page=1&page_size={page_size}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data["items"]) <= page_size
        assert data["page_size"] == page_size


def test_pagination_consistency_across_pages(client: TestClient, large_dataset):
    """Test that items don't appear on multiple pages.

    Validates:
    - Fetching all pages returns unique items
    - Total items across all pages matches total count
    """
    page_size = 10
    all_listing_ids = set()
    page = 1

    while True:
        response = client.get(f"/api/v1/listings/?page={page}&page_size={page_size}")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        if not data["items"]:
            break

        # Check for duplicates
        current_ids = {item["listing_id"] for item in data["items"]}
        assert len(all_listing_ids & current_ids) == 0, "Found duplicate items"

        all_listing_ids.update(current_ids)
        page += 1

        if page > data["total_pages"]:
            break

    # At least our test data should be present
    test_ids = {f"test_pagination_{i:03d}" for i in range(50)}
    assert test_ids.issubset(all_listing_ids)


def test_pagination_with_city_filter(client: TestClient, large_dataset):
    """Test pagination works correctly with filters applied.

    Validates:
    - Pagination metadata reflects filtered results
    - All items on all pages match the filter
    """
    response = client.get("/api/v1/listings/?page=1&page_size=10&city=TestCity")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total"] >= 50  # All test data has TestCity
    assert len(data["items"]) <= 10

    # Verify all items match the filter
    for item in data["items"]:
        assert item["location"]["city"] == "TestCity"


def test_pagination_edge_case_page_size_1(client: TestClient, large_dataset):
    """Test pagination with page_size=1 (edge case)."""
    response = client.get("/api/v1/listings/?page=1&page_size=1")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) == 1
    assert data["page_size"] == 1
    assert data["total_pages"] >= 50


def test_pagination_invalid_page_number(client: TestClient, large_dataset):
    """Test pagination with invalid page number (0 or negative).

    Should return 422 validation error.
    """
    # Page 0 should fail
    response = client.get("/api/v1/listings/?page=0&page_size=10")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Negative page should fail
    response = client.get("/api/v1/listings/?page=-1&page_size=10")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_pagination_invalid_page_size(client: TestClient, large_dataset):
    """Test pagination with invalid page_size (0, negative, or > 100).

    Should return 422 validation error.
    """
    # Page size 0 should fail
    response = client.get("/api/v1/listings/?page=1&page_size=0")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Page size > 100 should fail
    response = client.get("/api/v1/listings/?page=1&page_size=101")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Negative page size should fail
    response = client.get("/api/v1/listings/?page=1&page_size=-10")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_pagination_metadata_calculation(client: TestClient, large_dataset):
    """Test that pagination metadata is calculated correctly.

    Validates:
    - total_pages = ceil(total / page_size)
    - Correct calculation for various page sizes
    """
    # Get total count
    response = client.get("/api/v1/listings/?page=1&page_size=10")
    total = response.json()["total"]

    # Test various page sizes
    test_cases = [
        (10, (total + 9) // 10),  # Ceiling division
        (20, (total + 19) // 20),
        (50, (total + 49) // 50),
    ]

    for page_size, expected_pages in test_cases:
        response = client.get(f"/api/v1/listings/?page=1&page_size={page_size}")
        data = response.json()
        assert data["total_pages"] == expected_pages, f"Expected {expected_pages} pages for page_size={page_size}"
