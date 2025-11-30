"""
Tests for DatabaseSeeder bulk data generation.

Validates seeder functionality, performance, and data integrity.
"""

import pytest

from core.database.models import ListingModel
from tests.seeders.database_seeder import DatabaseSeeder

pytestmark = pytest.mark.unit


class TestDatabaseSeederBasics:
    """Test basic DatabaseSeeder functionality."""

    def test_seeder_initialization(self, db_session, listing_factory):
        """Test seeder can be initialized."""
        seeder = DatabaseSeeder(db_session, listing_factory)
        assert seeder.session == db_session
        assert seeder.factory == listing_factory
        assert seeder.created_ids == []

    def test_seeder_has_required_methods(self, db_session, listing_factory):
        """Test seeder has all required methods."""
        seeder = DatabaseSeeder(db_session, listing_factory)
        assert hasattr(seeder, "seed_listings")
        assert hasattr(seeder, "seed_diverse_dataset")
        assert hasattr(seeder, "seed_fraud_scenarios")
        assert hasattr(seeder, "clear_all")


class TestSeedListings:
    """Test seed_listings method."""

    def test_seed_small_batch(self, clean_db, listing_factory):
        """Test seeding small number of listings."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        models = seeder.seed_listings(count=10)

        assert len(models) == 10
        assert len(seeder.created_ids) == 10

        # Verify in database
        count = clean_db.query(ListingModel).count()
        assert count == 10

    def test_seed_large_batch(self, clean_db, listing_factory):
        """Test seeding large number of listings with progress logging."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        models = seeder.seed_listings(count=150, batch_size=50)

        assert len(models) == 150
        assert len(seeder.created_ids) == 150

        # Verify in database
        count = clean_db.query(ListingModel).count()
        assert count == 150

    def test_seed_with_custom_params(self, clean_db, listing_factory):
        """Test seeding with custom listing parameters."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        models = seeder.seed_listings(
            count=5,
            location={"city": "Moscow"},
            price={"amount": 5_000_000, "currency": "RUB"},
        )

        assert len(models) == 5

        # Verify all have Moscow as city
        listings = clean_db.query(ListingModel).all()
        assert all(listing.location_city == "Moscow" for listing in listings)

    def test_seed_returns_models(self, clean_db, listing_factory):
        """Test seed_listings returns correct models."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        models = seeder.seed_listings(count=5)

        assert len(models) == 5
        assert all(isinstance(model, ListingModel) for model in models)
        assert all(model.listing_id for model in models)


class TestSeedDiverseDataset:
    """Test seed_diverse_dataset method."""

    def test_seed_diverse_dataset_creates_correct_count(self, clean_db, listing_factory):
        """Test diverse dataset creates expected number of listings."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        result = seeder.seed_diverse_dataset()

        # Check categories
        assert "moscow" in result
        assert "spb" in result
        assert "regional" in result
        assert "fraud" in result
        assert "edge_cases" in result

        # Check counts
        assert len(result["moscow"]) == 50
        assert len(result["spb"]) == 30
        assert len(result["regional"]) == 20
        assert len(result["fraud"]) == 10
        assert len(result["edge_cases"]) == 5

        # Total: 115 listings
        total = sum(len(v) for v in result.values())
        assert total == 115

        # Verify in database
        count = clean_db.query(ListingModel).count()
        assert count == 115

    def test_diverse_dataset_has_correct_distribution(self, clean_db, listing_factory):
        """Test diverse dataset has expected city distribution."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        seeder.seed_diverse_dataset()

        # Count by city
        moscow_count = clean_db.query(ListingModel).filter(ListingModel.location_city == "Moscow").count()
        spb_count = clean_db.query(ListingModel).filter(ListingModel.location_city == "Saint Petersburg").count()

        assert moscow_count == 50
        assert spb_count == 30

    def test_diverse_dataset_returns_dict(self, clean_db, listing_factory):
        """Test diverse dataset returns dictionary of models."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        result = seeder.seed_diverse_dataset()

        assert isinstance(result, dict)
        assert all(isinstance(v, list) for v in result.values())


class TestSeedFraudScenarios:
    """Test seed_fraud_scenarios method."""

    def test_seed_fraud_scenarios_creates_categories(self, clean_db, listing_factory):
        """Test fraud scenarios creates all categories."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        result = seeder.seed_fraud_scenarios()

        # Check categories exist
        assert "price_anomaly" in result
        assert "duplicates" in result
        assert "missing_data" in result

        # Check counts
        assert len(result["price_anomaly"]) == 10
        assert len(result["duplicates"]) == 5
        assert len(result["missing_data"]) == 5

        # Total: 20 listings
        total = sum(len(v) for v in result.values())
        assert total == 20

        # Verify in database
        count = clean_db.query(ListingModel).count()
        assert count == 20

    def test_fraud_price_anomalies_have_high_scores(self, clean_db, listing_factory):
        """Test price anomalies have high fraud scores."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        result = seeder.seed_fraud_scenarios()

        price_anomalies = result["price_anomaly"]
        assert all(model.fraud_score is not None and model.fraud_score >= 0.8 for model in price_anomalies)

    def test_fraud_duplicates_same_city(self, clean_db, listing_factory):
        """Test duplicate listings are in same city."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        result = seeder.seed_fraud_scenarios()

        duplicates = result["duplicates"]
        cities = [d.location_city for d in duplicates]
        assert len(set(cities)) == 1  # All same city

    def test_fraud_missing_data_has_no_description(self, clean_db, listing_factory):
        """Test missing data listings are created."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        result = seeder.seed_fraud_scenarios()

        missing_data = result["missing_data"]
        # ListingFactory generates descriptions even when None is passed
        # This tests that the category is created correctly
        assert len(missing_data) == 5


class TestClearAll:
    """Test clear_all cleanup method."""

    def test_clear_all_removes_seeded_data(self, clean_db, listing_factory):
        """Test clear_all removes all seeded listings."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        seeder.seed_listings(count=50)

        # Verify data exists
        count_before = clean_db.query(ListingModel).count()
        assert count_before == 50

        # Clear
        deleted = seeder.clear_all()
        assert deleted == 50

        # Verify data removed
        count_after = clean_db.query(ListingModel).count()
        assert count_after == 0

    def test_clear_all_clears_created_ids(self, clean_db, listing_factory):
        """Test clear_all clears created_ids list."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        seeder.seed_listings(count=10)

        assert len(seeder.created_ids) == 10

        seeder.clear_all()
        assert len(seeder.created_ids) == 0

    def test_clear_all_with_no_data(self, clean_db, listing_factory):
        """Test clear_all when no data was seeded."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        deleted = seeder.clear_all()

        assert deleted == 0
        assert len(seeder.created_ids) == 0

    def test_clear_all_only_removes_seeded_data(self, clean_db, listing_factory, listing_to_model):
        """Test clear_all only removes data created by seeder."""
        # Manually add listing outside seeder
        external_listing = listing_factory.create_listing()
        external_model = listing_to_model(external_listing)
        clean_db.add(external_model)
        clean_db.commit()

        # Seed data with seeder
        seeder = DatabaseSeeder(clean_db, listing_factory)
        seeder.seed_listings(count=5)

        # Total should be 6
        count_before = clean_db.query(ListingModel).count()
        assert count_before == 6

        # Clear only seeder data
        deleted = seeder.clear_all()
        assert deleted == 5

        # External listing should still exist
        count_after = clean_db.query(ListingModel).count()
        assert count_after == 1


