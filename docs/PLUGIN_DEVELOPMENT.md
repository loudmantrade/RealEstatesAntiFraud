# Plugin Development Guide

## Обзор

RealEstatesAntiFraud использует модульную архитектуру на основе плагинов. Это руководство описывает, как создавать и интегрировать плагины различных типов.

## Типы плагинов

1. **Source Plugins** - Источники данных (скрейперы, API коннекторы)
2. **Processing Plugins** - Обработка и обогащение данных
3. **Detection Plugins** - Детекция мошенничества
4. **Search Plugins** - Поиск и индексация
5. **Display Plugins** - Отображение и форматирование

## Структура плагина

### Базовая структура директории

```
plugin-{type}-{name}/
├── plugin.yaml              # Манифест плагина (обязательно)
├── __init__.py             # Python package
├── main.py                 # Главный класс плагина
├── config.yaml             # Конфигурация по умолчанию
├── requirements.txt        # Python зависимости
├── README.md               # Документация плагина
├── CHANGELOG.md            # История изменений
├── LICENSE                 # Лицензия
├── tests/                  # Тесты
│   ├── __init__.py
│   ├── test_main.py
│   └── fixtures/
├── assets/                 # Статические файлы (иконки, etc)
│   └── icon.png
└── examples/               # Примеры использования
    └── example_usage.py
```

### Манифест плагина (plugin.yaml)

```yaml
# Базовая информация
id: plugin-source-example
name: Example Source Plugin
version: 1.0.0
type: source  # source | processing | detection | search | display
api_version: 1.0

# Метаданные
description: |
  Detailed description of what the plugin does
author:
  name: Your Name
  email: your.email@example.com
  url: https://yourwebsite.com

# Лицензия
license: MIT
repository: https://github.com/username/plugin-source-example

# Зависимости
dependencies:
  core_version: ">=1.0.0"
  python_version: ">=3.10"
  plugins:
    - plugin-processing-normalizer: ">=1.0.0"
  
# Конфигурация
config:
  schema: config.yaml
  required_keys:
    - api_key
    - base_url
  
# Возможности
capabilities:
  - incremental_scraping
  - real_time_updates
  - batch_processing

# Ресурсы
resources:
  memory_mb: 512
  cpu_cores: 2
  disk_mb: 100

# Метрики
metrics:
  - name: listings_scraped
    type: counter
  - name: scraping_duration
    type: histogram
  - name: errors_count
    type: counter

# Хуки
hooks:
  on_install: scripts/install.sh
  on_enable: scripts/enable.sh
  on_disable: scripts/disable.sh
  on_uninstall: scripts/uninstall.sh

# Теги для поиска в маркетплейсе
tags:
  - real-estate
  - scraper
  - russia
  - api

# Changelog
changelog_url: https://github.com/username/plugin/blob/main/CHANGELOG.md
```

## 1. Source Plugin Development

### Интерфейс

```python
from abc import ABC, abstractmethod
from typing import Iterator, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ScrapingParams:
    """Parameters for scraping operation"""
    city: Optional[str] = None
    property_type: Optional[str] = None
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    since: Optional[datetime] = None
    limit: Optional[int] = None

class SourcePlugin(ABC):
    """Base class for all source plugins"""
    
    def __init__(self, config: Dict):
        """
        Initialize plugin with configuration
        
        Args:
            config: Plugin configuration dict
        """
        self.config = config
        self.enabled = False
        
    @abstractmethod
    def get_metadata(self) -> Dict:
        """
        Returns plugin metadata
        
        Returns:
            {
                'id': str,
                'name': str,
                'version': str,
                'type': str,
                'capabilities': List[str]
            }
        """
        pass
    
    @abstractmethod
    def configure(self, config: Dict) -> None:
        """
        Configure plugin with settings
        
        Args:
            config: Configuration dictionary
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate plugin configuration
        
        Returns:
            True if config is valid
        """
        pass
    
    @abstractmethod
    def scrape(self, params: ScrapingParams) -> Iterator[Dict]:
        """
        Main scraping method
        
        Args:
            params: Scraping parameters
            
        Yields:
            Listings in Unified Data Model format
        """
        pass
    
    @abstractmethod
    def scrape_single(self, listing_id: str) -> Optional[Dict]:
        """
        Scrape single listing by ID
        
        Args:
            listing_id: Listing identifier
            
        Returns:
            Listing in UDM format or None
        """
        pass
    
    @abstractmethod
    def validate_listing(self, listing: Dict) -> bool:
        """
        Validate listing data against UDM schema
        
        Args:
            listing: Listing data
            
        Returns:
            True if valid
        """
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict:
        """
        Return scraping statistics
        
        Returns:
            {
                'total_scraped': int,
                'success_count': int,
                'error_count': int,
                'last_scrape_time': datetime,
                'average_duration': float
            }
        """
        pass
    
    def on_error(self, error: Exception, context: Dict) -> None:
        """
        Error handler
        
        Args:
            error: Exception that occurred
            context: Context information
        """
        pass
    
    def health_check(self) -> bool:
        """
        Check if plugin is healthy
        
        Returns:
            True if healthy
        """
        return True
```

