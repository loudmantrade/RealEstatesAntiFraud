# RealEstatesAntiFraud

[![CI](https://github.com/loudmantrade/RealEstatesAntiFraud/actions/workflows/ci.yml/badge.svg)](https://github.com/loudmantrade/RealEstatesAntiFraud/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/loudmantrade/RealEstatesAntiFraud/branch/main/graph/badge.svg)](https://codecov.io/gh/loudmantrade/RealEstatesAntiFraud)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Интеллектуальный аггрегатор объявлений о недвижимости с системой автоматической детекции мошенничества.

## 🎯 Цель проекта

Создание надежной платформы для поиска недвижимости, которая:
- Собирает объявления с популярных досок объявлений
- Автоматически выявляет мошеннические объявления
- Предоставляет удобный поиск и фильтрацию
- Защищает пользователей от fraud

## 🏗️ Архитектура

Проект построен на микросервисной архитектуре с plugin-based extensibility. Подробное описание см. в [ARCHITECTURE.md](./ARCHITECTURE.md)

### 🔌 Plugin System

Система поддерживает пять типов плагинов:
- **Source Plugins** - Интеграция с источниками данных
- **Processing Plugins** - Обработка и обогащение данных
- **Detection Plugins** - Алгоритмы детекции мошенничества
- **Search Plugins** - Поисковые движки
- **Display Plugins** - Форматирование и отображение

**Документация:**
- [Plugin Manifest Specification v1.0](docs/PLUGIN_SPEC.md) - Формальная спецификация манифеста
- [Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md) - Руководство разработчика плагинов

### Основные компоненты:

1. **Scraping Layer** - Интеллектуальный сбор данных с антидетектом
2. **Fraud Detection** - ML-система детекции мошенничества
3. **Search Engine** - Быстрый полнотекстовый поиск
4. **API Layer** - REST/GraphQL API
5. **Web Application** - Пользовательский интерфейс

## 🚀 Функциональность

### Для пользователей:
- 🔍 Поиск объявлений с продвинутыми фильтрами
- 🗺️ Карта с геолокацией
- 🛡️ Индикатор надежности объявления (fraud score)
- 📊 Аналитика рынка и цен
- 🔔 Уведомления о новых объявлениях
- ⭐ Сохраненные поиски и избранное

### Для администраторов:
- 📈 Dashboard с метриками
- 🤖 Управление скрейперами
- ⚙️ Настройка правил детекции
- 👥 Модерация помеченных объявлений
- 📊 Отчеты и аналитика

## 🛠️ Технологический стек

### Backend:
- **Python**: FastAPI, Scrapy, TensorFlow/PyTorch, scikit-learn
- **Node.js**: Real-time services
- **Databases**: PostgreSQL, MongoDB, Elasticsearch, Redis
- **Message Queue**: Apache Kafka / RabbitMQ
- **ML/AI**: XGBoost, Neural Networks, MLflow

### Frontend:
- **Framework**: React / Next.js
- **UI**: TailwindCSS / Material-UI
- **Maps**: Mapbox / Google Maps
- **State**: Redux / Zustand

### Infrastructure:
- **Containerization**: Docker
- **Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana, ELK Stack

## 📋 Требования

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

## 🏁 Быстрый старт

### Docker (рекомендуется)

```bash
# Клонирование репозитория
git clone https://github.com/loudmantrade/RealEstatesAntiFraud.git
cd RealEstatesAntiFraud

# Запуск всех сервисов с Docker Compose
docker-compose up -d

# Проверка статуса
docker-compose ps

# API доступно по адресу
open http://localhost:8000/api/v1/docs
```

### Локальная разработка

```bash
# Установка зависимостей
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Запуск БД в Docker
docker-compose up -d postgres redis

# Запуск API
uvicorn core.api.main:app --reload --host 0.0.0.0 --port 8000
```

**📚 Подробная документация:** См. [docs/DOCKER.md](docs/DOCKER.md)

## 📁 Структура проекта

```
RealEstatesAntiFraud/
├── services/
│   ├── scraper/              # Сервис скрейпинга
│   ├── fraud-detection/      # ML сервис детекции фрода
│   ├── api/                  # REST/GraphQL API
│   ├── search/               # Поисковый сервис
│   ├── etl/                  # ETL pipeline
│   └── notifications/        # Сервис уведомлений
├── frontend/
│   ├── web/                  # Web приложение
│   └── admin/                # Admin dashboard
├── ml-models/                # ML модели и обучение
├── infrastructure/
│   ├── docker/               # Docker конфигурации
│   ├── kubernetes/           # K8s манифесты
│   └── terraform/            # Infrastructure as Code
├── docs/                     # Документация
├── tests/                    # Тесты
├── ARCHITECTURE.md           # Архитектура системы
└── README.md                 # Этот файл
```

## 🧪 Тестирование

Проект использует комплексную стратегию тестирования с автоматическими проверками в CI/CD pipeline.

### CI/CD Pipeline

GitHub Actions автоматически запускает тесты на каждый push и pull request:

- ✅ **Unit Tests** - быстрые тесты на Python 3.11, 3.12, 3.13
- ✅ **Integration Tests** - тесты с PostgreSQL на всех версиях Python
- ✅ **Linting** - black, isort, flake8
- ✅ **Type Checking** - mypy
- ✅ **Security Scan** - bandit
- ✅ **Coverage Reports** - автоматическая загрузка в Codecov

### Unit Tests
Быстрые тесты с in-memory SQLite:
```bash
# Запуск всех unit тестов
make test-unit

# Или напрямую через pytest
pytest tests/unit/ -v
```

### Integration Tests
Тесты с реальной PostgreSQL базой данных в Docker:

**Предварительные требования:**
- Docker и docker-compose установлены
- Порт 5433 свободен (или измените в `docker-compose.test.yml`)

**Запуск integration тестов:**
```bash
# Полный цикл (запуск DB → тесты → остановка DB)
make test-integration

# Или вручную:
# 1. Запустить тестовую БД
make test-integration-up

# 2. Запустить тесты
pytest tests/integration/ -v --cov=core

# 3. Остановить БД
make test-integration-down
```

**В CI/CD:**
Integration tests автоматически запускаются с PostgreSQL service container на каждый PR.

**Просмотр логов тестовой БД:**
```bash
make test-integration-logs
```

**Конфигурация:**
- Database URL: `postgresql://test_user:test_pass@localhost:5433/realestate_test`
- Настройки в файле `.env.test`
- Docker Compose: `docker-compose.test.yml`

### All Tests
```bash
# Запуск unit + integration тестов
make test-all

# Все тесты с coverage
make test-coverage
```

### Test Structure
```
tests/
├── unit/              # Юнит-тесты (in-memory SQLite)
│   ├── core/
│   │   └── test_plugin_manager.py
│   ├── test_dependency_graph.py
│   ├── test_manifest_schema.py
│   ├── test_manifest_validator.py
│   └── ...
└── integration/       # Интеграционные тесты (PostgreSQL)
    ├── conftest.py    # Fixtures (db_session, client)
    ├── test_listings_crud.py         # CRUD операции (5 тестов)
    ├── test_listings_pagination.py   # Пагинация (11 тестов)
    ├── test_listings_filters.py      # Фильтрация (15 тестов)
    └── test_listings_advanced.py     # Транзакции и целостность (13 тестов)
```

**Статистика тестов:**
- 44 integration tests - полное покрытие Listings API
- Все тесты проходят в CI на Python 3.11, 3.12, 3.13
- Покрытие кода доступно на [Codecov](https://codecov.io/gh/loudmantrade/RealEstatesAntiFraud)

### Troubleshooting

**Проблема: "Port 5433 is already in use"**
```bash
# Проверьте запущенные контейнеры
docker ps | grep 5433

# Остановите конфликтующие контейнеры
docker stop <container_id>

# Или измените порт в docker-compose.test.yml
```

**Проблема: "Database connection failed"**
```bash
# Убедитесь, что контейнер запущен и здоров
docker-compose -f docker-compose.test.yml ps

# Проверьте логи
docker-compose -f docker-compose.test.yml logs postgres-test

# Подождите 3-5 секунд для инициализации PostgreSQL
```

**Проблема: "Fixtures not found"**
```bash
# Убедитесь, что conftest.py существует
ls tests/integration/conftest.py

# Проверьте PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH
```

## 📊 ML Модели

### Детекция мошенничества

Система использует несколько моделей:

1. **Text Classifier** (XGBoost)
   - Анализ описаний объявлений
   - Обнаружение подозрительных паттернов

2. **Image Analysis** (CNN)
   - Детекция стоковых фотографий
   - Reverse image search
   - Обнаружение манипуляций с изображениями

3. **Behavioral Model** (Isolation Forest)
   - Анализ поведения продавцов
   - Обнаружение аномалий

### Обучение моделей

```bash
# Запуск pipeline обучения
python ml-models/train_fraud_detector.py

# Оценка модели
python ml-models/evaluate.py --model fraud_classifier_v1

# Deploy модели
python ml-models/deploy.py --model fraud_classifier_v1 --env production
```

## 🔒 Безопасность

- JWT authentication для API
- Rate limiting (100 req/min per IP)
- HTTPS only
- Input validation & sanitization
- GDPR compliance (анонимизация данных)
- Regular security audits

## 📈 Производительность

- API Response Time: < 200ms (p95)
- Search Response: < 100ms
- Uptime: > 99.9%
- Scraping Rate: 10,000+ listings/hour
- ML Inference: < 50ms per listing

## 🤝 Contributing

Мы приветствуем вклад в проект! См. [CONTRIBUTING.md](./CONTRIBUTING.md)

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

## 📝 Лицензия

Distributed under the MIT License. See `LICENSE` for more information.

## 👥 Команда

- Lead Developer: [Your Name]
- ML Engineer: TBD
- DevOps: TBD
- Frontend: TBD

## 📧 Контакты

- Email: contact@realestatesantifraud.com
- Telegram: @realestatesantifraud
- Website: https://realestatesantifraud.com

## 🗺️ Roadmap

### Q1 2024
- [x] Архитектура и дизайн системы
- [ ] MVP скрейпера (2-3 источника)
- [ ] Базовая детекция фрода (rule-based)
- [ ] Минимальный UI

### Q2 2024
- [ ] ML модель детекции фрода
- [ ] Расширение до 10+ источников
- [ ] Admin dashboard
- [ ] API v1

### Q3 2024
- [ ] Image analysis
- [ ] Real-time updates
- [ ] Mobile app
- [ ] Kubernetes deployment

### Q4 2024
- [ ] Advanced analytics
- [ ] Recommendation system
- [ ] Partner API
- [ ] White-label решение

## 💡 Вдохновение

Проект вдохновлен следующими сервисами:
- Zillow (США)
- Rightmove (UK)
- Immobilienscout24 (Germany)

---

⭐ Если проект полезен, поставьте звезду!
