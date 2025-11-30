"""SQLAlchemy models for database tables."""

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import TypeDecorator

from core.database.base import Base


class JSONBType(TypeDecorator):
    """Portable JSONB type that falls back to JSON for non-PostgreSQL databases."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(JSON())


class ListingModel(Base):
    """SQLAlchemy model for listings table."""

    __tablename__ = "listings"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Core fields from UDM
    listing_id = Column(String(255), unique=True, nullable=False, index=True)

    # Source information
    source_plugin_id = Column(String(255), nullable=False, index=True)
    source_platform = Column(String(255), nullable=False)
    source_original_id = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)

    # Listing type and property type
    type = Column(String(50), nullable=False, index=True)  # sale | rent
    property_type = Column(String(50), nullable=False, index=True)  # apartment | house | commercial | land

    # Location
    location_country = Column(String(100), nullable=True)
    location_city = Column(String(255), nullable=True, index=True)
    location_address = Column(Text, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lng = Column(Float, nullable=True)

    # Price
    price_amount = Column(Numeric(precision=12, scale=2), nullable=False, index=True)
    price_currency = Column(String(10), nullable=False)
    price_per_sqm = Column(Numeric(precision=12, scale=2), nullable=True)

    # Description and media
    description = Column(Text, nullable=True)
    media = Column(JSONBType, nullable=True)  # Store media as JSONB/JSON

    # Fraud detection
    fraud_score = Column(Float, nullable=True, index=True)

    # Additional metadata stored as JSONB/JSON for flexibility
    extra_metadata = Column(JSONBType, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_location_city_type", "location_city", "type"),
        Index("idx_price_range", "price_amount"),
        Index("idx_fraud_score", "fraud_score"),
        Index(
            "idx_location_coordinates",
            "location_lat",
            "location_lng",
            postgresql_using="btree",
        ),
    )

    def __repr__(self):
        return f"<Listing(id={self.id}, listing_id={self.listing_id}, city={self.location_city})>"
