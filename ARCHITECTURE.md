# Архитектура сервиса RealEstatesAntiFraud

## Обзор системы

Модульная микросервисная архитектура для аггрегации объявлений о недвижимости с интеллектуальной системой детекции мошенничества.

## Принципы архитектуры

### 🔌 Plugin-Based Architecture

Система построена на принципе **модульности и расширяемости** через plugin API:

- **Core System** - неизменяемое ядро с API для плагинов
- **Source Plugins** - модули источников данных (скрейперы, API-коннекторы)
- **Processing Plugins** - модули обработки и трансформации
- **Detection Plugins** - модули детекции мошенничества
- **Search Plugins** - модули поиска и индексации
- **Display Plugins** - модули отображения и форматирования

### Ключевые преимущества:

✅ Добавление новых источников без изменения ядра  
✅ Независимая разработка и тестирование модулей  
✅ Версионирование плагинов  
✅ Горячая замена и обновление модулей  
✅ Marketplace плагинов для сообщества

## Основные компоненты

### 1. Core System (Ядро системы)

#### 1.1 Plugin Manager
- **Функции**:
  - Регистрация и загрузка плагинов
  - Управление жизненным циклом плагинов
  - Dependency injection
  - Версионирование и совместимость
  - Изоляция плагинов (sandboxing)

#### 1.2 Plugin Registry API
- **Endpoints**:
  - `POST /api/plugins/register` - Регистрация плагина
  - `GET /api/plugins/list` - Список установленных плагинов
  - `PUT /api/plugins/{id}/enable` - Активация плагина
  - `DELETE /api/plugins/{id}` - Удаление плагина
  - `GET /api/plugins/{id}/status` - Статус плагина

#### 1.3 Unified Data Model (UDM)
**Стандартизированная модель данных для всех источников**:

```json
{
  "listing_id": "uuid",
  "source": {
    "plugin_id": "string",
    "platform": "string",
    "original_id": "string",
    "url": "string"
  },
  "type": "sale|rent",
  "property_type": "apartment|house|commercial|land",
  "location": {
    "country": "string",
    "region": "string",
    "city": "string",
    "district": "string",
    "address": "string",
    "coordinates": {"lat": 0.0, "lng": 0.0},
    "postal_code": "string"
  },
  "price": {
    "amount": 0,
    "currency": "string",
    "price_per_sqm": 0,
    "negotiable": false
  },
  "details": {
    "area_total": 0,
    "area_living": 0,
    "rooms": 0,
    "bedrooms": 0,
    "bathrooms": 0,
    "floor": 0,
    "total_floors": 0,
    "year_built": 0,
    "condition": "string",
    "features": []
  },
  "description": {
    "title": "string",
    "text": "string",
    "language": "string"
  },
  "media": {
    "images": [{"url": "string", "caption": "string"}],
    "videos": [{"url": "string"}],
    "virtual_tour": "string"
  },
  "seller": {
    "type": "owner|agent|agency",
    "name": "string",
    "contacts": {
      "phone": [],
      "email": [],
      "messenger": {}
    }
  },
  "metadata": {
    "published_at": "timestamp",
    "updated_at": "timestamp",
    "scraped_at": "timestamp",
    "raw_data": {}
  }
}
```

### 2. Source Plugins Layer (Слой источников данных)

**Каждый источник = отдельный плагин**

#### 2.1 Plugin Structure
```
plugin-source-{platform}/
├── plugin.yaml              # Манифест плагина
├── scraper.py              # Логика скрейпинга
├── mapper.py               # Маппинг в UDM
├── config.yaml             # Конфигурация
├── requirements.txt        # Зависимости
└── tests/                  # Тесты
```

#### 2.2 Scraper Plugins (Примеры)

**A. HTML Scraper Plugin** (для сайтов без API)
- **plugin-source-avito**
- **plugin-source-cian**
- **plugin-source-domclick**
- **plugin-source-yandex-realty**