### Пример: HTML Scraper Plugin

```python
from typing import Iterator, Dict, Optional
import scrapy
from scrapy.crawler import CrawlerProcess
from .base import SourcePlugin, ScrapingParams

class ExampleScraperPlugin(SourcePlugin):
    """Example HTML scraper plugin"""
    
    def get_metadata(self) -> Dict:
        return {
            'id': 'plugin-source-example',
            'name': 'Example Scraper',
            'version': '1.0.0',
            'type': 'source',
            'capabilities': ['incremental_scraping', 'batch_processing']
        }
    
    def configure(self, config: Dict) -> None:
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')
        self.rate_limit = config.get('rate_limit', 10)
        
    def validate_config(self) -> bool:
        return bool(self.base_url and self.api_key)
    
    def scrape(self, params: ScrapingParams) -> Iterator[Dict]:
        """Main scraping logic"""
        
        # Build URL with params
        url = self._build_url(params)
        
        # Use Scrapy spider
        process = CrawlerProcess({
            'USER_AGENT': 'Mozilla/5.0...',
            'DOWNLOAD_DELAY': 1.0 / self.rate_limit,
        })
        
        listings = []
        
        class ListingSpider(scrapy.Spider):
            name = 'listings'
            start_urls = [url]
            
            def parse(self, response):
                for item in response.css('.listing-item'):
                    listing = self._extract_listing(item)
                    listings.append(listing)
                    
                # Pagination
                next_page = response.css('a.next-page::attr(href)').get()
                if next_page:
                    yield response.follow(next_page, self.parse)
        
        process.crawl(ListingSpider)
        process.start()
        
        for listing in listings:
            # Map to UDM format
            udm_listing = self._map_to_udm(listing)
            if self.validate_listing(udm_listing):
                yield udm_listing
    
    def _extract_listing(self, item) -> Dict:
        """Extract listing from HTML element"""
        return {
            'title': item.css('h2::text').get(),
            'price': item.css('.price::text').get(),
            'address': item.css('.address::text').get(),
            # ... more fields
        }
    
    def _map_to_udm(self, listing: Dict) -> Dict:
        """Map scraped data to Unified Data Model"""
        return {
            'listing_id': self._generate_id(),
            'source': {
                'plugin_id': 'plugin-source-example',
                'platform': 'example.com',
                'original_id': listing.get('id'),
                'url': listing.get('url')
            },
            'type': 'sale',
            'property_type': 'apartment',
            'location': {
                'address': listing.get('address'),
                # ... map other fields
            },
            'price': {
                'amount': self._parse_price(listing.get('price')),
                'currency': 'RUB'
            },
            # ... map all other fields according to UDM
        }
    
    def validate_listing(self, listing: Dict) -> bool:
        """Validate listing against UDM schema"""
        required_fields = ['listing_id', 'source', 'type', 'price']
        return all(listing.get(field) for field in required_fields)
    
    def scrape_single(self, listing_id: str) -> Optional[Dict]:
        """Scrape single listing"""
        # Implementation
        pass
    
    def get_statistics(self) -> Dict:
        return {
            'total_scraped': self.stats.get('scraped', 0),
            'success_count': self.stats.get('success', 0),
            'error_count': self.stats.get('errors', 0),
            'last_scrape_time': self.stats.get('last_time'),
            'average_duration': self.stats.get('avg_duration', 0.0)
        }
```

### Пример: API Connector Plugin

