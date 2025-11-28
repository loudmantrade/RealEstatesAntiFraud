"""Repository pattern for listings CRUD operations."""

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database.models import ListingModel
from core.models.udm import Listing


class ListingRepository:
    """Repository for managing listings in the database."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(self, listing: Listing) -> ListingModel:
        """Create a new listing in the database.

        Args:
            listing: Listing UDM model

        Returns:
            Created ListingModel instance
        """
        # Convert media to dict if present
        media_dict = None
        if listing.media:
            media_dict = {
                "images": [
                    {"url": img.url, "caption": img.caption}
                    for img in listing.media.images
                ]
            }

        db_listing = ListingModel(
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
                listing.location.coordinates.lat
                if listing.location.coordinates
                else None
            ),
            location_lng=(
                listing.location.coordinates.lng
                if listing.location.coordinates
                else None
            ),
            price_amount=listing.price.amount,
            price_currency=listing.price.currency,
            price_per_sqm=listing.price.price_per_sqm,
            description=listing.description,
            media=media_dict,
            fraud_score=listing.fraud_score,
        )

        self.db.add(db_listing)
        self.db.commit()
        self.db.refresh(db_listing)

        return db_listing

    def get_by_id(self, listing_id: str) -> Optional[ListingModel]:
        """Get listing by listing_id.

        Args:
            listing_id: Unique listing identifier

        Returns:
            ListingModel instance or None if not found
        """
        return (
            self.db.query(ListingModel)
            .filter(ListingModel.listing_id == listing_id)
            .first()
        )

    def get_by_db_id(self, id: int) -> Optional[ListingModel]:
        """Get listing by database id.

        Args:
            id: Database primary key

        Returns:
            ListingModel instance or None if not found
        """
        return self.db.query(ListingModel).filter(ListingModel.id == id).first()

    def get_all(
        self, skip: int = 0, limit: int = 100, city: Optional[str] = None
    ) -> List[ListingModel]:
        """Get all listings with pagination and optional filtering.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            city: Optional city filter

        Returns:
            List of ListingModel instances
        """
        query = self.db.query(ListingModel)

        if city:
            query = query.filter(ListingModel.location_city == city)

        return query.offset(skip).limit(limit).all()

    def count(self, city: Optional[str] = None) -> int:
        """Count total listings with optional filtering.

        Args:
            city: Optional city filter

        Returns:
            Total count of listings
        """
        query = self.db.query(func.count(ListingModel.id))

        if city:
            query = query.filter(ListingModel.location_city == city)

        return query.scalar()

    def update(self, listing_id: str, **kwargs) -> Optional[ListingModel]:
        """Update listing by listing_id.

        Args:
            listing_id: Unique listing identifier
            **kwargs: Fields to update

        Returns:
            Updated ListingModel instance or None if not found
        """
        db_listing = self.get_by_id(listing_id)
        if not db_listing:
            return None

        for key, value in kwargs.items():
            if hasattr(db_listing, key):
                setattr(db_listing, key, value)

        self.db.commit()
        self.db.refresh(db_listing)

        return db_listing

    def delete(self, listing_id: str) -> bool:
        """Delete listing by listing_id.

        Args:
            listing_id: Unique listing identifier

        Returns:
            True if deleted, False if not found
        """
        db_listing = self.get_by_id(listing_id)
        if not db_listing:
            return False

        self.db.delete(db_listing)
        self.db.commit()

        return True

    def get_by_fraud_score_range(
        self, min_score: float, max_score: float, skip: int = 0, limit: int = 100
    ) -> List[ListingModel]:
        """Get listings filtered by fraud score range.

        Args:
            min_score: Minimum fraud score (inclusive)
            max_score: Maximum fraud score (inclusive)
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return

        Returns:
            List of ListingModel instances
        """
        return (
            self.db.query(ListingModel)
            .filter(
                ListingModel.fraud_score >= min_score,
                ListingModel.fraud_score <= max_score,
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_price_range(
        self,
        min_price: float,
        max_price: float,
        skip: int = 0,
        limit: int = 100,
        city: Optional[str] = None,
    ) -> List[ListingModel]:
        """Get listings filtered by price range.

        Args:
            min_price: Minimum price (inclusive)
            max_price: Maximum price (inclusive)
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            city: Optional city filter

        Returns:
            List of ListingModel instances
        """
        query = self.db.query(ListingModel).filter(
            ListingModel.price_amount >= min_price,
            ListingModel.price_amount <= max_price,
        )

        if city:
            query = query.filter(ListingModel.location_city == city)

        return query.offset(skip).limit(limit).all()