**Общие возможности**:
- Scrapy/Playwright/Selenium
- Anti-detection встроенный
- Rate limiting
- Retry logic
- Инкрементальный сбор

**B. API Connector Plugin** (для партнерских API)
- **plugin-source-api-partner1**
- **plugin-source-api-partner2**

**Возможности**:
- OAuth2/API Key authentication
- Rate limiting по лимитам API
- Webhook поддержка для real-time updates
- Batch API calls

**C. RSS/Feed Plugin**
- **plugin-source-rss-generic**

**D. Database Connector Plugin**
- **plugin-source-db-postgres**
- Для импорта из внешних БД

#### 2.3 Source Plugin API Interface

Каждый source plugin должен реализовать:

```python
from abc import ABC, abstractmethod
from typing import Iterator, Dict

class SourcePlugin(ABC):
    """Base class for all source plugins"""
    
    @abstractmethod
    def get_metadata(self) -> Dict:
        """Returns plugin metadata"""
        pass
    
    @abstractmethod
    def configure(self, config: Dict) -> None:
        """Configure plugin with settings"""
        pass
    
    @abstractmethod
    def scrape(self, params: Dict) -> Iterator[Dict]:
        """
        Main scraping method
        Yields listings in Unified Data Model format
        """
        pass
    
    @abstractmethod
    def validate(self, listing: Dict) -> bool:
        """Validate listing data"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict:
        """Return scraping statistics"""
        pass
```

#### 2.4 Scheduler Service (для всех плагинов)
- **Технологии**: Apache Airflow / Celery Beat
- **Функции**:
  - Управление расписанием всех source plugins
  - Приоритизация задач
  - Мониторинг статуса
  - Адаптивная частота обновлений по источникам

#### 2.5 Anti-Detection Service (общий для скрейперов)
- **Компоненты**:
  - Пул прокси-серверов (residential/mobile)
  - User-Agent rotation
  - Browser fingerprint randomization
  - Cookie management
  - TLS fingerprint spoofing
  - CAPTCHA solving integration

### 3. Processing Plugins Layer (Слой обработки данных)

**Модульная система обработки данных**

#### 3.1 Processing Plugin API Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class ProcessingPlugin(ABC):
    """Base class for processing plugins"""
    
    @abstractmethod
    def get_metadata(self) -> Dict:
        """Returns plugin metadata"""
        pass
    
    @abstractmethod
    def process(self, listing: Dict) -> Dict:
        """
        Process listing and return enriched data
        Input: listing in UDM format
        Output: enriched listing in UDM format
        """
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Return execution priority (lower = earlier)"""
        pass
```

#### 3.2 Built-in Processing Plugins

**A. Validation Plugin** (`plugin-processing-validator`)
- Проверка обязательных полей
- Валидация типов данных
- Проверка диапазонов значений

**B. Normalization Plugin** (`plugin-processing-normalizer`)
- Стандартизация адресов
- Нормализация цен (к единой валюте)
- Унификация единиц измерения
- Очистка текста

**C. Geocoding Plugin** (`plugin-processing-geocoder`)
- Геокодирование адресов
- Определение координат
- Enrichment с данными района
- Интеграция: Google Maps API, Yandex Maps, OSM

**D. NLP Analysis Plugin** (`plugin-processing-nlp`)
- Извлечение ключевых слов
- Sentiment analysis
- Language detection
- Entity extraction (metro, schools, etc.)

**E. Image Processing Plugin** (`plugin-processing-images`)
- EXIF metadata extraction
- Image quality assessment
- Thumbnail generation
- Face/license plate blurring

**F. Price Analysis Plugin** (`plugin-processing-price-analyzer`)
- Вычисление цены за м²
- Сравнение с рыночными ценами
- Детекция аномальных цен
- Price history tracking

**G. Deduplication Plugin** (`plugin-processing-dedup`)
- **Технологии**: MinHash, LSH
- Обнаружение дубликатов по тексту
- Сравнение изображений (perceptual hashing)
- Связывание объявлений от одного продавца

#### 3.3 ETL Pipeline Orchestrator
- **Технологии**: Apache Kafka / RabbitMQ, Apache Spark
- **Процесс**:
  1. Source plugin → Raw data → Kafka topic
  2. Processing Pipeline reads from Kafka
  3. Executes plugins by priority
  4. Each plugin enriches the data
  5. Final data → Storage layer

**Pipeline Configuration Example**:
```yaml
pipeline:
  - plugin: validator
    priority: 1
    config:
      strict_mode: true
  
  - plugin: normalizer
    priority: 2
    
  - plugin: geocoder
    priority: 3
    config:
      provider: yandex
      fallback: google
  
  - plugin: nlp
    priority: 4
    parallel: true
    
  - plugin: images
    priority: 5
    parallel: true
    
  - plugin: dedup
    priority: 10
```

### 4. Detection Plugins Layer (Слой детекции мошенничества)

**Модульная система детекции fraud**

#### 4.1 Detection Plugin API Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List

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
        Returns: {
            'signals': [{'type': str, 'severity': float, 'description': str}],
            'confidence': float,
            'details': {}
        }
        """
        pass
    
    @abstractmethod
    def get_weight(self) -> float:
        """Return plugin weight in final score calculation"""
        pass
