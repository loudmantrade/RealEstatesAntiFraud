# RealEstatesAntiFraud - Project Structure

```
RealEstatesAntiFraud/
│
├── core/                           # Ядро системы (неизменяемое)
│   ├── __init__.py
│   ├── plugin_manager.py          # Менеджер плагинов
│   ├── plugin_registry.py         # Реестр плагинов
│   ├── api/                       # Core API
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── plugins.py        # API для управления плагинами
│   │   │   ├── listings.py       # API для объявлений
│   │   │   ├── search.py         # API поиска
│   │   │   └── admin.py          # Admin API
│   │   └── middleware/
│   │       ├── auth.py
│   │       ├── rate_limit.py
│   │       └── logging.py
│   ├── models/                    # Базовые модели данных
│   │   ├── __init__.py
│   │   ├── udm.py                # Unified Data Model
│   │   ├── plugin.py             # Plugin metadata model
│   │   └── user.py
│   ├── interfaces/                # Интерфейсы для плагинов
│   │   ├── __init__.py
│   │   ├── source_plugin.py
│   │   ├── processing_plugin.py
│   │   ├── detection_plugin.py
│   │   ├── search_plugin.py
│   │   └── display_plugin.py
│   ├── orchestration/             # Оркестрация процессов
│   │   ├── __init__.py
│   │   ├── scraping_scheduler.py
│   │   ├── etl_pipeline.py
│   │   ├── detection_orchestrator.py
│   │   └── index_manager.py
│   ├── storage/                   # Абстракция хранилища
│   │   ├── __init__.py
│   │   ├── postgres.py
│   │   ├── elasticsearch.py
│   │   ├── mongodb.py
│   │   └── redis.py
│   └── utils/                     # Утилиты
│       ├── __init__.py
│       ├── validation.py
│       ├── logging.py
│       └── helpers.py
│
├── plugins/                        # Директория плагинов
│   │
│   ├── sources/                   # Source plugins
│   │   ├── avito/
│   │   │   ├── plugin.yaml
│   │   │   ├── __init__.py
│   │   │   ├── scraper.py
│   │   │   ├── mapper.py
│   │   │   ├── config.yaml
│   │   │   ├── requirements.txt
│   │   │   ├── README.md
│   │   │   └── tests/
│   │   ├── cian/
│   │   │   └── ...
│   │   ├── domclick/
│   │   │   └── ...
│   │   ├── yandex-realty/
│   │   │   └── ...
│   │   └── api-partner-template/  # Шаблон для API коннекторов
│   │       └── ...
│   │
│   ├── processing/                # Processing plugins
│   │   ├── validator/
│   │   │   └── ...
│   │   ├── normalizer/
│   │   │   └── ...
│   │   ├── geocoder/
│   │   │   ├── plugin.yaml
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   └── providers/
│   │   │       ├── yandex.py
│   │   │       ├── google.py
│   │   │       └── osm.py
│   │   ├── nlp-analyzer/
│   │   │   └── ...
│   │   ├── image-processor/
│   │   │   └── ...
│   │   ├── price-analyzer/
│   │   │   └── ...
│   │   └── deduplicator/
│   │       └── ...
│   │
│   ├── detection/                 # Detection plugins
│   │   ├── ml-classifier/
│   │   │   ├── plugin.yaml
│   │   │   ├── __init__.py
│   │   │   ├── model.py
│   │   │   ├── features.py
│   │   │   ├── models/            # Сохраненные модели
│   │   │   │   ├── fraud_classifier_v1.pkl
│   │   │   │   └── scaler.pkl
│   │   │   └── training/
│   │   │       ├── train.py
│   │   │       └── evaluate.py
│   │   ├── deep-learning/
│   │   │   └── ...
│   │   ├── image-analysis/
│   │   │   ├── plugin.yaml
│   │   │   ├── __init__.py
│   │   │   ├── cnn_model.py
│   │   │   ├── reverse_search.py
│   │   │   └── manipulation_detector.py
│   │   ├── price-anomaly/
│   │   │   └── ...
│   │   ├── text-analysis/
│   │   │   └── ...
│   │   ├── seller-reputation/
│   │   │   └── ...
│   │   ├── location-validator/
│   │   │   └── ...
│   │   ├── rules-engine/
│   │   │   ├── plugin.yaml
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   └── rules/
│   │   │       ├── blacklist.json
│   │   │       ├── keywords.json
│   │   │       └── patterns.json
│   │   └── behavioral-analysis/
│   │       └── ...
│   │
│   ├── search/                    # Search plugins
│   │   ├── elasticsearch/
│   │   │   ├── plugin.yaml
│   │   │   ├── __init__.py
│   │   │   ├── indexer.py
│   │   │   ├── searcher.py
│   │   │   └── mappings/
│   │   │       └── listing.json
│   │   ├── meilisearch/
│   │   │   └── ...
│   │   └── postgres-fts/
│   │       └── ...
│   │
│   └── display/                   # Display plugins
│       ├── card-view/
│       │   └── ...
│       ├── list-view/
│       │   └── ...
│       ├── map-view/
│       │   └── ...
│       ├── detail-view/
│       │   └── ...
│       └── export-pdf/
│           └── ...
│
├── services/                      # Микросервисы
│   ├── api-gateway/              # API Gateway (Kong config)
│   │   ├── kong.yml
│   │   └── plugins/
│   ├── scraper-service/          # Scraping orchestration
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── app.py
│   │   └── config.py
│   ├── etl-service/              # ETL Pipeline
│   │   └── ...
│   ├── detection-service/        # Fraud detection orchestration
│   │   └── ...
│   ├── search-service/           # Search API
│   │   └── ...
│   ├── notification-service/     # Notifications
│   │   └── ...
│   └── analytics-service/        # Analytics
│       └── ...
│
├── infrastructure/               # Инфраструктура
│   ├── docker/
│   │   ├── docker-compose.yml    # Для разработки
│   │   ├── docker-compose.prod.yml
│   │   └── Dockerfile.*
│   ├── kubernetes/               # K8s манифесты
│   │   ├── namespaces/
│   │   ├── deployments/
│   │   ├── services/
│   │   ├── ingress/
│   │   ├── configmaps/
│   │   ├── secrets/
│   │   └── helm/                 # Helm charts
│   ├── terraform/                # Infrastructure as Code
│   │   ├── aws/
│   │   ├── gcp/
│   │   └── azure/
│   ├── ansible/                  # Configuration management
│   │   └── playbooks/
│   └── monitoring/               # Monitoring configs
│       ├── prometheus/
│       ├── grafana/
│       └── alertmanager/
│
├── frontend/                     # Frontend приложения
│   ├── web/                      # Web приложение
│   │   ├── package.json
│   │   ├── next.config.js
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── api/
│   │   │   ├── store/           # State management
│   │   │   └── utils/
│   │   └── public/
│   └── admin/                    # Admin dashboard
│       ├── package.json
│       └── src/
│           ├── pages/
│           │   ├── plugins/     # Plugin management UI
│           │   ├── scrapers/    # Scraper monitoring
│           │   ├── detection/   # Fraud detection UI
│           │   └── analytics/
│           └── components/
│
├── ml-models/                    # ML модели и обучение
│   ├── fraud-detection/
│   │   ├── notebooks/           # Jupyter notebooks
│   │   ├── data/
│   │   │   ├── raw/
│   │   │   ├── processed/
│   │   │   └── features/
│   │   ├── models/              # Обученные модели
│   │   ├── scripts/
│   │   │   ├── train.py
│   │   │   ├── evaluate.py
│   │   │   └── deploy.py
│   │   └── config/
│   ├── image-analysis/
│   │   └── ...
│   ├── price-prediction/
│   │   └── ...
│   └── mlflow/                  # MLflow tracking server config
│       └── docker-compose.yml
│
├── shared-libs/                  # Общие библиотеки
│   ├── python/
│   │   ├── udm/                 # UDM utilities
│   │   ├── api-client/          # API клиент
│   │   └── logging/             # Логирование
│   └── js/
│       └── api-client/
│
├── database/                     # Скрипты БД
│   ├── migrations/              # Миграции
│   │   ├── postgres/
│   │   └── mongodb/
│   ├── seeds/                   # Тестовые данные
│   └── schemas/
│       ├── postgres/
│       │   ├── listings.sql
│       │   ├── plugins.sql
│       │   ├── users.sql
│       │   └── fraud_signals.sql
│       └── elasticsearch/
│           └── listings_mapping.json
│
├── docs/                         # Документация
│   ├── README.md
│   ├── ARCHITECTURE.md          # Архитектура
│   ├── PLUGIN_DEVELOPMENT.md    # Разработка плагинов
│   ├── UNIFIED_DATA_MODEL.md    # UDM спецификация
│   ├── API.md                   # API документация
│   ├── DEPLOYMENT.md            # Развертывание
│   ├── CONTRIBUTING.md          # Как контрибьютить
│   └── images/                  # Диаграммы и скриншоты
│
├── tests/                        # Тесты
│   ├── unit/
│   │   ├── core/
│   │   └── plugins/
│   ├── integration/
│   │   ├── test_scraping_pipeline.py
│   │   ├── test_etl_pipeline.py
│   │   └── test_detection_pipeline.py
│   ├── e2e/
│   │   └── test_user_flows.py
│   ├── fixtures/
│   └── conftest.py
│
├── scripts/                      # Утилитные скрипты
│   ├── install_plugin.py
│   ├── migrate_database.py
│   ├── seed_data.py
│   ├── backup.sh
│   └── deploy.sh
│
├── .github/                      # GitHub workflows
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── cd.yml
│   │   ├── plugin-validation.yml
│   │   └── security-scan.yml
│   └── ISSUE_TEMPLATE/
│
├── config/                       # Конфигурация
│   ├── development.yaml
│   ├── staging.yaml
│   ├── production.yaml
│   └── plugins.yaml             # Конфигурация плагинов
│
├── .env.example                  # Пример переменных окружения
├── .gitignore
├── .dockerignore
├── requirements.txt              # Python зависимости (core)
├── package.json                  # Node.js скрипты
├── Makefile                      # Команды для разработки
├── docker-compose.yml            # Для локальной разработки
├── README.md                     # Главный README
├── LICENSE                       # Лицензия
└── CHANGELOG.md                  # История изменений
```