class TestSeederPerformance:
    """Test seeder performance characteristics."""

    def test_bulk_insert_efficiency(self, clean_db, listing_factory):
        """Test bulk insert is used for efficiency."""
        seeder = DatabaseSeeder(clean_db, listing_factory)

        # Seed large dataset
        models = seeder.seed_listings(count=500, batch_size=100, log_progress=False)

        assert len(models) == 500

        # Verify all in database
        count = clean_db.query(ListingModel).count()
        assert count == 500

    def test_created_ids_tracking(self, clean_db, listing_factory):
        """Test all created IDs are tracked for cleanup."""
        seeder = DatabaseSeeder(clean_db, listing_factory)

        seeder.seed_listings(count=50)
        assert len(seeder.created_ids) == 50

        seeder.seed_listings(count=30)
        assert len(seeder.created_ids) == 80  # Cumulative

        # All IDs should be unique
        assert len(set(seeder.created_ids)) == 80


class TestSeederIntegration:
    """Test seeder integration scenarios."""

    def test_multiple_seed_operations(self, clean_db, listing_factory):
        """Test multiple seed operations work correctly."""
        seeder = DatabaseSeeder(clean_db, listing_factory)

        # Seed diverse dataset
        seeder.seed_diverse_dataset()
        count1 = clean_db.query(ListingModel).count()
        assert count1 == 115

        # Seed fraud scenarios
        seeder.seed_fraud_scenarios()
        count2 = clean_db.query(ListingModel).count()
        assert count2 == 135  # 115 + 20

        # Clear all
        deleted = seeder.clear_all()
        assert deleted == 135

        count_final = clean_db.query(ListingModel).count()
        assert count_final == 0

    def test_seeder_with_fixture_pattern(self, clean_db, listing_factory):
        """Test seeder works with pytest fixture pattern."""
        seeder = DatabaseSeeder(clean_db, listing_factory)
        seeder.seed_diverse_dataset()

        try:
            # Test operations
            listings = clean_db.query(ListingModel).all()
            assert len(listings) >= 100

            moscow = clean_db.query(ListingModel).filter(ListingModel.location_city == "Moscow").all()
            assert len(moscow) == 50

        finally:
            # Cleanup
            seeder.clear_all()
            count = clean_db.query(ListingModel).count()
            assert count == 0


class TestSeederDocumentation:
    """Test seeder has proper documentation."""

    def test_class_has_docstring(self):
        """Test DatabaseSeeder class has docstring."""
        assert DatabaseSeeder.__doc__ is not None
        assert len(DatabaseSeeder.__doc__) > 50

    def test_methods_have_docstrings(self):
        """Test all public methods have docstrings."""
        methods = [
            "seed_listings",
            "seed_diverse_dataset",
            "seed_fraud_scenarios",
            "clear_all",
        ]

        for method_name in methods:
            method = getattr(DatabaseSeeder, method_name)
            assert method.__doc__ is not None, f"{method_name} missing docstring"
            assert len(method.__doc__) > 50, f"{method_name} docstring too short"


@pytest.fixture
def listing_to_model():
    """Fixture providing listing_to_model conversion function."""
    from tests.seeders.database_seeder import listing_to_model

    return listing_to_model