```

#### 4.2 Detection Plugins

**A. ML Classifier Plugin** (`plugin-detection-ml-classifier`)
- **Технологии**: scikit-learn, XGBoost/LightGBM
- **Модель**: Gradient Boosting Classifier
- **Features**:
  - Price anomaly score
  - Text quality metrics
  - Image count/quality
  - Seller behavior patterns
  - Historical data

**B. Deep Learning Plugin** (`plugin-detection-deep-learning`)
- **Технологии**: TensorFlow/PyTorch
- **Модели**:
  - BERT для анализа текста
  - CNN для анализа изображений
  - Multi-modal fusion

**C. Image Analysis Plugin** (`plugin-detection-image-analysis`)
- **Функции**:
  - Reverse image search (TinEye, Google)
  - Stock photo detection
  - Photoshop/manipulation detection
  - EXIF metadata validation
  - Image quality assessment

**D. Price Anomaly Plugin** (`plugin-detection-price-anomaly`)
- **Алгоритмы**: Isolation Forest, Z-score
- **Проверки**:
  - Сравнение с рыночными ценами
  - Детекция слишком низких/высоких цен
  - Historical price analysis
  - Price-per-sqm validation

**E. Text Analysis Plugin** (`plugin-detection-text-analysis`)
- **NLP анализ**:
  - Spelling/grammar check
  - Keyword spam detection
  - Urgency language patterns
  - Scam phrase detection
  - Language consistency

**F. Seller Reputation Plugin** (`plugin-detection-seller-reputation`)
- **Анализ**:
  - Частота публикаций
  - Количество активных объявлений
  - История предыдущих объявлений
  - Phone/email blacklist check
  - Cross-platform seller analysis

**G. Location Validation Plugin** (`plugin-detection-location-validator`)
- **Проверки**:
  - Существование адреса
  - Соответствие фото и геолокации
  - Distance anomalies
  - Property existence verification

**H. Rules Engine Plugin** (`plugin-detection-rules`)
- **Технологии**: Drools / JSON Rules Engine
- **Правила**:
  - Blacklist (phones, emails, keywords)
  - Threshold-based rules
  - Pattern matching
  - Configurable rule sets

**I. Behavioral Analysis Plugin** (`plugin-detection-behavioral`)
- **Graph Analysis**:
  - Network analysis связей между объявлениями
  - Cluster detection
  - Аномалии в паттернах поведения
  - Coordinated fraud detection

#### 4.3 Risk Scoring Orchestrator
- **Функции**:
  - Запуск всех активных detection plugins
  - Агрегация результатов с учетом весов
  - Вычисление итогового fraud score (0-100)
  - Классификация (safe/suspicious/fraud)

**Scoring Formula**:
```python
fraud_score = sum(
    plugin.analyze(listing)['confidence'] * plugin.get_weight()
    for plugin in active_detection_plugins
) / sum(plugin.get_weight() for plugin in active_detection_plugins)

