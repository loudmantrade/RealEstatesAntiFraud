# Plugin Development Guide

## Обзор

RealEstatesAntiFraud использует модульную архитектуру на основе плагинов. Это руководство описывает, как создавать и интегрировать плагины различных типов.

> 📘 **Формальная спецификация**: См. [PLUGIN_SPEC.md](PLUGIN_SPEC.md) для полной спецификации манифеста плагина v1.0 с JSON Schema и примерами валидации.

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
    plugin-processing-normalizer: "^2.0.0"  # Caret: allows 2.x.x (not 3.0.0)
    plugin-detection-ml: "~1.5.0"           # Tilde: allows 1.5.x (not 1.6.0)
    plugin-source-base: ">=1.0.0 <2.0.0"    # Range: between 1.0.0 and 2.0.0
    plugin-utils-common: "*"                 # Any version
  
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

## Plugin Discovery and Loading

### Overview

The core system automatically discovers and loads plugins from the `plugins/` directory using a filesystem-based discovery mechanism. This enables hot-drop functionality where new plugins can be added without restarting the application.

### Discovery Process

1. **Recursive Scanning**: The `PluginManager.discover_plugins()` method recursively scans the `plugins/` directory for `plugin.yaml` files
2. **Manifest Validation**: Each discovered manifest is validated against the JSON Schema specification
3. **Error Handling**: Invalid manifests are logged but don't stop discovery of other plugins

**Example:**
```python
from pathlib import Path
from core.plugin_manager import PluginManager

manager = PluginManager()
manifests = manager.discover_plugins(Path("plugins"))
print(f"Discovered {len(manifests)} valid plugins")
```

### Loading Process

The `PluginManager.load_plugins()` method performs the following steps for each discovered plugin:

1. **Validate Manifest**: Uses `validate_manifest()` from validators module
2. **Register Metadata**: Creates `PluginMetadata` and registers with manager
3. **Dynamic Import**: Imports Python module specified in `entrypoint.module`
4. **Instantiate Class**: Creates instance of class specified in `entrypoint.class`
5. **Error Recovery**: Failed plugins are logged and skipped, allowing others to load

**Loading from directory:**
```python
loaded, failed = manager.load_plugins(plugins_dir=Path("plugins"))
print(f"Loaded: {len(loaded)}, Failed: {len(failed)}")
```

**Loading specific manifests:**
```python
manifests = [
    Path("plugins/cian-source/plugin.yaml"),
    Path("plugins/fraud-detector/plugin.yaml"),
]
loaded, failed = manager.load_plugins(manifest_paths=manifests)
```

### Hot-Drop Support

Plugins can be added to the `plugins/` directory while the system is running:

1. **Copy Plugin**: Add plugin directory with `plugin.yaml` to `plugins/`
2. **Trigger Discovery**: Call `discover_plugins()` again to find new plugin
3. **Load Plugin**: Call `load_plugins()` to instantiate the new plugin

**Example hot-drop:**
```python
# Initial load
manager.load_plugins(plugins_dir=Path("plugins"))

# ... later, after adding new plugin directory ...

# Discover new plugins
new_manifests = manager.discover_plugins(Path("plugins"))
manager.load_plugins(manifest_paths=new_manifests)
```

### Plugin Directory Structure

```
plugins/
├── cian-source/
│   ├── plugin.yaml          # Required: manifest file
│   ├── cian_scraper.py      # Plugin implementation
│   ├── __init__.py          # Optional: package marker
│   └── requirements.txt     # Optional: plugin dependencies
│
├── avito-source/
│   ├── plugin.yaml
│   └── avito_scraper.py
│
└── fraud-detector/
    ├── plugin.yaml
    ├── detector.py
    └── models/
        └── fraud_model.pkl
```

### Entrypoint Configuration

The manifest `entrypoint` field specifies how to load the plugin:

```yaml
entrypoint:
  module: cian_scraper      # Python module name (without .py)
  class: CianSourcePlugin   # Plugin class name
```

**Requirements:**
- Module must be importable from plugin directory
- Class must implement appropriate plugin interface (SourcePlugin, ProcessingPlugin, etc.)
- Class must implement all required abstract methods from base interface

### Error Handling

The plugin loading system handles various error scenarios gracefully:

| Error Type | Behavior | Logged |
|------------|----------|--------|
| Invalid manifest | Plugin skipped | ✓ ERROR |
| Missing entrypoint | Plugin registered, not instantiated | ✓ WARNING |
| Import error | Plugin failed, removed from registry | ✓ ERROR |
| Instantiation error | Plugin failed, removed from registry | ✓ ERROR |
| Missing abstract methods | Plugin failed, removed from registry | ✓ ERROR |

**Checking for errors:**
```python
loaded, failed = manager.load_plugins(plugins_dir=Path("plugins"))

for manifest_path, exception in failed:
    print(f"Failed to load {manifest_path}: {exception}")
```

### Logging

Plugin discovery and loading emit detailed logs at various levels:

- **DEBUG**: Module imports, class lookups, detailed operation steps
- **INFO**: Successful discovery, registration, instantiation
- **WARNING**: Missing entrypoints, skipped operations
- **ERROR**: Validation failures, import errors, instantiation failures

**Configure logging:**
```python
import logging

# Enable detailed plugin loading logs
logging.getLogger('core.plugin_manager').setLevel(logging.DEBUG)
```

### Troubleshooting

#### Plugin Not Discovered

**Symptom**: Plugin directory exists but not found by discovery

**Solutions:**
- Ensure `plugin.yaml` file exists in plugin directory
- Verify manifest passes JSON Schema validation
- Check file permissions (readable by application)
- Look for ERROR logs indicating validation failures

#### Module Import Error

**Symptom**: `ModuleNotFoundError` or `ImportError` during loading

**Solutions:**
- Verify `entrypoint.module` matches Python file name (without `.py`)
- Ensure plugin directory is properly structured
- Check that `core` package is in sys.path for interface imports
- Install any plugin-specific dependencies

#### Class Not Found

**Symptom**: `AttributeError: module has no attribute 'ClassName'`

**Solutions:**
- Verify `entrypoint.class` matches actual class name (case-sensitive)
- Ensure class is defined at module level (not nested)
- Check for syntax errors in plugin Python file

#### Abstract Methods Error

**Symptom**: `TypeError: Can't instantiate abstract class...`

**Solutions:**
- Implement all required abstract methods from base interface
- Check interface documentation for required methods
- Ensure method signatures match interface definition

#### Plugin Loads But Doesn't Work

**Symptom**: Plugin instantiates but fails during operation

**Solutions:**
- Check plugin implementation for bugs
- Verify `validate_config()` method accepts configuration
- Review plugin-specific logs for runtime errors
- Test plugin in isolation before deployment

### Best Practices

1. **Validate Early**: Test plugin manifest with `validate_manifest()` before deployment
2. **Handle Dependencies**: Include `requirements.txt` for plugin-specific dependencies
3. **Implement Fully**: Ensure all abstract methods are implemented before testing
4. **Log Appropriately**: Use Python logging module for plugin-specific logs
5. **Test Isolation**: Test plugins independently before adding to plugins/ directory
6. **Version Carefully**: Use semantic versioning in manifest `version` field
7. **Document Configuration**: Provide clear documentation for plugin configuration options

### Example Complete Plugin

**plugin.yaml:**
```yaml
id: plugin-source-cian
name: Cian.ru Source Plugin
version: 1.0.0
type: source
api_version: "1.0"
description: Scrapes real estate listings from Cian.ru

author:
  name: Development Team
  email: dev@example.com

entrypoint:
  module: cian_scraper
  class: CianSourcePlugin

capabilities:
  - incremental_scraping
  - real_time_updates

dependencies:
  python_version: ">=3.10"
  core_version: ">=1.0.0"
```

