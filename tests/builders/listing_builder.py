"""
ListingBuilder for constructing Listing objects with fluent API.

This builder provides a convenient way to create complex Listing objects
for testing using method chaining and sensible defaults.

Example:
    >>> builder = ListingBuilder()
    >>> listing = (builder
    ...     .with_location('Москва', lat=55.7558, lng=37.6173)
    ...     .with_price(5_000_000, currency='RUB')
    ...     .with_property_type('apartment')
    ...     .build())
"""

import uuid
from typing import Dict, List, Optional

from faker import Faker

from core.models.udm import (
    Coordinates,
    Listing,
    Location,
    Media,
    MediaImage,
    Price,
    SourceInfo,
)


class ListingBuilder:
    """
    Builder for constructing Listing objects with fluent interface.

    Provides method chaining for easy construction of complex listings
    with sensible defaults. Useful for test scenarios requiring specific
    configurations.

    Example:
        >>> builder = ListingBuilder()
        >>> listing = (builder
        ...     .with_location('Москва')
        ...     .with_price(5_000_000)
        ...     .with_property_type('apartment')
        ...     .as_fraud_candidate()
        ...     .build())
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize ListingBuilder.

        Args:
            seed: Optional seed for reproducible test data
        """
        self.faker = Faker("ru_RU")
        if seed is not None:
            Faker.seed(seed)
            self.faker.seed_instance(seed)

        # Initialize with defaults
        self._reset()

    def _reset(self):
        """Reset builder to default state."""
        self._listing_id = self.faker.uuid4()
        self._source = {
            "plugin_id": "test_plugin",
            "platform": "test.ru",
            "original_id": self.faker.uuid4(),
            "url": f"https://test.ru/listing/{self._listing_id}",
        }
        self._type = "sale"
        self._property_type = "apartment"
        self._location = {
            "city": "Москва",
            "address": None,
            "coordinates": {"lat": 55.7558, "lng": 37.6173},
        }
        self._price = {
            "amount": 5_000_000.0,
            "currency": "RUB",
            "price_per_sqm": None,
        }
        self._area = None
        self._rooms = None
        self._description = None
        self._media = None
        self._fraud_score = None

    def with_listing_id(self, listing_id: str) -> "ListingBuilder":
        """
        Set listing ID.

        Args:
            listing_id: Listing identifier

        Returns:
            Self for method chaining
        """
        self._listing_id = listing_id
        return self

    def with_source(
        self,
        plugin_id: str,
        platform: str,
        original_id: Optional[str] = None,
        url: Optional[str] = None,
    ) -> "ListingBuilder":
        """
        Set source information.

        Args:
            plugin_id: Source plugin identifier
            platform: Platform name
            original_id: Original listing ID from platform
            url: Listing URL

        Returns:
            Self for method chaining
        """
        self._source = {
            "plugin_id": plugin_id,
            "platform": platform,
            "original_id": original_id or self.faker.uuid4(),
            "url": url or f"https://{platform}/listing/{self._listing_id}",
        }
        return self

    def with_location(
        self,
        city: str,
        address: Optional[str] = None,
        lat: Optional[float] = None,
        lng: Optional[float] = None,
    ) -> "ListingBuilder":
        """
        Set location information.

        Args:
            city: City name
            address: Full address
            lat: Latitude coordinate
            lng: Longitude coordinate

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_location('Москва', address='ул. Арбат, 1',
            ...                       lat=55.7558, lng=37.6173)
        """
        # Default coordinates for major cities
        default_coords = {
            "Москва": (55.7558, 37.6173),
            "Санкт-Петербург": (59.9311, 30.3609),
            "Екатеринбург": (56.8389, 60.6057),
            "Новосибирск": (55.0084, 82.9357),
            "Казань": (55.8304, 49.0661),
        }

        if lat is None or lng is None:
            default_lat, default_lng = default_coords.get(city, (55.7558, 37.6173))
            lat = lat or default_lat
            lng = lng or default_lng

        self._location = {
            "city": city,
            "address": address,
            "coordinates": {"lat": lat, "lng": lng},
        }
        return self

    def with_price(
        self,
        amount: float,
        currency: str = "RUB",
        price_per_sqm: Optional[float] = None,
    ) -> "ListingBuilder":
        """
        Set price information.

        Args:
            amount: Total price
            currency: Currency code (default: RUB)
            price_per_sqm: Price per square meter

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_price(5_000_000, currency='RUB')
        """
        self._price = {
            "amount": float(amount),
            "currency": currency,
            "price_per_sqm": price_per_sqm,
        }
        return self

    def with_property_type(self, property_type: str) -> "ListingBuilder":
        """
        Set property type.

        Args:
            property_type: Type (apartment/house/commercial/land)

        Returns:
            Self for method chaining
        """
        valid_types = ["apartment", "house", "commercial", "land"]
        if property_type not in valid_types:
            raise ValueError(
                f"Invalid property_type: {property_type}. "
                f"Must be one of {valid_types}"
            )
        self._property_type = property_type
        return self

    def with_listing_type(self, listing_type: str) -> "ListingBuilder":
        """
        Set listing type (sale/rent).

        Args:
            listing_type: Type (sale or rent)

        Returns:
            Self for method chaining
        """
        valid_types = ["sale", "rent"]
        if listing_type not in valid_types:
            raise ValueError(
                f"Invalid listing_type: {listing_type}. "
                f"Must be one of {valid_types}"
            )
        self._type = listing_type
        return self

    def with_area(self, area: float, rooms: Optional[int] = None) -> "ListingBuilder":
        """
        Set area and optionally rooms.

        Args:
            area: Area in square meters
            rooms: Number of rooms

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_area(85.5, rooms=3)
        """
        self._area = float(area)
        if rooms is not None:
            self._rooms = rooms

        # Calculate price_per_sqm if price is set and not already set
        if self._price["amount"] and self._price["price_per_sqm"] is None:
            self._price["price_per_sqm"] = self._price["amount"] / area

        return self

    def with_description(self, text: str) -> "ListingBuilder":
        """
        Set description text.

        Args:
            text: Description text

        Returns:
            Self for method chaining
        """
        self._description = text
        return self

    def with_media(self, images: List[Dict[str, str]]) -> "ListingBuilder":
        """
        Set media images.

        Args:
            images: List of image dicts with 'url' and optional 'caption'

        Returns:
            Self for method chaining

        Example:
            >>> builder.with_media([
            ...     {'url': 'https://example.com/1.jpg', 'caption': 'Вид'},
            ...     {'url': 'https://example.com/2.jpg'}
            ... ])
        """
        self._media = {"images": images}
        return self

    def with_fraud_score(self, score: float) -> "ListingBuilder":
        """
        Set fraud score.

        Args:
            score: Fraud score (0-100)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If score not in range [0, 100]
        """
        if not 0 <= score <= 100:
            raise ValueError(f"Fraud score must be 0-100, got {score}")
        self._fraud_score = score
        return self

    def with_fraud_indicators(self, indicators: List[str]) -> "ListingBuilder":
        """
        Set fraud indicators (for documentation/testing).

        Note: This doesn't affect the actual listing, just documents
        the fraud scenario being tested.

        Args:
            indicators: List of fraud indicator names

        Returns:
            Self for method chaining
        """
        # Store in description for test documentation
        if self._description:
            self._description += f"\n[Fraud indicators: {', '.join(indicators)}]"
        else:
            self._description = f"[Fraud indicators: {', '.join(indicators)}]"
        return self

    def as_fraud_candidate(
        self, fraud_type: str = "unrealistic_price"
    ) -> "ListingBuilder":
        """
        Apply fraud scenario preset.

        Args:
            fraud_type: Type of fraud scenario
                - unrealistic_price: Very low price
                - no_photos: No media images
                - fake_location: Suspicious coordinates
                - duplicate: Duplicate-like description

        Returns:
            Self for method chaining

        Example:
            >>> builder.as_fraud_candidate('unrealistic_price')
        """
        if fraud_type == "unrealistic_price":
            # Set price 80% below market
            self._price["amount"] = 1_000_000.0
            self._fraud_score = 85.0
            self.with_fraud_indicators(["unrealistic_price"])

        elif fraud_type == "no_photos":
            self._media = {"images": []}
            self._fraud_score = 70.0
            self.with_fraud_indicators(["no_photos"])

        elif fraud_type == "fake_location":
            # Set coordinates outside normal range
            self._location["coordinates"] = {
                "lat": 0.0,
                "lng": 0.0,
            }
            self._fraud_score = 75.0
            self.with_fraud_indicators(["fake_location"])

        elif fraud_type == "duplicate":
            self._description = (
                "Отличная квартира в центре города. "
                "Отличная квартира в центре города. "
                "Срочно продам."
            )
            self._fraud_score = 65.0
            self.with_fraud_indicators(["duplicate_description"])

        else:
            raise ValueError(
                f"Unknown fraud_type: {fraud_type}. "
                "Use: unrealistic_price, no_photos, "
                "fake_location, duplicate"
            )

        return self

    def as_edge_case(self, case_type: str) -> "ListingBuilder":
        """
        Apply edge case preset.

        Args:
            case_type: Type of edge case
                - minimal: Minimal required fields only
                - maximal: All fields populated
                - zero_price: Zero price
                - huge_price: Extremely high price
                - negative_area: Invalid negative area

        Returns:
            Self for method chaining

        Example:
            >>> builder.as_edge_case('minimal')
        """
        if case_type == "minimal":
            self._description = None
            self._media = None
            self._fraud_score = None
            self._area = None
            self._rooms = None
            self._location["district"] = None
            self._location["address"] = None

        elif case_type == "maximal":
            self._description = self.faker.text(max_nb_chars=500)
            self._media = {
                "images": [
                    {
                        "url": self.faker.image_url(),
                        "caption": self.faker.sentence(),
                    }
                    for _ in range(15)
                ]
            }
            self._fraud_score = 15.0
            self._area = 150.0
            self._rooms = 5
            self._location["address"] = self.faker.address()

        elif case_type == "zero_price":
            self._price["amount"] = 0.0
            self._fraud_score = 95.0

        elif case_type == "huge_price":
            self._price["amount"] = 1_000_000_000.0
            self._fraud_score = 80.0

        elif case_type == "negative_area":
            self._area = -50.0

        else:
            raise ValueError(
                f"Unknown case_type: {case_type}. "
                "Use: minimal, maximal, zero_price, "
                "huge_price, negative_area"
            )

        return self

    def build(self) -> Listing:
        """
        Build and return the Listing object.

        Returns:
            Constructed Listing instance

        Raises:
            ValueError: If required fields are invalid

        Example:
            >>> builder = ListingBuilder()
            >>> listing = builder.with_price(5_000_000).build()
        """
        # Build nested objects
        source = SourceInfo(**self._source)
        coordinates = Coordinates(**self._location["coordinates"])
        location = Location(
            city=self._location["city"],
            address=self._location["address"],
            coordinates=coordinates,
        )
        price = Price(**self._price)

        # Build media if present
        media = None
        if self._media is not None:
            media_images = [MediaImage(**img) for img in self._media["images"]]
            media = Media(images=media_images)

        # Create listing
        listing = Listing(
            listing_id=self._listing_id,
            source=source,
            type=self._type,
            property_type=self._property_type,
            location=location,
            price=price,
            description=self._description,
            media=media,
            fraud_score=self._fraud_score,
        )

        return listing

    def build_dict(self) -> Dict:
        """
        Build and return listing as dictionary.

        Useful for JSON serialization or API testing.

        Returns:
            Listing as dictionary

        Example:
            >>> builder = ListingBuilder()
            >>> data = builder.with_price(5_000_000).build_dict()
        """
        listing = self.build()
        return listing.model_dump(mode="json")