risk_level = {
    'safe': fraud_score < 30,
    'suspicious': 30 <= fraud_score < 70,
    'fraud': fraud_score >= 70
}
```

### 4. Storage Layer (Слой хранения)

#### 4.1 Primary Database
- **PostgreSQL** (основные данные)
  - Объявления
  - Пользователи
  - Транзакции
  - Метрики качества
  
### 5. Search Plugins Layer (Слой поиска)

**Модульная система поиска и индексации**

#### 5.1 Search Plugin API Interface

```python
from abc import ABC, abstractmethod
from typing import Dict, List

class SearchPlugin(ABC):
    """Base class for search plugins"""
    
    @abstractmethod
    def index(self, listing: Dict) -> bool:
        """Index a listing"""
        pass
    
    @abstractmethod
    def search(self, query: Dict) -> List[Dict]:
        """
        Execute search query
        Returns: list of listings with relevance scores
        """
        pass
    
    @abstractmethod
    def suggest(self, prefix: str) -> List[str]:
        """Auto-suggest for search"""
        pass
```

#### 5.2 Search Plugins

**A. Elasticsearch Plugin** (`plugin-search-elasticsearch`)
- Full-text search
- Faceted search (фильтры)
- Geo-search
- Fuzzy matching
- Aggregations

**B. Meilisearch Plugin** (`plugin-search-meilisearch`)
- Быстрый typo-tolerant поиск
- Instant search
- Легковесная альтернатива

**C. Algolia Plugin** (`plugin-search-algolia`)
- Managed search as a service
- Advanced ranking
- Personalization

**D. PostgreSQL FTS Plugin** (`plugin-search-postgres-fts`)
- Native PostgreSQL full-text search
- Для простых случаев

#### 5.3 Index Manager
- Управление индексами всех search plugins
- Routing запросов к нужному плагину
- Fallback механизмы

#### 4.2 Primary Search Engine (Default)
- **Elasticsearch**
  - Full-text search по объявлениям
  - Фасетный поиск (фильтры)
  - Geo-поиск
  - Индексы для быстрого поиска

#### 4.3 Document Store
- **MongoDB**
  - Сырые HTML страницы
  - Логи скрейпинга
  - Неструктурированные данные

#### 4.4 Cache Layer
- **Redis**
  - Кэширование популярных запросов
  - Session management
  - Rate limiting
  - Real-time counters

#### 4.5 Object Storage
- **MinIO / AWS S3**
  - Изображения объявлений
  - Бэкапы
  - ML модели

#### 4.6 Time-Series Database
- **InfluxDB / TimescaleDB**
  - Метрики мониторинга
  - История изменения цен
  - Статистика скрейпинга

### 5. API Layer (Слой API)

#### 5.1 Gateway API
- **Технологии**: Kong / Nginx + Custom Service (Node.js/Go)
- **Функции**:
  - Rate limiting
  - Authentication/Authorization (JWT)
  - Request routing
  - API versioning

#### 5.2 REST API Service
- **Технологии**: FastAPI (Python) / Express (Node.js)
- **Endpoints**:
  - `/api/v1/listings` - CRUD объявлений
  - `/api/v1/search` - Поиск
  - `/api/v1/fraud-check` - Проверка объявления
  - `/api/v1/stats` - Статистика
  - `/api/v1/alerts` - Уведомления о фроде

#### 5.3 GraphQL API (опционально)
- **Технологии**: Apollo Server
- **Преимущества**: Гибкие запросы для фронтенда

### 6. Display Plugins Layer (Слой отображения)

**Модульная система визуализации и форматирования**

#### 6.1 Display Plugin API Interface

```python
from abc import ABC, abstractmethod
from typing import Dict