**cian_scraper.py:**
```python
"""Cian.ru source plugin implementation."""
import logging
from typing import Dict, List, Optional
from core.interfaces.source_plugin import SourcePlugin
from core.models.udm import UnifiedListing

logger = logging.getLogger(__name__)


class CianSourcePlugin(SourcePlugin):
    """Source plugin for scraping Cian.ru."""
    
    def __init__(self):
        """Initialize plugin."""
        self.initialized = True
        logger.info("CianSourcePlugin initialized")
    
    def configure(self, config: Dict) -> None:
        """Configure plugin with settings."""
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://cian.ru")
        logger.info(f"Configured with base_url: {self.base_url}")
    
    def validate_listing(self, listing: Dict) -> bool:
        """Validate scraped listing data."""
        required_fields = ["id", "title", "price"]
        return all(field in listing for field in required_fields)
    
    def scrape(self, params: Optional[Dict] = None) -> List[UnifiedListing]:
        """Scrape multiple listings."""
        # Implementation here
        logger.info("Scraping listings from Cian.ru")
        return []
    
    def scrape_single(self, listing_id: str) -> Optional[UnifiedListing]:
        """Scrape single listing by ID."""
        # Implementation here
        logger.info(f"Scraping listing {listing_id}")
        return None
    
    def get_metadata(self) -> Dict:
        """Return plugin metadata."""
        return {
            "source": "cian.ru",
            "version": "1.0.0",
            "supported_cities": ["moscow", "saint_petersburg"]
        }
    
    def get_statistics(self) -> Dict:
        """Return scraping statistics."""
        return {
            "total_scraped": 0,
            "last_scrape": None,
            "errors": 0
        }
```

This plugin is now ready to be placed in `plugins/cian-source/` and will be automatically discovered and loaded by the system.

## Version Constraints and Dependency Management

### Overview

The plugin system uses semantic versioning (semver) to manage plugin dependencies. This ensures that plugins only load when their dependencies are available in compatible versions, preventing runtime errors and version conflicts.

### Semantic Versioning Format

Versions follow the semver format: `MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]`

**Examples:**
- `1.0.0` - Release version
- `2.1.5` - Release with patches
- `1.0.0-alpha.1` - Pre-release version
- `1.0.0+build.123` - Version with build metadata
- `2.0.0-beta.2+sha.5114f85` - Pre-release with build metadata

**Version Comparison Rules:**
- `1.0.0 < 1.0.1` (patch increment)
- `1.0.0 < 1.1.0` (minor increment)
- `1.0.0 < 2.0.0` (major increment)
- `1.0.0-alpha < 1.0.0` (pre-release is lower)
- `1.0.0+build.1 == 1.0.0+build.2` (build metadata ignored)

### Constraint Formats

The system supports multiple constraint formats for specifying version requirements:

#### 1. Exact Version
```yaml
dependencies:
  plugins:
    plugin-a: "1.2.3"  # Only version 1.2.3
```

#### 2. Caret Constraint (^)
Allows patch and minor updates, but not major version changes.

```yaml
dependencies:
  plugins:
    plugin-a: "^1.2.3"  # Allows: 1.2.3, 1.2.4, 1.9.9
                         # Blocks: 2.0.0, 0.9.9
```

**Rules:**
- `^1.2.3` → `>=1.2.3 <2.0.0`
- `^0.2.3` → `>=0.2.3 <1.0.0`
- `^0.0.3` → `>=0.0.3 <0.1.0`

**Use Case**: Typical dependency where you trust minor updates won't break compatibility.

#### 3. Tilde Constraint (~)
Allows only patch updates.

```yaml
dependencies:
  plugins:
    plugin-a: "~1.2.3"  # Allows: 1.2.3, 1.2.4, 1.2.99
                         # Blocks: 1.3.0, 2.0.0
```