## Описание ключевых директорий

### `/core`
Неизменяемое ядро системы. Содержит:
- Plugin Manager для загрузки и управления плагинами
- Базовые интерфейсы для всех типов плагинов
- Unified Data Model (UDM)
- API endpoints
- Оркестрация процессов

### `/plugins`
Модульные плагины, организованные по типам:
- **sources/** - Скрейперы и API коннекторы
- **processing/** - Обработка и обогащение данных
- **detection/** - Детекция мошенничества
- **search/** - Поиск и индексация
- **display/** - Отображение данных

Каждый плагин - независимый модуль со своими зависимостями.

### `/services`
Микросервисы для различных функций:
- API Gateway (Kong)
- Scraper orchestration
- ETL pipeline
- Detection service
- Search service
- Notifications
- Analytics

### `/infrastructure`
Инфраструктурные конфигурации:
- Docker/Docker Compose
- Kubernetes manifests
- Terraform (IaC)
- Monitoring configs

### `/frontend`
Frontend приложения:
- **web/** - Пользовательский интерфейс (Next.js)
- **admin/** - Admin dashboard с UI для управления плагинами

### `/ml-models`
ML модели и обучение:
- Notebooks для экспериментов
- Training scripts
- Обученные модели
- MLflow configuration

### `/database`
Схемы БД и миграции:
- PostgreSQL schemas
- MongoDB schemas
- Elasticsearch mappings
- Migration scripts

## Workflow разработки

```bash
# 1. Клонирование
git clone https://github.com/yourorg/RealEstatesAntiFraud.git
cd RealEstatesAntiFraud

# 2. Запуск инфраструктуры
docker-compose up -d

# 3. Установка зависимостей
pip install -r requirements.txt
cd frontend/web && npm install

# 4. Применение миграций
python scripts/migrate_database.py

# 5. Установка базовых плагинов
make install-default-plugins

# 6. Запуск в dev режиме
make dev
```

## Makefile команды

```makefile
.PHONY: help dev test install-plugins

help:  ## Show help
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev:  ## Run in development mode
	docker-compose up -d
	python core/api/main.py

test:  ## Run tests
	pytest tests/ -v --cov=core --cov=plugins

install-plugins:  ## Install all default plugins
	python scripts/install_plugin.py plugins/sources/avito
	python scripts/install_plugin.py plugins/sources/cian
	python scripts/install_plugin.py plugins/processing/geocoder
	python scripts/install_plugin.py plugins/detection/ml-classifier

build:  ## Build Docker images
	docker-compose build

migrate:  ## Run database migrations
	python scripts/migrate_database.py

seed:  ## Seed database with test data
	python scripts/seed_data.py

clean:  ## Clean up
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
```