class DisplayPlugin(ABC):
    """Base class for display plugins"""
    
    @abstractmethod
    def format_listing(self, listing: Dict, format: str) -> Dict:
        """
        Format listing for display
        format: 'card', 'list', 'detail', 'map', 'export'
        """
        pass
    
    @abstractmethod
    def get_template(self) -> str:
        """Return template name/path"""
        pass
```

#### 6.2 Display Plugins

**A. Card View Plugin** (`plugin-display-card`)
- Компактное отображение в виде карточек
- Настраиваемые поля

**B. List View Plugin** (`plugin-display-list`)
- Табличное отображение
- Sortable columns

**C. Map View Plugin** (`plugin-display-map`)
- Интеграция с картами
- Clusters
- Heatmaps

**D. Detail View Plugin** (`plugin-display-detail`)
- Полная информация
- Gallery
- Contact forms

**E. Export Plugins**
- `plugin-display-export-pdf`
- `plugin-display-export-excel`
- `plugin-display-export-json`

### 7. Frontend Layer (Слой интерфейса)

#### 7.1 Web Application
- **Технологии**: React/Vue.js/Next.js
- **Функции**:
  - Каталог объявлений (через display plugins)
  - Расширенный поиск с фильтрами
  - Карты (Mapbox/Google Maps)
  - Индикатор fraud score
  - Личный кабинет
  - Система уведомлений
  - **Plugin Marketplace UI**

#### 7.2 Admin Dashboard
- **Технологии**: React Admin / Vue Admin
- **Функции**:
  - **Управление плагинами** (установка/удаление/настройка)
  - Мониторинг скрейперов
  - Управление правилами детекции
  - Ревью помеченных объявлений
  - Аналитика и отчеты
  - Управление источниками
  - **Plugin Store** (установка новых плагинов)

### 8. Supporting Services (Вспомогательные сервисы)

#### 7.1 Notification Service
- **Технологии**: Node.js + Bull Queue
- **Каналы**: Email, Push, SMS, Telegram
- **Триггеры**: Новые объявления, высокий fraud score

#### 7.2 Analytics Service
- **Технологии**: Apache Superset / Metabase
- **Метрики**:
  - Статистика по рынку недвижимости
  - Эффективность детекции фрода
  - Качество источников данных

#### 7.3 Monitoring & Logging
- **Технологии**:
  - **OpenTelemetry** - единый стандарт observability (traces, metrics, logs)
  - Prometheus + Grafana (метрики)
  - ELK Stack (Elasticsearch, Logstash, Kibana) - логи
  - Sentry - отслеживание ошибок
  - Jaeger / Tempo - distributed tracing (OpenTelemetry compatible)
  
**OpenTelemetry Integration:**
- **Traces**: Автоматическая инструментация FastAPI, PostgreSQL, Redis, HTTP clients
- **Metrics**: Custom метрики (plugin execution time, fraud detection accuracy, scraping stats)
- **Logs**: Структурированные логи с correlation IDs (trace_id, span_id)
- **Exporters**: OTLP (OpenTelemetry Protocol) для отправки в Jaeger/Tempo/Grafana Cloud
- **Context Propagation**: W3C Trace Context для distributed tracing across services
- **Sampling**: Head-based sampling (configurable rate) для production

#### 7.4 Model Training Pipeline
- **Технологии**: Kubeflow / MLflow
- **Функции**:
  - Автоматическое переобучение моделей
  - A/B тестирование моделей
  - Feature store
  - Model versioning

## Архитектурная диаграмма

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   Web App        │              │  Admin Dashboard │        │
│  │  (React/Next.js) │              │   (React Admin)  │        │
│  └──────────────────┘              └──────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API GATEWAY                            │
│              (Kong/Nginx + Auth + Rate Limiting)                │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  REST API    │    │   GraphQL API    │    │ WebSocket    │
│  (FastAPI)   │    │ (Apollo Server)  │    │   Server     │
└──────────────┘    └──────────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Search Service   │  │ Listing Service  │  │  User Service    │
│ (Elasticsearch)  │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRAUD DETECTION LAYER                        │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │  ML Classifier │  │  Rules Engine  │  │ Risk Scoring   │   │
│  │ (XGBoost/NN)   │  │   (Drools)     │  │    Service     │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │          Image Analysis (CNN + Reverse Search)          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DATA PROCESSING LAYER                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Message Queue (Kafka/RabbitMQ)                        │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ ETL Pipeline   │  │ Deduplication  │  │  NLP Service   │   │
│  │ (Spark/Airflow)│  │ Service (LSH)  │  │                │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SCRAPING LAYER                             │
│  ┌────────────────────────────────────────────────────────┐    │
│  │         Scheduler (Airflow/Celery Beat)                │    │
│  └────────────────────────────────────────────────────────┘    │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐   │
│  │ Scraper Pool   │  │ Anti-Detection │  │  Proxy Pool    │   │
│  │ (Scrapy/       │  │    Module      │  │ (Residential)  │   │
│  │  Playwright)   │  │                │  │                │   │
│  └────────────────┘  └────────────────┘  └────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │ PostgreSQL   │ │ Elasticsearch│ │   MongoDB    │           │
│  │ (Main DB)    │ │  (Search)    │ │ (Raw Data)   │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
│  │    Redis     │ │    MinIO     │ │  InfluxDB    │           │
│  │   (Cache)    │ │  (Objects)   │ │ (TimeSeries) │           │
│  └──────────────┘ └──────────────┘ └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MONITORING & OBSERVABILITY                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              OpenTelemetry Collector                    │   │
│  │  (Traces, Metrics, Logs aggregation & export)           │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Jaeger/Tempo │  │  Prometheus  │  │  ELK Stack   │         │
│  │  (Traces)    │  │  +Grafana    │  │   (Logs)     │         │
│  │              │  │  (Metrics)   │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow (Поток данных)

### 1. Сбор данных
```
Scheduler → Scraper Service (+ Anti-Detection) 
    → Raw HTML → Message Queue (Kafka)
    → ETL Pipeline → Normalization + Enrichment
    → Deduplication → Storage (PostgreSQL + Elasticsearch)