**Rules:**
- `~1.2.3` → `>=1.2.3 <1.3.0`
- `~1.2` → `>=1.2.0 <1.3.0`
- `~1` → `>=1.0.0 <2.0.0`

**Use Case**: Conservative dependency where you only trust patch-level updates.

#### 4. Comparison Operators
Support for `>=`, `<=`, `>`, `<`, `=` operators.

```yaml
dependencies:
  plugins:
    plugin-a: ">=1.0.0"   # Any version 1.0.0 or higher
    plugin-b: ">2.0.0"    # Strictly greater than 2.0.0
    plugin-c: "<=3.0.0"   # Up to and including 3.0.0
    plugin-d: "<2.0.0"    # Strictly less than 2.0.0
    plugin-e: "=1.5.0"    # Exact version (same as "1.5.0")
```

**Use Cases:**
- `>=X.Y.Z`: Minimum version requirement
- `<X.0.0`: Maximum major version
- `>X.Y.Z`: Exclude specific version

#### 5. Range Constraints
Combine multiple operators for precise ranges.

```yaml
dependencies:
  plugins:
    plugin-a: ">=1.0.0 <2.0.0"   # 1.x.x versions only
    plugin-b: ">1.5.0 <=2.3.0"   # Between 1.5.0 and 2.3.0
```

**Use Case**: When you need precise control over acceptable version range.

#### 6. Wildcard Constraints
Use `*` for flexible matching.

```yaml
dependencies:
  plugins:
    plugin-a: "*"       # Any version
    plugin-b: "1.*"     # Any 1.x.x version
    plugin-c: "1.2.*"   # Any 1.2.x version
```

**Rules:**
- `*` → `>=0.0.0` (any version)
- `1.*` → `>=1.0.0 <2.0.0`
- `1.2.*` → `>=1.2.0 <1.3.0`

**Use Case**: Maximum flexibility for internal or tightly-controlled dependencies.

### Dependency Validation

The system validates dependencies in two phases:

#### Phase 1: Load Time
When plugins are loaded, the system:
1. Parses all plugin manifests
2. Extracts dependency constraints
3. Validates that all required plugins exist

#### Phase 2: Graph Building
Before instantiating plugins:
1. Builds dependency graph with all plugins
2. Validates version constraints for each dependency
3. Detects circular dependencies
4. Computes topological load order

**Example:**
```python
from core.plugin_manager import PluginManager
from core.dependency_graph import VersionIncompatibilityError

manager = PluginManager()

try:
    loaded, failed = manager.load_plugins(plugins_dir="plugins")
    print(f"Successfully loaded {len(loaded)} plugins")
except VersionIncompatibilityError as e:
    print(f"Version conflict: {e}")
    print(f"Plugin '{e.dependent_plugin}' requires")
    print(f"'{e.dependency_plugin}' version '{e.required_version}'")
    print(f"but found version '{e.actual_version}'")
```

### Error Handling

#### Missing Dependency
```
MissingDependencyError: Plugin 'plugin-a' has missing dependencies: plugin-b, plugin-c
```

**Solution**: Install missing plugins or remove the dependent plugin.

#### Version Incompatibility
```
VersionIncompatibilityError: Plugin 'plugin-a' requires 'plugin-b' version '^2.0.0', 
but found version '1.5.0'
```

**Solutions:**
1. Update `plugin-b` to compatible version (e.g., 2.0.0+)
2. Downgrade `plugin-a` to version compatible with plugin-b 1.5.0
3. Adjust version constraint in plugin-a manifest

#### Circular Dependency
```
CyclicDependencyError: Cyclic dependency detected: plugin-a -> plugin-b -> plugin-a
```

**Solution**: Refactor plugins to remove circular dependency.

### Best Practices

