"""Integration tests for Listings API filter combinations.

Tests various filter combinations: city, price range, fraud score,
and their combinations with pagination.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

pytestmark = [pytest.mark.integration, pytest.mark.database, pytest.mark.api]


@pytest.fixture
def diverse_dataset(client: TestClient):
    """Create a diverse dataset with various cities, prices, and fraud scores.

    Returns 30 listings with:
    - 3 cities: Moscow (10), SPB (10), Kazan (10)
    - Price range: 500k - 5M RUB
    - Fraud scores: 0.0 - 1.0
    """
    listing_ids = []
    cities = ["Moscow", "Saint Petersburg", "Kazan"]

    for i in range(30):
        city = cities[i % 3]
        listing_data = {
            "listing": {
                "listing_id": f"test_filter_{i:03d}",
                "source": {
                    "plugin_id": "test_plugin",
                    "platform": "test.com",
                },
                "type": "sale" if i % 2 == 0 else "rent",
                "property_type": "apartment",
                "location": {"city": city, "country": "Russia"},
                "price": {
                    "amount": 500000.0 + i * 150000,
                    "currency": "RUB",
                },
                "fraud_score": round((i % 11) * 0.1, 2),  # 0.0 to 1.0
            }
        }

        response = client.post("/api/v1/listings/", json=listing_data)
        assert response.status_code == status.HTTP_201_CREATED
        listing_ids.append(f"test_filter_{i:03d}")

    yield listing_ids

    # Cleanup
    for listing_id in listing_ids:
        client.delete(f"/api/v1/listings/{listing_id}")


def test_filter_by_city(client: TestClient, diverse_dataset):
    """Test filtering by city.

    Validates:
    - Only listings from specified city are returned
    - Total count reflects filtered results
    """
    response = client.get("/api/v1/listings/?city=Moscow&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["total"] >= 10  # At least 10 Moscow listings

    # Verify all returned listings are from Moscow
    for item in data["items"]:
        if item["listing_id"].startswith("test_filter_"):
            assert item["location"]["city"] == "Moscow"


def test_filter_by_multiple_cities(client: TestClient, diverse_dataset):
    """Test filtering by different cities returns different results."""
    cities = ["Moscow", "Saint Petersburg", "Kazan"]

    for city in cities:
        response = client.get(f"/api/v1/listings/?city={city}&page_size=50")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["total"] >= 10

        # Verify all items match the city
        for item in data["items"]:
            if item["listing_id"].startswith("test_filter_"):
                assert item["location"]["city"] == city


def test_filter_by_price_min(client: TestClient, diverse_dataset):
    """Test filtering by minimum price.

    Validates:
    - Only listings >= price_min are returned
    """
    price_min = 2000000.0
    response = client.get(f"/api/v1/listings/?price_min={price_min}&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) > 0

    # Verify all returned listings have price >= price_min
    for item in data["items"]:
        if item["listing_id"].startswith("test_filter_"):
            assert item["price"]["amount"] >= price_min


def test_filter_by_price_max(client: TestClient, diverse_dataset):
    """Test filtering by maximum price.

    Validates:
    - Only listings <= price_max are returned
    """
    price_max = 2000000.0
    response = client.get(f"/api/v1/listings/?price_max={price_max}&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) > 0

    # Verify all returned listings have price <= price_max
    for item in data["items"]:
        if item["listing_id"].startswith("test_filter_"):
            assert item["price"]["amount"] <= price_max


def test_filter_by_price_range(client: TestClient, diverse_dataset):
    """Test filtering by price range (min and max).

    Validates:
    - Only listings within price range are returned
    """
    price_min = 1000000.0
    price_max = 3000000.0
    response = client.get(f"/api/v1/listings/?price_min={price_min}&price_max={price_max}&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) > 0

    # Verify all returned listings are within price range
    for item in data["items"]:
        if item["listing_id"].startswith("test_filter_"):
            assert price_min <= item["price"]["amount"] <= price_max


def test_filter_by_fraud_score_min(client: TestClient, diverse_dataset):
    """Test filtering by minimum fraud score.

    Validates:
    - Only listings >= fraud_score_min are returned
    """
    fraud_score_min = 0.5
    response = client.get(f"/api/v1/listings/?fraud_score_min={fraud_score_min}&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) > 0

    # Verify all returned listings have fraud_score >= fraud_score_min
    for item in data["items"]:
        if item["listing_id"].startswith("test_filter_") and item["fraud_score"]:
            assert item["fraud_score"] >= fraud_score_min


def test_filter_by_fraud_score_max(client: TestClient, diverse_dataset):
    """Test filtering by maximum fraud score.

    Validates:
    - Only listings <= fraud_score_max are returned
    """
    fraud_score_max = 0.3
    response = client.get(f"/api/v1/listings/?fraud_score_max={fraud_score_max}&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) > 0

    # Verify all returned listings have fraud_score <= fraud_score_max
    for item in data["items"]:
        if item["listing_id"].startswith("test_filter_") and item["fraud_score"]:
            assert item["fraud_score"] <= fraud_score_max


def test_filter_by_fraud_score_range(client: TestClient, diverse_dataset):
    """Test filtering by fraud score range (min and max).

    Validates:
    - Only listings within fraud score range are returned
    """
    fraud_score_min = 0.3
    fraud_score_max = 0.7
    response = client.get(
        f"/api/v1/listings/?fraud_score_min={fraud_score_min}&fraud_score_max={fraud_score_max}&page_size=50"
    )
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert len(data["items"]) > 0

    # Verify all returned listings are within fraud score range
    for item in data["items"]:
        if item["listing_id"].startswith("test_filter_") and item["fraud_score"]:
            assert fraud_score_min <= item["fraud_score"] <= fraud_score_max


def test_filter_combination_city_and_price(client: TestClient, diverse_dataset):
    """Test combining city and price filters.

    Validates:
    - Results match both city AND price criteria
    """
    city = "Moscow"
    price_min = 1000000.0
    price_max = 3000000.0

    response = client.get(f"/api/v1/listings/?city={city}&price_min={price_min}&price_max={price_max}&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    # Verify all items match both filters
    for item in data["items"]:
        if item["listing_id"].startswith("test_filter_"):
            assert item["location"]["city"] == city
            assert price_min <= item["price"]["amount"] <= price_max


def test_filter_with_pagination(client: TestClient, diverse_dataset):
    """Test that filters work correctly with pagination.

    Validates:
    - Filtered results are paginated correctly
    - Total count reflects filtered data
    - Page navigation works with filters
    """
    city = "Moscow"

    # Page 1
    response1 = client.get(f"/api/v1/listings/?city={city}&page=1&page_size=5")
    assert response1.status_code == status.HTTP_200_OK
    data1 = response1.json()
    assert len(data1["items"]) <= 5
    assert data1["page"] == 1

    # Page 2
    response2 = client.get(f"/api/v1/listings/?city={city}&page=2&page_size=5")
    assert response2.status_code == status.HTTP_200_OK
    data2 = response2.json()
    assert data2["page"] == 2

    # Ensure no overlap
    ids1 = {item["listing_id"] for item in data1["items"]}
    ids2 = {item["listing_id"] for item in data2["items"]}
    assert len(ids1 & ids2) == 0, "Pages should not have overlapping items"


def test_filter_no_results(client: TestClient, diverse_dataset):
    """Test filters that return no results.

    Validates:
    - Empty items array
    - Total count is 0
    - No error occurs
    """
    response = client.get("/api/v1/listings/?city=NonExistentCity&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # Should return empty or only listings not matching our test data
    test_items = [item for item in data["items"] if item["listing_id"].startswith("test_filter_")]
    assert len(test_items) == 0


def test_filter_invalid_fraud_score(client: TestClient, diverse_dataset):
    """Test invalid fraud score parameters.

    Should return 422 validation error for:
    - fraud_score < 0
    - fraud_score > 1
    """
    # fraud_score_min < 0
    response = client.get("/api/v1/listings/?fraud_score_min=-0.1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # fraud_score_max > 1
    response = client.get("/api/v1/listings/?fraud_score_max=1.5")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_filter_invalid_price(client: TestClient, diverse_dataset):
    """Test invalid price parameters.

    Should return 422 validation error for negative prices.
    """
    # Negative price_min
    response = client.get("/api/v1/listings/?price_min=-1000")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Negative price_max
    response = client.get("/api/v1/listings/?price_max=-500")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_filter_price_min_greater_than_max(client: TestClient, diverse_dataset):
    """Test logical inconsistency: price_min > price_max.

    Should return empty results (no error).
    """
    response = client.get("/api/v1/listings/?price_min=5000000&price_max=1000000&page_size=50")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    # Should return no test items (logically impossible filter)
    test_items = [item for item in data["items"] if item["listing_id"].startswith("test_filter_")]
    assert len(test_items) == 0


def test_filter_fraud_score_exact_boundaries(client: TestClient, diverse_dataset):
    """Test fraud score filter with exact boundary values.

    Validates inclusive boundaries (>= and <=).
    """
    # Create a listing with exact fraud score
    listing_data = {
        "listing": {
            "listing_id": "test_boundary_001",
            "source": {"plugin_id": "test", "platform": "test.com"},
            "type": "sale",
            "property_type": "apartment",
            "location": {"city": "Moscow"},
            "price": {"amount": 1000000.0, "currency": "RUB"},
            "fraud_score": 0.5,
        }
    }
    client.post("/api/v1/listings/", json=listing_data)

    # Test inclusive lower boundary
    response = client.get("/api/v1/listings/?fraud_score_min=0.5&page_size=50")
    data = response.json()
    boundary_items = [item for item in data["items"] if item["listing_id"] == "test_boundary_001"]
    assert len(boundary_items) == 1

    # Test inclusive upper boundary
    response = client.get("/api/v1/listings/?fraud_score_max=0.5&page_size=50")
    data = response.json()
    boundary_items = [item for item in data["items"] if item["listing_id"] == "test_boundary_001"]
    assert len(boundary_items) == 1

    # Cleanup
    client.delete("/api/v1/listings/test_boundary_001")