```

### 2. Детекция мошенничества
```
New Listing → Fraud Detection Service
    ├→ ML Classifier (features extraction → prediction)
    ├→ Rules Engine (rule matching)
    ├→ Image Analysis (CNN + reverse search)
    └→ Risk Scoring → Store fraud_score
    
If high_risk → Alert to Admin Dashboard
```

### 3. Поиск и выдача
```
User Search Request → API Gateway 
    → Search Service (Elasticsearch)
    → Filter by fraud_score (exclude high-risk)
    → Enrich with data from PostgreSQL
    → Return results to Frontend
```

## Технологический стек

### Backend
- **Python**: Scrapy, FastAPI, scikit-learn, TensorFlow
- **Node.js**: Real-time services, WebSocket
- **Go**: High-performance services (опционально)

### Databases & Storage
- PostgreSQL, MongoDB, Elasticsearch, Redis, MinIO, InfluxDB

### Message Queues
- Apache Kafka / RabbitMQ

### Orchestration
- Docker + Kubernetes
- Apache Airflow

### ML/AI
- TensorFlow/PyTorch, XGBoost, MLflow, Kubeflow

### Observability
- **OpenTelemetry** (traces, metrics, logs)
- Jaeger / Tempo (tracing backend)
- Prometheus + Grafana (metrics & dashboards)
- ELK Stack (log aggregation)
- Sentry (error tracking)

### Frontend
- React/Next.js, TypeScript, TailwindCSS

## Безопасность

### 1. Scraping Security
- Rotating proxies (residential/mobile)
- Распределенная архитектура
- Случайные задержки (1-5 сек)
- Разные User-Agents и браузерные отпечатки
- CAPTCHA-solving services интеграция

### 2. API Security
- JWT Authentication
- Rate limiting (по IP и пользователю)
- CORS policies
- Input validation
- SQL injection protection

### 3. Data Security
- Шифрование данных в покое (at rest)
- TLS для передачи данных
- GDPR compliance (анонимизация)
- Regular security audits

## Масштабирование

### Horizontal Scaling
- Все сервисы в Docker containers
- Kubernetes для оркестрации
- Auto-scaling на основе нагрузки
- Load balancing

### Vertical Scaling
- Database sharding (по регионам)
- Read replicas для PostgreSQL
- Elasticsearch cluster
- Redis cluster

### Caching Strategy
- Multi-level caching (L1: Application, L2: Redis)
- CDN для статики
- Кэширование поисковых запросов

## Этапы разработки

### Phase 1: MVP (2-3 месяца)
- [ ] Базовый скрейпер для 2-3 источников
- [ ] PostgreSQL + Elasticsearch setup
- [ ] Простой REST API
- [ ] Минимальный фронтенд
- [ ] Rule-based fraud detection

### Phase 2: ML Integration (2-3 месяца)
- [ ] ML модель для детекции фрода
- [ ] Image analysis module
- [ ] Улучшенный ETL pipeline
- [ ] Admin dashboard
- [ ] Мониторинг и алерты

### Phase 3: Scaling (2-3 месяца)
- [ ] Расширение источников (10+)
- [ ] Kubernetes deployment
- [ ] Advanced anti-detection
- [ ] Real-time updates (WebSocket)
- [ ] Mobile app (опционально)

### Phase 4: Advanced Features (3-4 месяца)
- [ ] Price prediction ML model
- [ ] Recommendation system
- [ ] Social features
- [ ] API для партнеров
- [ ] Advanced analytics

## Метрики успеха

### Качество данных
- Количество активных объявлений
- Freshness данных (< 1 час)
- Процент дубликатов (< 5%)

### Fraud Detection
- Precision/Recall/F1-score модели
- False positive rate (< 5%)
- Time to detect (< 5 мин)

### Performance
- API response time (< 200ms p95)
- Search response time (< 100ms)
- Uptime (> 99.9%)

### Business Metrics
- DAU/MAU
- Conversion rate
- User satisfaction (NPS)

## Риски и митигация

| Риск | Вероятность | Воздействие | Митигация |
|------|-------------|-------------|-----------|
| Блокировка скрейперов | Высокая | Критическое | Прокси-ротация, anti-detection, резервные источники |
| Плохое качество ML модели | Средняя | Высокое | A/B тестирование, human-in-the-loop validation |
| Проблемы с производительностью | Средняя | Высокое | Load testing, horizontal scaling, caching |
| Юридические проблемы | Средняя | Критическое | Terms of service compliance, robots.txt, правовая экспертиза |
| GDPR нарушения | Низкая | Критическое | Анонимизация, consent management, DPO |

## Стоимость инфраструктуры (примерная, $/месяц)

- **Cloud Compute** (Kubernetes cluster): $500-1000
- **Databases** (managed): $300-500
- **Proxies** (residential): $500-1000
- **Object Storage**: $50-100
- **Monitoring & Logging**: $100-200
- **ML Infrastructure**: $200-400
- **CDN**: $50-100

**Total**: ~$1700-3300/месяц (на старте)

## Заключение

Данная архитектура обеспечивает:
- ✅ Масштабируемость и отказоустойчивость
- ✅ Эффективную детекцию мошенничества
- ✅ Незаметный сбор данных
- ✅ Высокую производительность
- ✅ Возможность постепенного развития

Система построена на принципах микросервисной архитектуры, что позволяет независимо разрабатывать, тестировать и масштабировать отдельные компоненты.