#### 1. Use Caret for Most Dependencies
```yaml
dependencies:
  plugins:
    plugin-utils: "^1.0.0"  # Trust minor updates
```
**Reason**: Follows semver philosophy - minor/patch updates should be backwards-compatible.

#### 2. Use Tilde for Risky Dependencies
```yaml
dependencies:
  plugins:
    plugin-experimental: "~0.5.0"  # Only patch updates
```
**Reason**: Pre-1.0 or unstable plugins may break compatibility in minor versions.

#### 3. Use Ranges for Major Version Transitions
```yaml
dependencies:
  plugins:
    plugin-core: ">=1.5.0 <3.0.0"  # Support 1.x and 2.x
```
**Reason**: Allows gradual migration across major versions.

#### 4. Pin Exact Versions for Critical Production
```yaml
dependencies:
  plugins:
    plugin-payment: "2.3.1"  # Exact version
```
**Reason**: Zero surprises - only update after thorough testing.

#### 5. Use Wildcards for Internal Plugins
```yaml
dependencies:
  plugins:
    company-internal-utils: "*"  # Any version
```
**Reason**: Internal plugins are under your control and versioned together.

#### 6. Document Breaking Changes
When releasing a new major version:
- Document all breaking changes in CHANGELOG.md
- Provide migration guide
- Consider deprecation warnings in previous version

#### 7. Test Across Version Range
Test your plugin with:
- Minimum supported version of each dependency
- Latest supported version of each dependency
- Common intermediate versions

### Example: Complete Dependency Declaration

```yaml
id: plugin-processing-enricher
name: Property Enricher
version: 2.1.0
type: processing

dependencies:
  # Core system requirements
  core_version: ">=1.0.0"
  python_version: ">=3.10,<4.0"
  
  # Plugin dependencies with various constraints
  plugins:
    # Required base functionality - caret for stability
    plugin-source-base: "^2.0.0"
    
    # Geocoding service - tilde for conservative updates
    plugin-processing-geocoder: "~1.5.0"
    
    # ML model plugin - exact version for reproducibility
    plugin-detection-ml-model: "3.2.1"
    
    # Utility library - range for flexibility
    plugin-utils-common: ">=1.0.0 <2.0.0"
    
    # Optional enhancement - any version
    plugin-enhancement-images: "*"
    
    # Cache service - support both v1 and v2
    plugin-cache-redis: ">=1.5.0 <3.0.0"
```

### Troubleshooting

#### Check Installed Versions
```python
from core.plugin_manager import manager

for plugin_id, metadata in manager.list_plugins().items():
    print(f"{plugin_id}: v{metadata.version}")
```

#### Validate Specific Constraint
```python
from core.utils.semver import Version, VersionConstraint

version = Version.parse("2.1.5")
constraint = VersionConstraint("^2.0.0")

if constraint.satisfies(version):
    print("✓ Version satisfies constraint")
else:
    print("✗ Version does not satisfy constraint")
```

#### Visualize Dependency Graph
```python
from core.plugin_manager import manager

manager.build_dependency_graph()
dot_graph = manager._dependency_graph.export_dot()

# Save to file for visualization with Graphviz
with open("dependencies.dot", "w") as f:
    f.write(dot_graph)

# Convert to image: dot -Tpng dependencies.dot -o dependencies.png
```

## Hot Reload

The plugin system supports hot reload - updating plugin code without restarting the core service. This enables:
- **Development**: Rapid iteration without service restarts
- **Production Updates**: Deploy bug fixes and features with zero downtime  
- **A/B Testing**: Safely test new plugin versions

### How It Works

Hot reload follows a 5-step process:

1. **Graceful Shutdown**: Calls `shutdown()` on old plugin instance
2. **Module Reload**: Uses `importlib.reload()` to load updated Python code
3. **Class Lookup**: Finds plugin class in reloaded module
4. **Instantiation**: Creates new instance with updated code
5. **Instance Replacement**: Atomically replaces old instance with new one

### Usage