```python
import requests
from typing import Iterator, Dict, Optional
from .base import SourcePlugin, ScrapingParams

class APIConnectorPlugin(SourcePlugin):
    """Partner API connector plugin"""
    
    def configure(self, config: Dict) -> None:
        self.api_url = config.get('api_url')
        self.api_key = config.get('api_key')
        self.oauth_token = config.get('oauth_token')
        
    def scrape(self, params: ScrapingParams) -> Iterator[Dict]:
        """Fetch from API"""
        
        headers = {
            'Authorization': f'Bearer {self.oauth_token}',
            'X-API-Key': self.api_key
        }
        
        page = 1
        per_page = 100
        
        while True:
            response = requests.get(
                f'{self.api_url}/listings',
                headers=headers,
                params={
                    'page': page,
                    'per_page': per_page,
                    'city': params.city,
                    'type': params.property_type,
                    # ... other params
                }
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            listings = data.get('listings', [])
            
            if not listings:
                break
            
            for listing in listings:
                udm_listing = self._map_to_udm(listing)
                if self.validate_listing(udm_listing):
                    yield udm_listing
            
            page += 1
            
            # Check if there are more pages
            if page > data.get('total_pages', 1):
                break
```

## 2. Processing Plugin Development

### Интерфейс

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ProcessingPlugin(ABC):
    """Base class for processing plugins"""
    
    def __init__(self, config: Dict):
        self.config = config
        
    @abstractmethod
    def get_metadata(self) -> Dict:
        """Returns plugin metadata"""
        pass
    
    @abstractmethod
    def process(self, listing: Dict) -> Dict:
        """
        Process listing and return enriched data
        
        Args:
            listing: Listing in UDM format
            
        Returns:
            Enriched listing in UDM format
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """
        Return execution priority (lower = earlier)
        
        Returns:
            Priority value (0-100)
        """
        pass
    
    def validate_input(self, listing: Dict) -> bool:
        """Validate input data"""
        return True
    
    def validate_output(self, listing: Dict) -> bool:
        """Validate output data"""
        return True
```

### Пример: Geocoding Plugin

```python
import requests
from typing import Dict
from .base import ProcessingPlugin

class GeocodingPlugin(ProcessingPlugin):
    """Geocode addresses to coordinates"""
    
    def get_metadata(self) -> Dict:
        return {
            'id': 'plugin-processing-geocoder',
            'name': 'Geocoding Plugin',
            'version': '1.0.0',
            'type': 'processing'
        }
    
    def get_priority(self) -> int:
        return 3  # Execute after normalization
    
    def process(self, listing: Dict) -> Dict:
        """Add geocoding data"""
        
        location = listing.get('location', {})
        address = location.get('address')
        
        if not address:
            return listing
        
        # Skip if already has coordinates
        if location.get('coordinates'):
            return listing
        
        # Geocode using external service
        coords = self._geocode(address)
        
        if coords:
            listing['location']['coordinates'] = coords
            
            # Add enrichment data
            enrichment = self._get_location_enrichment(coords)
            listing['location']['enrichment'] = enrichment
        
        return listing
    
    def _geocode(self, address: str) -> Optional[Dict]:
        """Geocode address to coordinates"""
        provider = self.config.get('provider', 'yandex')
        
        if provider == 'yandex':
            return self._geocode_yandex(address)
        elif provider == 'google':
            return self._geocode_google(address)
        else:
            return None
    
    def _geocode_yandex(self, address: str) -> Optional[Dict]:
        api_key = self.config.get('yandex_api_key')
        
        response = requests.get(
            'https://geocode-maps.yandex.ru/1.x/',
            params={
                'apikey': api_key,
                'geocode': address,
                'format': 'json'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            point = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
            lng, lat = map(float, point.split())
            return {'lat': lat, 'lng': lng}
        
        return None
    
    def _get_location_enrichment(self, coords: Dict) -> Dict:
        """Get additional location data"""
        return {
            'nearest_metro': self._find_nearest_metro(coords),
            'district_info': self._get_district_info(coords),
            'nearby_pois': self._get_nearby_pois(coords)
        }
```

## 3. Detection Plugin Development

### Интерфейс

```python
from abc import ABC, abstractmethod
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class FraudSignal:
    """Single fraud signal"""
    type: str  # 'price_anomaly', 'fake_images', etc.
    severity: float  # 0.0 - 1.0
    description: str
    evidence: Dict

class DetectionPlugin(ABC):
    """Base class for fraud detection plugins"""
    
    @abstractmethod
    def get_metadata(self) -> Dict:
        """Returns plugin metadata"""
        pass
    
    @abstractmethod
    def analyze(self, listing: Dict) -> Dict:
        """
        Analyze listing for fraud signals
        
        Returns:
            {
                'signals': List[FraudSignal],
                'confidence': float,  # 0.0 - 1.0
                'details': Dict
            }
        """
        pass
    
    @abstractmethod
    def get_weight(self) -> float:
        """
        Return plugin weight in final score calculation
        
        Returns:
            Weight value (0.0 - 1.0)
        """
        pass
```

### Пример: Price Anomaly Detection Plugin

```python
import numpy as np
from typing import Dict, List
from .base import DetectionPlugin, FraudSignal

class PriceAnomalyPlugin(DetectionPlugin):
    """Detect abnormal prices"""
    
    def get_metadata(self) -> Dict:
        return {
            'id': 'plugin-detection-price-anomaly',
            'name': 'Price Anomaly Detector',
            'version': '1.0.0',
            'type': 'detection'
        }
    
    def get_weight(self) -> float:
        return 0.3  # 30% weight in final score
    
    def analyze(self, listing: Dict) -> Dict:
        """Analyze price for anomalies"""
        
        signals = []
        
        # Get listing details
        price = listing['price']['amount']
        area = listing['details'].get('area_total', 0)
        location = listing['location']
        property_type = listing['property_type']
        
        if area == 0:
            return {'signals': signals, 'confidence': 0.0, 'details': {}}
        
        price_per_sqm = price / area
        
        # Get market statistics for comparison
        market_stats = self._get_market_stats(location, property_type)
        
        if market_stats:
            mean_price = market_stats['mean_price_per_sqm']
            std_price = market_stats['std_price_per_sqm']
            
            # Calculate Z-score
            z_score = abs((price_per_sqm - mean_price) / std_price)
            
            # Too low price (potential scam)
            if price_per_sqm < mean_price - 2 * std_price:
                signals.append(FraudSignal(
                    type='suspiciously_low_price',
                    severity=min(z_score / 3, 1.0),
                    description=f'Price is {z_score:.1f} std deviations below market average',
                    evidence={
                        'price_per_sqm': price_per_sqm,
                        'market_mean': mean_price,
                        'z_score': z_score
                    }
                ))
            
            # Too high price (potential overpricing)
            elif price_per_sqm > mean_price + 3 * std_price:
                signals.append(FraudSignal(
                    type='suspiciously_high_price',
                    severity=min(z_score / 4, 1.0),
                    description=f'Price is {z_score:.1f} std deviations above market average',
                    evidence={
                        'price_per_sqm': price_per_sqm,
                        'market_mean': mean_price,
                        'z_score': z_score
                    }
                ))
        
        # Round numbers (999999 often used in scams)
        if self._is_suspicious_round_number(price):
            signals.append(FraudSignal(
                type='suspicious_round_price',
                severity=0.3,
                description='Price uses suspicious round number pattern',
                evidence={'price': price}
            ))
        
        # Calculate overall confidence
        if signals:
            confidence = sum(s.severity for s in signals) / len(signals)
        else:
            confidence = 0.0
        
        return {
            'signals': signals,
            'confidence': confidence,
            'details': {
                'price_per_sqm': price_per_sqm,
                'market_comparison': market_stats
            }
        }
    
    def _get_market_stats(self, location: Dict, property_type: str) -> Dict:
        """Get market statistics from database"""
        # Query database for similar listings
        # Return mean, std, percentiles, etc.
        pass
    
    def _is_suspicious_round_number(self, price: int) -> bool:
        """Check if price is suspiciously round"""
        # Check patterns like 999999, 1000000, etc.
        return price % 100000 == 99999 or price % 1000000 == 0
```

## 4. Plugin Installation & Registration

### Установка через CLI

```bash
# Install from local directory
realestate-cli plugin install ./plugin-source-example

# Install from Git repository
realestate-cli plugin install git+https://github.com/user/plugin-source-example.git

# Install from package registry
realestate-cli plugin install plugin-source-example

# Install specific version
realestate-cli plugin install plugin-source-example@1.2.0
```

### Регистрация через API

```python
import requests

# Upload plugin
with open('plugin-source-example.zip', 'rb') as f:
    response = requests.post(
        'http://api.example.com/api/plugins/upload',
        files={'file': f},
        headers={'Authorization': 'Bearer TOKEN'}
    )

plugin_id = response.json()['plugin_id']

# Configure plugin
requests.post(
    f'http://api.example.com/api/plugins/{plugin_id}/configure',
    json={
        'api_key': 'your-api-key',
        'base_url': 'https://example.com',
        'rate_limit': 10
    }
)

# Enable plugin
requests.put(
    f'http://api.example.com/api/plugins/{plugin_id}/enable'
)
```

## 5. Testing Plugins

### Unit Tests

```python
import pytest
from plugin_source_example import ExampleScraperPlugin

def test_plugin_metadata():
    plugin = ExampleScraperPlugin({})
    metadata = plugin.get_metadata()
    
    assert metadata['id'] == 'plugin-source-example'
    assert metadata['type'] == 'source'
    assert 'incremental_scraping' in metadata['capabilities']

def test_scraping():
    config = {
        'base_url': 'https://example.com',
        'api_key': 'test-key',
        'rate_limit': 10
    }
    
    plugin = ExampleScraperPlugin(config)
    plugin.configure(config)
    
    params = ScrapingParams(city='Moscow', property_type='apartment')
    listings = list(plugin.scrape(params))
    
    assert len(listings) > 0
    assert plugin.validate_listing(listings[0])

def test_udm_mapping():
    plugin = ExampleScraperPlugin({})
    
    raw_listing = {
        'id': '123',
        'title': 'Test Apartment',
        'price': '5000000 руб.',
        'address': 'Moscow, Test Street, 1'
    }
    
    udm_listing = plugin._map_to_udm(raw_listing)
    
    assert udm_listing['listing_id']
    assert udm_listing['source']['platform'] == 'example.com'
    assert udm_listing['price']['currency'] == 'RUB'
```

### Integration Tests

```python
def test_full_pipeline():
    # Install plugin
    from core.plugin_manager import PluginManager
    
    manager = PluginManager()
    plugin = manager.install('./plugin-source-example')
    
    # Configure
    plugin.configure({
        'api_key': 'test-key',
        'base_url': 'https://example.com'
    })
    
    # Scrape
    params = ScrapingParams(city='Moscow', limit=10)
    listings = list(plugin.scrape(params))
    
    # Verify UDM format
    for listing in listings:
        assert plugin.validate_listing(listing)
        assert 'listing_id' in listing
        assert 'source' in listing
```

## 6. Publishing to Marketplace

### Подготовка к публикации

1. **Документация**: README.md, примеры использования
2. **Тесты**: Покрытие >80%
3. **Лицензия**: Указать в LICENSE файле
4. **Changelog**: Вести историю изменений
5. **Иконка**: 256x256 PNG

### Публикация

```bash
# Build plugin package
realestate-cli plugin build ./plugin-source-example

# Validate package
realestate-cli plugin validate plugin-source-example-1.0.0.zip

# Publish to marketplace
realestate-cli plugin publish plugin-source-example-1.0.0.zip \
  --token YOUR_TOKEN \
  --category "Source Plugins" \
  --tags "scraper,russia,real-estate"
```

## 7. Best Practices

### Security
- ✅ Валидация всех входных данных
- ✅ Sandboxing для изоляции плагинов
- ✅ Ограничение доступа к ресурсам
- ✅ Безопасное хранение API ключей

### Performance
- ✅ Асинхронность где возможно
- ✅ Batch processing
- ✅ Кэширование результатов
- ✅ Rate limiting

### Error Handling
- ✅ Graceful degradation
- ✅ Retry механизмы
- ✅ Детальное логирование
- ✅ Health checks

### Documentation
- ✅ Подробный README
- ✅ API documentation
- ✅ Code examples
- ✅ Changelog

## 8. Plugin Lifecycle

```
[Development] → [Testing] → [Packaging] → [Publishing] → [Installation] 
     ↓              ↓            ↓             ↓              ↓
  [Local]      [Unit/Int]   [Validation]  [Marketplace]   [Registry]
                                                              ↓
                                         [Configuration] → [Enable] → [Running]
                                                              ↓
                                                          [Monitor]
                                                              ↓
                                                        [Update/Disable]
```

## Примеры готовых плагинов

См. директорию `/plugins` для примеров реализации:
- `plugins/sources/avito/`
- `plugins/sources/cian/`
- `plugins/processing/geocoder/`
- `plugins/detection/ml-classifier/`
- `plugins/search/elasticsearch/`

## Поддержка

- **Документация**: https://docs.realestatesantifraud.com
- **GitHub**: https://github.com/yourorg/RealEstatesAntiFraud
- **Discord**: https://discord.gg/realestate-antifraud
- **Email**: plugins@realestatesantifraud.com
