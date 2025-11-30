"""Repository pattern for listings CRUD operations."""

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.database.models import ListingModel
from core.models.udm import Coordinates, Listing, Location, Media, MediaImage, Price, SourceInfo


def _model_to_udm(model: ListingModel) -> Listing:
    """Convert database model to UDM Listing.

    Args:
        model: ListingModel database instance

    Returns:
        Listing UDM instance
    """
    coordinates = None
    if model.location_lat is not None and model.location_lng is not None:
        coordinates = Coordinates(
            lat=model.location_lat,  # type: ignore[arg-type]
            lng=model.location_lng,  # type: ignore[arg-type]
        )

    location = Location(
        country=model.location_country,  # type: ignore[arg-type]
        city=model.location_city,  # type: ignore[arg-type]
        address=model.location_address,  # type: ignore[arg-type]
        coordinates=coordinates,
    )

    price = Price(
        amount=model.price_amount,  # type: ignore[arg-type]
        currency=model.price_currency,  # type: ignore[arg-type]
        price_per_sqm=model.price_per_sqm,  # type: ignore[arg-type]
    )

    source = SourceInfo(
        plugin_id=model.source_plugin_id,  # type: ignore[arg-type]
        platform=model.source_platform,  # type: ignore[arg-type]
        original_id=model.source_original_id,  # type: ignore[arg-type]
        url=model.source_url,  # type: ignore[arg-type]
    )

    media = None
    if model.media:
        images = [MediaImage(url=img["url"], caption=img.get("caption")) for img in model.media.get("images", [])]
        media = Media(images=images)

    return Listing(
        listing_id=model.listing_id,  # type: ignore[arg-type]
        source=source,
        type=model.type,  # type: ignore[arg-type]
        property_type=model.property_type,  # type: ignore[arg-type]
        location=location,
        price=price,
        description=model.description,  # type: ignore[arg-type]
        media=media,
        fraud_score=model.fraud_score,  # type: ignore[arg-type]
    )


class ListingRepository:
    """Repository for managing listings in the database."""

    def __init__(self, db: Session):
        """Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def create(self, listing: Listing) -> Listing:
        """Create a new listing in the database.

        Args:
            listing: Listing UDM model

        Returns:
            Created Listing UDM instance
        """
        # Convert media to dict if present
        media_dict = None
        if listing.media:
            media_dict = {"images": [{"url": img.url, "caption": img.caption} for img in listing.media.images]}

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
            location_lat=(listing.location.coordinates.lat if listing.location.coordinates else None),
            location_lng=(listing.location.coordinates.lng if listing.location.coordinates else None),
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

        return _model_to_udm(db_listing)

    def get_by_id(self, listing_id: str) -> Optional[Listing]:
        """Get listing by listing_id.

        Args:
            listing_id: Unique listing identifier

        Returns:
            Listing UDM instance or None if not found
        """
        model = self.db.query(ListingModel).filter(ListingModel.listing_id == listing_id).first()
        return _model_to_udm(model) if model else None

    def get_by_db_id(self, id: int) -> Optional[Listing]:
        """Get listing by database id.

        Args:
            id: Database primary key

        Returns:
            Listing UDM instance or None if not found
        """
        model = self.db.query(ListingModel).filter(ListingModel.id == id).first()
        return _model_to_udm(model) if model else None

    def get_all(self, skip: int = 0, limit: int = 100, city: Optional[str] = None) -> List[Listing]:
        """Get all listings with pagination and optional filtering.

        Args:
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            city: Optional city filter

        Returns:
            List of Listing UDM instances
        """
        query = self.db.query(ListingModel)

        if city:
            query = query.filter(ListingModel.location_city == city)

        models = query.offset(skip).limit(limit).all()
        return [_model_to_udm(model) for model in models]

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

    def count_by_fraud_score_range(self, min_score: float, max_score: float) -> int:
        """Count listings filtered by fraud score range.

        Args:
            min_score: Minimum fraud score (inclusive)
            max_score: Maximum fraud score (inclusive)

        Returns:
            Total count of listings in range
        """
        return (
            self.db.query(func.count(ListingModel.id))
            .filter(
                ListingModel.fraud_score >= min_score,
                ListingModel.fraud_score <= max_score,
            )
            .scalar()
        )

    def count_by_price_range(
        self,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        city: Optional[str] = None,
    ) -> int:
        """Count listings filtered by price range.

        Args:
            min_price: Minimum price (inclusive), None for no lower limit
            max_price: Maximum price (inclusive), None for no upper limit
            city: Optional city filter

        Returns:
            Total count of listings in range
        """
        query = self.db.query(func.count(ListingModel.id))

        if min_price is not None:
            query = query.filter(ListingModel.price_amount >= min_price)
        if max_price is not None:
            query = query.filter(ListingModel.price_amount <= max_price)
        if city:
            query = query.filter(ListingModel.location_city == city)

        return query.scalar()

    def update(self, listing_id: str, **kwargs) -> Optional[Listing]:
        """Update listing by listing_id.

        Args:
            listing_id: Unique listing identifier
            **kwargs: Fields to update

        Returns:
            Updated Listing UDM instance or None if not found
        """
        model = self.db.query(ListingModel).filter(ListingModel.listing_id == listing_id).first()
        if not model:
            return None

        for key, value in kwargs.items():
            if hasattr(model, key):
                setattr(model, key, value)

        self.db.commit()
        self.db.refresh(model)

        return _model_to_udm(model)

    def delete(self, listing_id: str) -> bool:
        """Delete listing by listing_id.

        Args:
            listing_id: Unique listing identifier

        Returns:
            True if deleted, False if not found
        """
        model = self.db.query(ListingModel).filter(ListingModel.listing_id == listing_id).first()
        if not model:
            return False

        self.db.delete(model)
        self.db.commit()

        return True

    def get_by_fraud_score_range(
        self, min_score: float, max_score: float, skip: int = 0, limit: int = 100
    ) -> List[Listing]:
        """Get listings filtered by fraud score range.

        Args:
            min_score: Minimum fraud score (inclusive)
            max_score: Maximum fraud score (inclusive)
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return

        Returns:
            List of Listing UDM instances
        """
        models = (
            self.db.query(ListingModel)
            .filter(
                ListingModel.fraud_score >= min_score,
                ListingModel.fraud_score <= max_score,
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_model_to_udm(model) for model in models]

    def get_by_price_range(
        self,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        skip: int = 0,
        limit: int = 100,
        city: Optional[str] = None,
    ) -> List[Listing]:
        """Get listings filtered by price range.

        Args:
            min_price: Minimum price (inclusive), None for no lower limit
            max_price: Maximum price (inclusive), None for no upper limit
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            city: Optional city filter

        Returns:
            List of Listing UDM instances
        """
        query = self.db.query(ListingModel)

        if min_price is not None:
            query = query.filter(ListingModel.price_amount >= min_price)
        if max_price is not None:
            query = query.filter(ListingModel.price_amount <= max_price)

        if city:
            query = query.filter(ListingModel.location_city == city)

        models = query.offset(skip).limit(limit).all()
        return [_model_to_udm(model) for model in models]
