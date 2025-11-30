"""
Database Seeder for Bulk Test Data Generation

Provides efficient bulk data seeding for integration and performance testing.
Uses ListingFactory and batch inserts for optimal performance.

Usage:
    def test_with_seeded_data(db_session, listing_factory):
        seeder = DatabaseSeeder(db_session, listing_factory)
        seeder.seed_diverse_dataset()

        listings = db_session.query(ListingModel).all()
        assert len(listings) >= 100
        seeder.clear_all()

Performance:
    - Bulk inserts for efficiency
    - Progress logging for large datasets
    - Transaction management
"""

import logging
from typing import Dict, List

from sqlalchemy.orm import Session

from core.database.models import ListingModel
from core.models.udm import Listing
from tests.factories.listing_factory import ListingFactory

logger = logging.getLogger(__name__)


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
        location_lat=(
            listing.location.coordinates.lat if listing.location.coordinates else None
        ),
        location_lng=(
            listing.location.coordinates.lng if listing.location.coordinates else None
        ),
        price_amount=listing.price.amount,
        price_currency=listing.price.currency,
        price_per_sqm=listing.price.price_per_sqm,
        description=listing.description,
        media=listing.media.model_dump() if listing.media else None,
        fraud_score=listing.fraud_score,
    )


class DatabaseSeeder:
    """Database seeder for bulk test data generation.

    Provides methods for seeding various types of test data with efficient
    bulk inserts and progress tracking.

    Attributes:
        session: SQLAlchemy database session
        factory: ListingFactory for generating listings
        created_ids: List of created listing IDs for cleanup

    Example:
        >>> seeder = DatabaseSeeder(db_session, listing_factory)
        >>> seeder.seed_diverse_dataset()
        >>> count = db_session.query(ListingModel).count()
        >>> assert count >= 100
        >>> seeder.clear_all()
    """

    def __init__(self, session: Session, listing_factory: ListingFactory):
        """Initialize database seeder.

        Args:
            session: SQLAlchemy database session
            listing_factory: Factory for generating listings
        """
        self.session = session
        self.factory = listing_factory
        self.created_ids: List[str] = []

    def seed_listings(
        self,
        count: int = 100,
        batch_size: int = 50,
        log_progress: bool = True,
        **kwargs,
    ) -> List[ListingModel]:
        """Seed N listings to database with bulk insert.

        Args:
            count: Number of listings to create
            batch_size: Number of records per batch insert
            log_progress: Whether to log progress for large datasets
            **kwargs: Additional parameters passed to create_listing()

        Returns:
            List of created ListingModel instances

        Example:
            >>> models = seeder.seed_listings(count=1000, price_min=100_000)
            >>> assert len(models) == 1000
        """
        if log_progress and count > 100:
            logger.info(f"Seeding {count} listings in batches of {batch_size}")

        models = []
        for i in range(0, count, batch_size):
            batch_count = min(batch_size, count - i)
            batch_listings = [
                self.factory.create_listing(**kwargs) for _ in range(batch_count)
            ]
            batch_models = [listing_to_model(listing) for listing in batch_listings]

            self.session.bulk_save_objects(batch_models)
            self.session.flush()

            models.extend(batch_models)
            self.created_ids.extend([m.listing_id for m in batch_models])

            if log_progress and count > 100 and (i + batch_count) % 100 == 0:
                logger.info(f"Seeded {i + batch_count}/{count} listings")

        self.session.commit()

        if log_progress and count > 100:
            logger.info(f"Completed seeding {count} listings")

        return models

    def seed_diverse_dataset(self) -> Dict[str, List[ListingModel]]:
        """Seed diverse realistic dataset with different distributions.

        Creates a balanced dataset representing real-world distribution:
        - 50 Moscow apartments (Russian market)
        - 30 SPb apartments (Russian market)
        - 20 regional listings (various cities)
        - 10 fraud candidates (suspicious patterns)
        - 5 edge cases (unusual data)

        Returns:
            Dictionary mapping category to list of created models

        Example:
            >>> data = seeder.seed_diverse_dataset()
            >>> assert len(data["moscow"]) == 50
            >>> assert len(data["fraud"]) == 10
        """
        logger.info("Seeding diverse dataset")

        result = {}

        # Moscow apartments - main market
        logger.info("Seeding Moscow apartments (50)")
        result["moscow"] = self._seed_moscow_apartments(50)

        # SPb apartments - secondary market
        logger.info("Seeding SPb apartments (30)")
        result["spb"] = self._seed_spb_apartments(30)

        # Regional listings
        logger.info("Seeding regional listings (20)")
        result["regional"] = self._seed_regional_listings(20)

        # Fraud candidates
        logger.info("Seeding fraud candidates (10)")
        result["fraud"] = self._seed_fraud_candidates(10)

        # Edge cases
        logger.info("Seeding edge cases (5)")
        result["edge_cases"] = self._seed_edge_cases(5)

        total = sum(len(v) for v in result.values())
        logger.info(f"Completed seeding diverse dataset: {total} listings")

        return result

    def seed_fraud_scenarios(self) -> Dict[str, List[ListingModel]]:
        """Seed listings for fraud detection testing.

        Creates specific fraud patterns:
        - Price anomalies (too low/high)
        - Duplicate detection scenarios
        - Missing data patterns
        - Suspicious descriptions

        Returns:
            Dictionary mapping scenario to list of created models

        Example:
            >>> scenarios = seeder.seed_fraud_scenarios()
            >>> assert "price_anomaly" in scenarios
            >>> assert len(scenarios["price_anomaly"]) > 0
        """
        logger.info("Seeding fraud scenarios")

        result = {}

        # Price anomalies - unrealistically low prices
        logger.info("Seeding price anomalies (10)")
        result["price_anomaly"] = [
            listing_to_model(
                self.factory.create_listing(
                    price={"amount": 50_000 + i * 5_000, "currency": "RUB"},
                    fraud_score=0.8 + i * 0.02,
                )
            )
            for i in range(10)
        ]
        self.session.bulk_save_objects(result["price_anomaly"])
        self.created_ids.extend([m.listing_id for m in result["price_anomaly"]])

        # Near duplicates - same location, similar price
        logger.info("Seeding near duplicates (5)")
        base_listing = self.factory.create_listing()
        result["duplicates"] = [
            listing_to_model(
                self.factory.create_listing(
                    location={"city": base_listing.location.city},
                    price={
                        "amount": base_listing.price.amount + i * 1_000,
                        "currency": base_listing.price.currency,
                    },
                )
            )
            for i in range(5)
        ]
        self.session.bulk_save_objects(result["duplicates"])
        self.created_ids.extend([m.listing_id for m in result["duplicates"]])

        # Missing data - no description
        logger.info("Seeding missing data patterns (5)")
        result["missing_data"] = [
            listing_to_model(self.factory.create_listing(description=None))
            for _ in range(5)
        ]
        self.session.bulk_save_objects(result["missing_data"])
        self.created_ids.extend([m.listing_id for m in result["missing_data"]])

        self.session.commit()

        total = sum(len(v) for v in result.values())
        logger.info(f"Completed seeding fraud scenarios: {total} listings")

        return result

    def clear_all(self) -> int:
        """Clear all seeded data from database.

        Deletes all records created by this seeder instance.

        Returns:
            Number of records deleted

        Example:
            >>> seeder.seed_listings(100)
            >>> deleted = seeder.clear_all()
            >>> assert deleted == 100
        """
        if not self.created_ids:
            logger.info("No data to clear")
            return 0

        logger.info(f"Clearing {len(self.created_ids)} seeded listings")

        deleted = (
            self.session.query(ListingModel)
            .filter(ListingModel.listing_id.in_(self.created_ids))
            .delete(synchronize_session=False)
        )

        self.session.commit()
        self.created_ids.clear()

        logger.info(f"Cleared {deleted} listings")
        return deleted

    # Private helper methods

    def _seed_moscow_apartments(self, count: int) -> List[ListingModel]:
        """Seed Moscow apartment listings."""
        listings = [
            self.factory.create_listing(
                location={"city": "Moscow"},
                price={"amount": 5_000_000 + i * 100_000, "currency": "RUB"},
            )
            for i in range(count)
        ]
        models = [listing_to_model(listing) for listing in listings]
        self.session.bulk_save_objects(models)
        self.created_ids.extend([m.listing_id for m in models])
        return models

    def _seed_spb_apartments(self, count: int) -> List[ListingModel]:
        """Seed Saint Petersburg apartment listings."""
        listings = [
            self.factory.create_listing(
                location={"city": "Saint Petersburg"},
                price={"amount": 3_000_000 + i * 80_000, "currency": "RUB"},
            )
            for i in range(count)
        ]
        models = [listing_to_model(listing) for listing in listings]
        self.session.bulk_save_objects(models)
        self.created_ids.extend([m.listing_id for m in models])
        return models

    def _seed_regional_listings(self, count: int) -> List[ListingModel]:
        """Seed regional city listings."""
        cities = ["Kazan", "Novosibirsk", "Yekaterinburg", "Nizhny Novgorod"]
        listings = [
            self.factory.create_listing(
                location={"city": cities[i % len(cities)]},
                price={"amount": 2_000_000 + i * 50_000, "currency": "RUB"},
            )
            for i in range(count)
        ]
        models = [listing_to_model(listing) for listing in listings]
        self.session.bulk_save_objects(models)
        self.created_ids.extend([m.listing_id for m in models])
        return models

    def _seed_fraud_candidates(self, count: int) -> List[ListingModel]:
        """Seed fraud candidate listings."""
        listings = [
            self.factory.create_listing(
                price={"amount": 100_000 + i * 10_000, "currency": "RUB"},
                fraud_score=0.7 + i * 0.02,
            )
            for i in range(count)
        ]
        models = [listing_to_model(listing) for listing in listings]
        self.session.bulk_save_objects(models)
        self.created_ids.extend([m.listing_id for m in models])
        return models

    def _seed_edge_cases(self, count: int) -> List[ListingModel]:
        """Seed edge case listings."""
        listings = [
            self.factory.create_listing(
                price={"amount": 999_999_999, "currency": "RUB"},
                description="A" * 5000 if i == 0 else None,  # Very long or missing
            )
            for i in range(count)
        ]
        models = [listing_to_model(listing) for listing in listings]
        self.session.bulk_save_objects(models)
        self.created_ids.extend([m.listing_id for m in models])
        return models