**Via API:**
```bash
curl -X POST http://localhost:8000/api/v1/plugins/plugin-source-cian/reload
```

**Via Python:**
```python
from core.plugin_manager import manager

# Reload specific plugin
updated = manager.reload_plugin("plugin-source-cian")
print(f"Reloaded: {updated.name} v{updated.version}")
```

### Implementing Graceful Shutdown

Override the `shutdown()` method in your plugin to perform cleanup:

```python
from core.interfaces.source_plugin import SourcePlugin

class MySourcePlugin(SourcePlugin):
    def __init__(self):
        self.db_connection = create_connection()
        self.background_task = start_task()
    
    def shutdown(self) -> None:
        """Gracefully shutdown plugin before reload."""
        # Close database connections
        if self.db_connection:
            self.db_connection.close()
        
        # Stop background tasks
        if self.background_task:
            self.background_task.cancel()
        
        # Save state if needed
        self.save_state()
    
    # ... implement abstract methods ...
```

### Best Practices

1. **Implement shutdown()**: Always cleanup resources (connections, threads, files)
2. **Keep State External**: Store plugin state in database/cache, not in-memory
3. **Test Reload**: Include reload scenarios in your integration tests
4. **Version Carefully**: Update plugin version after significant changes
5. **Monitor Errors**: Watch logs during reload for import/instantiation failures
6. **Avoid Long Shutdowns**: Keep `shutdown()` fast (<5 seconds) to prevent timeouts

### Limitations

**Module Caching**: Python caches bytecode, so some code changes may not reload:
- Changes to imported dependencies
- Changes to module-level variables
- Structural changes (removing classes)

**Workaround**: Restart service for major refactors

**Active Requests**: In-flight requests using old instance may fail
**Workaround**: Use request draining or load balancer health checks

**Memory Leaks**: Old instances not garbage collected if referenced elsewhere
**Workaround**: Ensure `shutdown()` breaks all circular references

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Plugin not found" | Plugin not registered | Load plugin first via `load_plugins()` |
| "Plugin not loaded" | Metadata exists but no instance | Check original load succeeded |
| "Failed to reload module" | Import error in updated code | Check logs for syntax/import errors |
| "Class not found" | Plugin class renamed/removed | Keep class name stable across reloads |
| "Can't instantiate" | Missing abstract method impl | Implement all required methods |
| Shutdown timeout | Long-running cleanup | Optimize `shutdown()` for <5s |
| Old behavior persists | Module cache issue | Restart service or clear `sys.modules` |

### Example: Full Reload Workflow

```python
# 1. Initial load
from core.plugin_manager import manager
from pathlib import Path

loaded, failed = manager.load_plugins(plugins_dir=Path("plugins"))
print(f"Loaded: {len(loaded)} plugins")

# 2. Modify plugin code
#    Edit plugins/my_plugin/source.py to fix a bug

# 3. Hot reload
try:
    updated = manager.reload_plugin("plugin-source-my-plugin")
    print(f"✓ Reloaded: {updated.name}")
except RuntimeError as e:
    print(f"✗ Reload failed: {e}")
    # Old instance still functional, check logs

# 4. Verify new behavior
plugin_instance = manager._instances["plugin-source-my-plugin"]
result = plugin_instance.scrape({"test": True})
print(f"New behavior working: {result}")
```

### Logging

Hot reload emits detailed logs:

```
INFO  - Starting hot reload for plugin: plugin-source-cian
DEBUG - Calling shutdown() on plugin-source-cian
INFO  - Graceful shutdown completed for plugin-source-cian
DEBUG - Reloading module: cian_scraper
DEBUG - Module reloaded successfully
INFO  - New instance created for plugin-source-cian
INFO  - Hot reload completed successfully for plugin-source-cian
```

Set log level to DEBUG for troubleshooting:
```python
import logging
logging.getLogger('core.plugin_manager').setLevel(logging.DEBUG)
```

