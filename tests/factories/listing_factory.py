"""
ListingFactory for generating realistic test Listing objects.

This factory uses Faker with Portuguese locale to generate realistic
real estate listings for testing purposes, targeting Portugal 🇵🇹 and Ukraine 🇺🇦 markets.
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
    Factory for creating test Listing instances targeting Portugal and Ukraine markets.

    Examples:
        >>> factory = ListingFactory()
        >>> listing = factory.create_listing()
        >>> listings = factory.create_batch(10)
        >>> lisboa_apts = factory.create_lisboa_apartments(5)
        >>> kyiv_apts = factory.create_kyiv_apartments(3)
    """

    # Lisboa districts with realistic price ranges (EUR per sqm)
    LISBOA_DISTRICTS = {
        "Baixa": {"min_price": 6_000, "max_price": 8_000, "coords": (38.7115, -9.1366)},
        "Chiado": {
            "min_price": 6_500,
            "max_price": 8_000,
            "coords": (38.7107, -9.1423),
        },
        "Alfama": {
            "min_price": 5_000,
            "max_price": 7_000,
            "coords": (38.7138, -9.1297),
        },
        "Belém": {"min_price": 4_500, "max_price": 6_500, "coords": (38.6976, -9.2068)},
        "Parque das Nações": {
            "min_price": 4_000,
            "max_price": 5_500,
            "coords": (38.7681, -9.0947),
        },
        "Alvalade": {
            "min_price": 3_500,
            "max_price": 5_000,
            "coords": (38.7573, -9.1476),
        },
        "Campo de Ourique": {
            "min_price": 4_500,
            "max_price": 6_000,
            "coords": (38.7197, -9.1678),
        },
        "Estrela": {
            "min_price": 5_000,
            "max_price": 7_000,
            "coords": (38.7144, -9.1615),
        },
    }

    # Porto districts with realistic price ranges (EUR per sqm)
    PORTO_DISTRICTS = {
        "Ribeira": {
            "min_price": 4_000,
            "max_price": 5_000,
            "coords": (41.1406, -8.6143),
        },
        "Boavista": {
            "min_price": 3_000,
            "max_price": 4_000,
            "coords": (41.1585, -8.6454),
        },
        "Foz do Douro": {
            "min_price": 3_500,
            "max_price": 4_500,
            "coords": (41.1522, -8.6754),
        },
        "Cedofeita": {
            "min_price": 2_800,
            "max_price": 3_800,
            "coords": (41.1533, -8.6227),
        },
        "Massarelos": {
            "min_price": 3_200,
            "max_price": 4_200,
            "coords": (41.1494, -8.6494),
        },
    }

    # Kyiv districts with realistic price ranges (EUR per sqm)
    KYIV_DISTRICTS = {
        "Печерськ": {
            "min_price": 2_500,
            "max_price": 3_500,
            "coords": (50.4268, 30.5383),
        },
        "Шевченківський": {
            "min_price": 2_000,
            "max_price": 3_000,
            "coords": (50.4547, 30.4870),
        },
        "Подільський": {
            "min_price": 1_500,
            "max_price": 2_500,
            "coords": (50.4699, 30.5153),
        },
        "Оболонський": {
            "min_price": 1_200,
            "max_price": 2_000,
            "coords": (50.5173, 30.4984),
        },
        "Дарницький": {
            "min_price": 1_000,
            "max_price": 1_800,
            "coords": (50.4119, 30.6361),
        },
    }

    # Lviv districts with realistic price ranges (EUR per sqm)
    LVIV_DISTRICTS = {
        "Центр": {"min_price": 1_500, "max_price": 2_000, "coords": (49.8397, 24.0297)},
        "Франківський": {
            "min_price": 1_200,
            "max_price": 1_800,
            "coords": (49.8175, 24.0078),
        },
        "Личаківський": {
            "min_price": 1_000,
            "max_price": 1_500,
            "coords": (49.8258, 24.0536),
        },
    }

    # Portuguese cities with coordinates
    PORTUGUESE_CITIES = {
        "Lisboa": (38.7223, -9.1393),
        "Porto": (41.1579, -8.6291),
        "Faro": (37.0194, -7.9322),
        "Coimbra": (40.2033, -8.4103),
        "Braga": (41.5454, -8.4265),
    }

    # Ukrainian cities with coordinates
    UKRAINIAN_CITIES = {
        "Київ": (50.4501, 30.5234),
        "Львів": (49.8397, 24.0297),
        "Одеса": (46.4825, 30.7233),
        "Харків": (49.9935, 36.2304),
        "Дніпро": (48.4647, 35.0462),
    }

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
        self.faker = Faker("pt_PT")  # Portuguese locale for primary market
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

    def create_lisboa_apartments(self, count: int = 1, district: Optional[str] = None) -> List[Listing]:
        """
        Create Lisboa apartment listings with realistic district prices.

        Args:
            count: Number of apartments to create
            district: Specific Lisboa district (random if not provided)

        Returns:
            List of Lisboa apartment Listing instances

        Example:
            >>> factory = ListingFactory()
            >>> apts = factory.create_lisboa_apartments(5, district='Baixa')
        """
        listings = []
        for _ in range(count):
            # Choose district
            selected_district = district or random.choice(list(self.LISBOA_DISTRICTS.keys()))
            district_data = self.LISBOA_DISTRICTS[selected_district]

            # Generate area (typical Lisboa apartment: 40-120 sqm)
            area = random.uniform(40, 120)

            # Calculate price based on district
            price_per_sqm = random.uniform(district_data["min_price"], district_data["max_price"])
            total_price = area * price_per_sqm

            # Generate Lisboa location with district coordinates
            base_lat, base_lng = district_data["coords"]
            location = {
                "country": "Portugal",
                "city": "Lisboa",
                "address": f"{selected_district}, {self.faker.street_address()}",
                "coordinates": {
                    "lat": base_lat + random.uniform(-0.01, 0.01),
                    "lng": base_lng + random.uniform(-0.01, 0.01),
                },
            }

            # Generate price
            price = {
                "amount": round(total_price, 2),
                "currency": "EUR",
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

    def create_porto_apartments(self, count: int = 1, district: Optional[str] = None) -> List[Listing]:
        """
        Create Porto apartment listings with realistic district prices.

        Args:
            count: Number of apartments to create
            district: Specific Porto district (random if not provided)

        Returns:
            List of Porto apartment Listing instances

        Example:
            >>> factory = ListingFactory()
            >>> apts = factory.create_porto_apartments(3, district='Ribeira')
        """
        listings = []
        for _ in range(count):
            # Choose district
            selected_district = district or random.choice(list(self.PORTO_DISTRICTS.keys()))
            district_data = self.PORTO_DISTRICTS[selected_district]

            # Generate area (typical Porto apartment: 35-110 sqm)
            area = random.uniform(35, 110)

            # Calculate price based on district
            price_per_sqm = random.uniform(district_data["min_price"], district_data["max_price"])
            total_price = area * price_per_sqm

            # Generate Porto location with district coordinates
            base_lat, base_lng = district_data["coords"]
            location = {
                "country": "Portugal",
                "city": "Porto",
                "address": f"{selected_district}, {self.faker.street_address()}",
                "coordinates": {
                    "lat": base_lat + random.uniform(-0.01, 0.01),
                    "lng": base_lng + random.uniform(-0.01, 0.01),
                },
            }

            # Generate price
            price = {
                "amount": round(total_price, 2),
                "currency": "EUR",
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

    def create_kyiv_apartments(self, count: int = 1, district: Optional[str] = None) -> List[Listing]:
        """
        Create Kyiv apartment listings with realistic district prices.

        Args:
            count: Number of apartments to create
            district: Specific Kyiv district (random if not provided)

        Returns:
            List of Kyiv apartment Listing instances

        Example:
            >>> factory = ListingFactory()
            >>> apts = factory.create_kyiv_apartments(3, district='Печерськ')
        """
        listings = []
        for _ in range(count):
            # Choose district
            selected_district = district or random.choice(list(self.KYIV_DISTRICTS.keys()))
            district_data = self.KYIV_DISTRICTS[selected_district]

            # Generate area (typical Kyiv apartment: 40-130 sqm)
            area = random.uniform(40, 130)

            # Calculate price based on district
            price_per_sqm = random.uniform(district_data["min_price"], district_data["max_price"])
            total_price = area * price_per_sqm

            # Generate Kyiv location with district coordinates
            base_lat, base_lng = district_data["coords"]
            location = {
                "country": "Ukraine",
                "city": "Київ",
                "address": f"{selected_district}, вул. {self.faker.street_name()}",
                "coordinates": {
                    "lat": base_lat + random.uniform(-0.01, 0.01),
                    "lng": base_lng + random.uniform(-0.01, 0.01),
                },
            }

            # Generate price
            price = {
                "amount": round(total_price, 2),
                "currency": "EUR",
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

    def create_lviv_apartments(self, count: int = 1, district: Optional[str] = None) -> List[Listing]:
        """
        Create Lviv apartment listings with realistic district prices.

        Args:
            count: Number of apartments to create
            district: Specific Lviv district (random if not provided)

        Returns:
            List of Lviv apartment Listing instances

        Example:
            >>> factory = ListingFactory()
            >>> apts = factory.create_lviv_apartments(2, district='Центр')
        """
        listings = []
        for _ in range(count):
            # Choose district
            selected_district = district or random.choice(list(self.LVIV_DISTRICTS.keys()))
            district_data = self.LVIV_DISTRICTS[selected_district]

            # Generate area (typical Lviv apartment: 35-100 sqm)
            area = random.uniform(35, 100)

            # Calculate price based on district
            price_per_sqm = random.uniform(district_data["min_price"], district_data["max_price"])
            total_price = area * price_per_sqm

            # Generate Lviv location with district coordinates
            base_lat, base_lng = district_data["coords"]
            location = {
                "country": "Ukraine",
                "city": "Львів",
                "address": f"{selected_district}, вул. {self.faker.street_name()}",
                "coordinates": {
                    "lat": base_lat + random.uniform(-0.01, 0.01),
                    "lng": base_lng + random.uniform(-0.01, 0.01),
                },
            }

            # Generate price
            price = {
                "amount": round(total_price, 2),
                "currency": "EUR",
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

    def create_regional_listings(self, city: str, count: int = 5) -> List[Listing]:
        """
        Generate listings for specific Portuguese or Ukrainian cities.

        Args:
            city: City name (Portuguese or Ukrainian)
            count: Number of listings to create

        Returns:
            List of Listing instances for the specified city

        Example:
            >>> factory = ListingFactory()
            >>> faro_listings = factory.create_regional_listings('Faro', 5)
            >>> odesa_listings = factory.create_regional_listings('Одеса', 3)
        """
        if city in self.PORTUGUESE_CITIES:
            country = "Portugal"
            coords = self.PORTUGUESE_CITIES[city]
        elif city in self.UKRAINIAN_CITIES:
            country = "Ukraine"
            coords = self.UKRAINIAN_CITIES[city]
        else:
            raise ValueError(
                f"City '{city}' not supported. Use one of: "
                f"{list(self.PORTUGUESE_CITIES.keys())} or "
                f"{list(self.UKRAINIAN_CITIES.keys())}"
            )

        listings = []
        for _ in range(count):
            area = random.uniform(40, 120)

            # Regional price adjustments (lower than Lisboa/Kyiv)
            if country == "Portugal":
                price_per_sqm = random.uniform(2_000, 4_000)
            else:  # Ukraine
                price_per_sqm = random.uniform(1_000, 2_000)

            total_price = area * price_per_sqm

            location = {
                "country": country,
                "city": city,
                "address": self.faker.street_address(),
                "coordinates": {
                    "lat": coords[0] + random.uniform(-0.02, 0.02),
                    "lng": coords[1] + random.uniform(-0.02, 0.02),
                },
            }

            price = {
                "amount": round(total_price, 2),
                "currency": "EUR",
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

    def create_fraud_candidates(self, count: int = 3, fraud_type: Optional[str] = None) -> List[Listing]:
        """
        Generate listings with specific fraud indicators for testing fraud detection.

        Args:
            count: Number of fraud listings to create
            fraud_type: Specific fraud type or random if None
                       Options: 'unrealistic_price', 'duplicate_photos',
                               'fake_location', 'missing_contact', 'too_good_to_be_true'

        Returns:
            List of Listing instances with fraud indicators

        Example:
            >>> factory = ListingFactory()
            >>> fraud = factory.create_fraud_candidates(3, 'unrealistic_price')
            >>> mixed_fraud = factory.create_fraud_candidates(5)
        """
        fraud_scenarios = {
            "unrealistic_price": self._create_unrealistic_price_listing,
            "duplicate_photos": self._create_no_photos_listing,
            "fake_location": self._create_fake_location_listing,
            "missing_contact": self._create_duplicate_description_listing,
            "too_good_to_be_true": self._create_too_good_listing,
        }

        if fraud_type and fraud_type not in fraud_scenarios:
            raise ValueError(f"Invalid fraud_type: {fraud_type}. " f"Options: {list(fraud_scenarios.keys())}")

        listings = []
        for _ in range(count):
            if fraud_type:
                scenario = fraud_scenarios[fraud_type]
            else:
                scenario = random.choice(list(fraud_scenarios.values()))

            listing = scenario()
            listings.append(listing)

        return listings

    def create_suspicious_listings(self, count: int = 1) -> List[Listing]:
        """
        Create listings with fraud indicators for testing fraud detection.

        Deprecated: Use create_fraud_candidates() instead for better control.

        Args:
            count: Number of suspicious listings to create

        Returns:
            List of Listing instances with high fraud scores

        Example:
            >>> factory = ListingFactory()
            >>> suspicious = factory.create_suspicious_listings(3)
        """
        return self.create_fraud_candidates(count)

    def create_edge_cases(self, count: int = 5) -> List[Listing]:
        """
        Generate listings with edge case data for testing validation.

        Args:
            count: Number of edge case listings to create

        Returns:
            List of Listing instances with edge case values

        Example:
            >>> factory = ListingFactory()
            >>> edge_cases = factory.create_edge_cases(5)
        """
        edge_case_generators = [
            self._create_minimal_listing,
            self._create_maximal_listing,
            self._create_zero_price_listing,
            self._create_negative_price_listing,
            self._create_invalid_coordinates_listing,
            self._create_empty_description_listing,
            self._create_oversized_area_listing,
        ]

        listings = []
        for i in range(count):
            # Cycle through generators if count > number of generators
            generator = edge_case_generators[i % len(edge_case_generators)]
            listing = generator()
            listings.append(listing)

        return listings

    # Private helper methods

    def _generate_source(self) -> Dict[str, Any]:
        """Generate realistic source information for Portugal/Ukraine markets."""
        platforms = [
            "idealista.pt",
            "imovirtual.com",
            "olx.pt",
            "olx.ua",
            "dom.ria.com",
            "lun.ua",
        ]
        platform = random.choice(platforms)

        return {
            "plugin_id": f"{platform.split('.')[0]}_plugin",
            "platform": platform,
            "original_id": self.faker.uuid4(),
            "url": f"https://{platform}/listing/{self.faker.uuid4()}",
        }

    def _generate_location(self) -> Dict[str, Any]:
        """Generate realistic Portugal/Ukraine location."""
        # Randomly choose between Portugal and Ukraine
        if random.random() < 0.6:  # 60% Portugal (priority market)
            country = "Portugal"
            city, coords = random.choice(list(self.PORTUGUESE_CITIES.items()))
        else:  # 40% Ukraine
            country = "Ukraine"
            city, coords = random.choice(list(self.UKRAINIAN_CITIES.items()))

        lat, lng = coords
        # Add small random offset to coordinates
        lat += random.uniform(-0.02, 0.02)
        lng += random.uniform(-0.02, 0.02)

        return {
            "country": country,
            "city": city,
            "address": self.faker.street_address(),
            "coordinates": {"lat": lat, "lng": lng},
        }

    def _generate_price(self, property_type: str, listing_type: str, location: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic price based on property type and location."""
        city = location.get("city", "Lisboa")
        country = location.get("country", "Portugal")

        # Base prices by property type and city (for sale in EUR)
        if property_type == "apartment":
            if city == "Lisboa":
                base_price = random.uniform(200_000, 600_000)
            elif city == "Porto":
                base_price = random.uniform(150_000, 400_000)
            elif city == "Київ":
                base_price = random.uniform(80_000, 250_000)
            elif city == "Львів":
                base_price = random.uniform(60_000, 150_000)
            elif country == "Portugal":
                base_price = random.uniform(100_000, 300_000)
            else:  # Other Ukrainian cities
                base_price = random.uniform(50_000, 150_000)
        elif property_type == "house":
            if country == "Portugal":
                base_price = random.uniform(300_000, 1_000_000)
            else:  # Ukraine
                base_price = random.uniform(150_000, 500_000)
        elif property_type == "commercial":
            if country == "Portugal":
                base_price = random.uniform(500_000, 3_000_000)
            else:  # Ukraine
                base_price = random.uniform(200_000, 1_000_000)
        else:  # land
            if country == "Portugal":
                base_price = random.uniform(50_000, 500_000)
            else:  # Ukraine
                base_price = random.uniform(20_000, 200_000)

        # Adjust for rent (monthly price)
        if listing_type == "rent":
            base_price = base_price * 0.005  # ~0.5% of sale price per month

        return {
            "amount": round(base_price, 2),
            "currency": "EUR",
            "price_per_sqm": (
                round(base_price / random.uniform(50, 150), 2) if property_type in ["apartment", "house"] else None
            ),
        }

    def _generate_description(self, property_type: str, location: Dict[str, Any]) -> str:
        """Generate realistic property description for Portugal/Ukraine markets."""
        city = location.get("city", "Lisboa")
        country = location.get("country", "Portugal")

        s1 = self.faker.sentence()
        s2 = self.faker.sentence()

        if country == "Portugal":
            templates = [
                f"Vende-se {property_type} em {city}. {s1} {s2}",
                f"Excelente {property_type} no centro de {city}. {s1}",
                f"{property_type.capitalize()} em {city}, {s1} {s2}",
            ]
        else:  # Ukraine
            templates = [
                f"Продається {property_type} у {city}. {s1} {s2}",
                f"Чудова {property_type} в центрі {city}. {s1}",
                f"{property_type.capitalize()} у {city}, {s1} {s2}",
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
        return self.create_listing(media={"images": []}, fraud_score=random.uniform(50, 70))

    def _create_fake_location_listing(self) -> Listing:
        """Create listing with mismatched coordinates."""
        listing = self.create_listing(property_type="apartment")
        # Set coordinates far from claimed city
        listing.location.coordinates = Coordinates(lat=0.0, lng=0.0)
        listing.fraud_score = random.uniform(60, 85)
        return listing

    def _create_duplicate_description_listing(self) -> Listing:
        """Create listing with generic/duplicated description."""
        generic_desc = "Excelente apartamento. Ótimo estado. Contacte-nos."
        return self.create_listing(description=generic_desc, fraud_score=random.uniform(40, 60))

    def _create_too_good_listing(self) -> Listing:
        """Create listing with 'too good to be true' description."""
        too_good_desc = "URGENT! Very cheap! Perfect condition! Must sell today!"
        listing = self.create_listing(property_type="apartment", description=too_good_desc)
        # Make price suspiciously low
        listing.price.amount = listing.price.amount * 0.3
        listing.fraud_score = random.uniform(75, 95)
        return listing

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
            price=Price(**self._generate_price("apartment", "sale", {"city": "Lisboa", "country": "Portugal"})),
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
            price={"amount": 0.0, "currency": "EUR", "price_per_sqm": 0.0},
            fraud_score=random.uniform(80, 100),
        )

    def _create_negative_price_listing(self) -> Listing:
        """Create listing with negative price (invalid edge case)."""
        return self.create_listing(
            price={"amount": -150_000.0, "currency": "EUR", "price_per_sqm": -2_500.0},
            fraud_score=random.uniform(90, 100),
        )

    def _create_invalid_coordinates_listing(self) -> Listing:
        """Create listing with coordinates outside Portugal/Ukraine."""
        listing = self.create_listing(property_type="apartment")
        # Set coordinates to invalid location (middle of ocean)
        listing.location.coordinates = Coordinates(lat=0.0, lng=0.0)
        listing.fraud_score = random.uniform(70, 90)
        return listing

    def _create_empty_description_listing(self) -> Listing:
        """Create listing with empty description."""
        return self.create_listing(
            description="",
            fraud_score=random.uniform(40, 60),
        )

    def _create_oversized_area_listing(self) -> Listing:
        """Create listing with unrealistically large area for apartment."""
        listing = self.create_listing(property_type="apartment")
        # Set area to 5000 sqm (unrealistic for apartment)
        area = 5_000.0
        listing.price.price_per_sqm = listing.price.amount / area
        listing.fraud_score = random.uniform(60, 80)
        return listing
