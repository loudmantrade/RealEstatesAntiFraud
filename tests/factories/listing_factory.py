"""
ListingFactory for generating realistic test Listing objects.

This factory uses Faker with Russian locale to generate realistic
real estate listings for testing purposes.
"""

import random
from typing import Any, Dict, List, Optional

from faker import Faker

from core.models.udm import (
    Coordinates,
    Listing,
    Location,
    Media,
    Price,
    SourceInfo,
)


class ListingFactory:
    """
    Factory for creating test Listing instances with realistic Russian data.

    Examples:
        >>> factory = ListingFactory()
        >>> listing = factory.create_listing()
        >>> listings = factory.create_batch(10)
        >>> moscow_apts = factory.create_moscow_apartments(5)
    """

    # Moscow districts with realistic price ranges (RUB per sqm)
    MOSCOW_DISTRICTS = {
        "Центральный": {"min_price": 300_000, "max_price": 500_000},
        "Арбат": {"min_price": 250_000, "max_price": 400_000},
        "Хамовники": {"min_price": 280_000, "max_price": 450_000},
        "Тверской": {"min_price": 270_000, "max_price": 420_000},
        "Таганский": {"min_price": 220_000, "max_price": 350_000},
        "Замоскворечье": {"min_price": 200_000, "max_price": 320_000},
        "Выхино-Жулебино": {"min_price": 150_000, "max_price": 220_000},
        "Бутово Южное": {"min_price": 120_000, "max_price": 180_000},
        "Бутово Северное": {"min_price": 130_000, "max_price": 190_000},
        "Марьино": {"min_price": 160_000, "max_price": 240_000},
    }

    # Major Russian cities
    RUSSIAN_CITIES = [
        "Москва",
        "Санкт-Петербург",
        "Екатеринбург",
        "Новосибирск",
        "Казань",
        "Нижний Новгород",
        "Челябинск",
        "Самара",
        "Омск",
        "Ростов-на-Дону",
    ]

    # Property types
    PROPERTY_TYPES = ["apartment", "house", "commercial", "land"]

    # Listing types
    LISTING_TYPES = ["sale", "rent"]

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the ListingFactory.

        Args:
            seed: Optional seed for reproducible random data
        """
        self.faker = Faker("ru_RU")
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            self.faker.seed_instance(seed)

    def create_listing(
        self,
        listing_id: Optional[str] = None,
        source: Optional[Dict[str, Any]] = None,
        listing_type: Optional[str] = None,
        property_type: Optional[str] = None,
        location: Optional[Dict[str, Any]] = None,
        price: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        media: Optional[Dict[str, Any]] = None,
        fraud_score: Optional[float] = None,
        **kwargs,
    ) -> Listing:
        """
        Create a single Listing with realistic Russian real estate data.

        Args:
            listing_id: Unique listing identifier (auto-generated)
            source: Source information dict
            listing_type: 'sale' or 'rent'
            property_type: 'apartment', 'house', 'commercial', or 'land'
            location: Location dict with city, address, coordinates
            price: Price dict with amount, currency, price_per_sqm
            description: Property description
            media: Media dict with images
            fraud_score: Fraud detection score (0-100)
            **kwargs: Additional fields for model overrides

        Returns:
            Listing instance with realistic data

        Examples:
            >>> factory = ListingFactory()
            >>> # Default listing
            >>> listing = factory.create_listing()
            >>>
            >>> # Custom price and location
            >>> listing = factory.create_listing(
            ...     price={'amount': 5_000_000, 'currency': 'RUB'},
            ...     location={'city': 'Москва'}
            ... )
        """
        # Generate listing_id
        if listing_id is None:
            listing_id = self.faker.uuid4()

        # Generate source
        if source is None:
            source = self._generate_source()

        # Generate listing_type
        if listing_type is None:
            listing_type = random.choice(self.LISTING_TYPES)

        # Generate property_type
        if property_type is None:
            property_type = random.choice(self.PROPERTY_TYPES)

        # Generate location
        if location is None:
            location = self._generate_location()

        # Generate price based on property type
        if price is None:
            price = self._generate_price(property_type, listing_type, location)

        # Generate description
        if description is None:
            description = self._generate_description(property_type, location)

        # Generate media
        if media is None:
            media = self._generate_media()

        # Build Listing object
        return Listing(
            listing_id=listing_id,
            source=SourceInfo(**source),
            type=listing_type,
            property_type=property_type,
            location=Location(**location),
            price=Price(**price),
            description=description,
            media=Media(**media) if media else None,
            fraud_score=fraud_score,
            **kwargs,
        )

    def create_batch(self, count: int, **kwargs) -> List[Listing]:
        """
        Create multiple listings at once.

        Args:
            count: Number of listings to create
            **kwargs: Common parameters to apply to all listings

        Returns:
            List of Listing instances

        Example:
            >>> factory = ListingFactory()
            >>> listings = factory.create_batch(10, property_type='apartment')
        """
        return [self.create_listing(**kwargs) for _ in range(count)]

    def create_moscow_apartments(
        self, count: int = 1, district: Optional[str] = None
    ) -> List[Listing]:
        """
        Create Moscow apartment listings with realistic district prices.

        Args:
            count: Number of apartments to create
            district: Specific Moscow district (random if not provided)

        Returns:
            List of Moscow apartment Listing instances

        Example:
            >>> factory = ListingFactory()
            >>> apts = factory.create_moscow_apartments(
            ...     5, district='Центральный'
            ... )
        """
        listings = []
        for _ in range(count):
            # Choose district
            selected_district = district or random.choice(
                list(self.MOSCOW_DISTRICTS.keys())
            )
            district_data = self.MOSCOW_DISTRICTS[selected_district]

            # Generate area (typical Moscow apartment: 30-150 sqm)
            area = random.uniform(30, 150)

            # Calculate price based on district
            price_per_sqm = random.uniform(
                district_data["min_price"], district_data["max_price"]
            )
            total_price = area * price_per_sqm

            # Generate Moscow location
            location = {
                "country": "Россия",
                "city": "Москва",
                "address": (
                    f"{selected_district}, {self.faker.street_address()}"
                ),
                "coordinates": {
                    "lat": random.uniform(55.55, 55.88),  # Moscow lat
                    "lng": random.uniform(37.37, 37.84),  # Moscow lng
                },
            }

            # Generate price
            price = {
                "amount": round(total_price, 2),
                "currency": "RUB",
                "price_per_sqm": round(price_per_sqm, 2),
            }

            listing = self.create_listing(
                listing_type="sale",
                property_type="apartment",
                location=location,
                price=price,
            )
            listings.append(listing)

        return listings

    def create_suspicious_listings(self, count: int = 1) -> List[Listing]:
        """
        Create listings with fraud indicators for testing fraud detection.

        Args:
            count: Number of suspicious listings to create

        Returns:
            List of Listing instances with high fraud scores

        Example:
            >>> factory = ListingFactory()
            >>> suspicious = factory.create_suspicious_listings(3)
        """
        fraud_scenarios = [
            self._create_unrealistic_price_listing,
            self._create_no_photos_listing,
            self._create_fake_location_listing,
            self._create_duplicate_description_listing,
        ]

        listings = []
        for _ in range(count):
            scenario = random.choice(fraud_scenarios)
            listing = scenario()
            listings.append(listing)

        return listings

    def create_edge_cases(self) -> List[Listing]:
        """
        Create listings with edge case data for testing validation.

        Returns:
            List of Listing instances with edge case values

        Example:
            >>> factory = ListingFactory()
            >>> edge_cases = factory.create_edge_cases()
        """
        return [
            self._create_minimal_listing(),
            self._create_maximal_listing(),
            self._create_zero_price_listing(),
        ]

    # Private helper methods

    def _generate_source(self) -> Dict[str, Any]:
        """Generate realistic source information."""
        platforms = ["cian.ru", "avito.ru", "domofond.ru", "yandex.ru/realty"]
        platform = random.choice(platforms)

        return {
            "plugin_id": f"{platform.split('.')[0]}_plugin",
            "platform": platform,
            "original_id": self.faker.uuid4(),
            "url": f"https://{platform}/listing/{self.faker.uuid4()}",
        }

    def _generate_location(self) -> Dict[str, Any]:
        """Generate realistic Russian location."""
        city = random.choice(self.RUSSIAN_CITIES)

        # Moscow has more specific coordinates
        if city == "Москва":
            lat = random.uniform(55.55, 55.88)
            lng = random.uniform(37.37, 37.84)
        elif city == "Санкт-Петербург":
            lat = random.uniform(59.80, 60.05)
            lng = random.uniform(30.15, 30.50)
        else:
            # Generic Russian coordinates
            lat = random.uniform(55.0, 60.0)
            lng = random.uniform(30.0, 40.0)

        return {
            "country": "Россия",
            "city": city,
            "address": self.faker.street_address(),
            "coordinates": {"lat": lat, "lng": lng},
        }

    def _generate_price(
        self, property_type: str, listing_type: str, location: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate realistic price based on property type and location."""
        city = location.get("city", "Москва")

        # Base prices by property type and city (for sale)
        if property_type == "apartment":
            if city == "Москва":
                base_price = random.uniform(5_000_000, 20_000_000)
            elif city == "Санкт-Петербург":
                base_price = random.uniform(4_000_000, 15_000_000)
            else:
                base_price = random.uniform(2_000_000, 8_000_000)
        elif property_type == "house":
            if city in ["Москва", "Санкт-Петербург"]:
                base_price = random.uniform(10_000_000, 50_000_000)
            else:
                base_price = random.uniform(5_000_000, 25_000_000)
        elif property_type == "commercial":
            base_price = random.uniform(10_000_000, 100_000_000)
        else:  # land
            base_price = random.uniform(1_000_000, 10_000_000)

        # Adjust for rent (monthly price)
        if listing_type == "rent":
            base_price = base_price * 0.005  # ~0.5% of sale price per month

        return {
            "amount": round(base_price, 2),
            "currency": "RUB",
            "price_per_sqm": (
                round(base_price / random.uniform(50, 150), 2)
                if property_type in ["apartment", "house"]
                else None
            ),
        }

    def _generate_description(
        self, property_type: str, location: Dict[str, Any]
    ) -> str:
        """Generate realistic property description in Russian."""
        city = location.get("city", "Москва")

        s1 = self.faker.sentence()
        s2 = self.faker.sentence()
        templates = [
            f"Продается {property_type} в {city}. {s1} {s2}",
            f"Отличная {property_type} в центре {city}. {s1}",
            f"{property_type.capitalize()} в {city}, {s1} {s2}",
        ]

        return random.choice(templates)

    def _generate_media(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate media with random number of images."""
        num_images = random.randint(1, 10)
        images = []

        for i in range(num_images):
            caption = f"Фото {i+1}" if random.random() > 0.5 else None
            images.append(
                {
                    "url": self.faker.image_url(width=1024, height=768),
                    "caption": caption,
                }
            )

        return {"images": images}

    # Fraud scenario generators

    def _create_unrealistic_price_listing(self) -> Listing:
        """Create listing with unrealistically low price (80% below market)."""
        listing = self.create_listing(property_type="apartment")
        # Set price to 20% of normal
        listing.price.amount = listing.price.amount * 0.2
        listing.fraud_score = random.uniform(70, 95)
        return listing

    def _create_no_photos_listing(self) -> Listing:
        """Create listing without any photos."""
        return self.create_listing(
            media={"images": []}, fraud_score=random.uniform(50, 70)
        )

    def _create_fake_location_listing(self) -> Listing:
        """Create listing with mismatched coordinates."""
        listing = self.create_listing(property_type="apartment")
        # Set coordinates far from claimed city
        listing.location.coordinates = Coordinates(lat=0.0, lng=0.0)
        listing.fraud_score = random.uniform(60, 85)
        return listing

    def _create_duplicate_description_listing(self) -> Listing:
        """Create listing with generic/duplicated description."""
        generic_desc = "Продается квартира. Хорошее состояние. Звоните."
        return self.create_listing(
            description=generic_desc, fraud_score=random.uniform(40, 60)
        )

    # Edge case generators

    def _create_minimal_listing(self) -> Listing:
        """Create listing with minimal required fields only."""
        # Provide empty values to override defaults
        return Listing(
            listing_id=self.faker.uuid4(),
            source=SourceInfo(**self._generate_source()),
            type=random.choice(self.LISTING_TYPES),
            property_type=random.choice(self.PROPERTY_TYPES),
            location=Location(**self._generate_location()),
            price=Price(
                **self._generate_price("apartment", "sale", {"city": "Москва"})
            ),
            description=None,
            media=None,
            fraud_score=None,
        )

    def _create_maximal_listing(self) -> Listing:
        """Create listing with all fields populated."""
        return self.create_listing(
            description=self.faker.text(max_nb_chars=500),
            media={
                "images": [
                    {
                        "url": self.faker.image_url(),
                        "caption": self.faker.sentence(),
                    }
                    for _ in range(15)
                ]
            },
            fraud_score=random.uniform(0, 100),
        )

    def _create_zero_price_listing(self) -> Listing:
        """Create listing with zero price (invalid but possible edge case)."""
        return self.create_listing(
            price={"amount": 0.0, "currency": "RUB", "price_per_sqm": 0.0},
            fraud_score=random.uniform(80, 100),
        )
