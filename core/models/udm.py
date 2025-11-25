from typing import Optional, List
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    lat: float
    lng: float


class SourceInfo(BaseModel):
    plugin_id: str
    platform: str
    original_id: Optional[str] = None
    url: Optional[str] = None


class Price(BaseModel):
    amount: float
    currency: str
    price_per_sqm: Optional[float] = None


class Location(BaseModel):
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    coordinates: Optional[Coordinates] = None


class MediaImage(BaseModel):
    url: str
    caption: Optional[str] = None


class Media(BaseModel):
    images: List[MediaImage] = []


class Listing(BaseModel):
    listing_id: str
    source: SourceInfo
    type: str  # sale | rent
    property_type: str  # apartment | house | commercial | land
    location: Location
    price: Price
    description: Optional[str] = None
    media: Optional[Media] = None
    fraud_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
