# План разработки ядра системы RealEstatesAntiFraud

Документ описывает детальный поэтапный план разработки **Core System** (ядра) и связанных базовых подсистем. Содержит декомпозицию задач до уровня подзадач, статусы, зависимости, критерии готовности и приоритеты. Используется как рабочая основа для ведения разработки.


## 📊 Текущий статус проекта

**Версия:** 0.5 | **Дата обновления:** 30 ноября 2025  
**Фаза:** Phase A - Testing Infrastructure (высокий приоритет)

### ✅ Завершено

**Core Infrastructure:**
- 13 bootstrap задач выполнены (0.1-0.13)
- Core структура и базовые модули реализованы
- Plugin-based архитектура заложена (интерфейсы, manager)
- FastAPI приложение с CRUD endpoints
- PostgreSQL + Redis + RabbitMQ integration
- Configuration management system
- Messaging layer (queue + orchestrator)
- **42 GitHub Issues созданы** ([смотреть все](https://github.com/loudmantrade/RealEstatesAntiFraud/issues))
- Milestone "Phase A - Technical Foundation" создан

**Plugin System:**
- **Issue #1:** Plugin manifest specification v1.0 (58 tests) ✅
- **Issue #2:** Manifest validation with JSON Schema (31 tests) ✅
- **Issue #3:** Dynamic plugin discovery and loading (23 tests) ✅
- **Issue #4:** Hot reload for plugin updates (16 tests, 86% coverage) ✅

**Observability:**
- **Issue #19:** Structured JSON logging (20 tests, 97% coverage) ✅
- **Issue #20:** Request tracing with correlation IDs (29 tests, 100% coverage) ✅

**Testing Infrastructure (20 issues закрыто за последние 2 дня):**
- **Issue #83:** CI status badge and documentation ✅
- **Issue #93:** Integration tests re-enabled in CI ✅
- **Issue #103-109:** Messaging, config, plugin manager integration tests ✅
- **Issue #112:** Unified local test environment ✅
- **Issue #118-126:** Coverage improvements (plugins API, orchestrator, queue) ✅
- **Issue #132:** Database base coverage increased ✅
- **Issue #136:** ListingFactory with Faker (25 tests, 100%) ✅
- **Issue #137:** EventFactory for messaging (33 tests, 100%) ✅

**Current PR:**
- **PR #146:** ListingBuilder with fluent API (44 tests, all passing) 🔄
  - Configured for Portugal 🇵🇹 (priority #1) and Ukraine 🇺🇦 (priority #2) markets
  - EUR currency, Lisboa default city, pt_PT locale
  - All 20 CI checks passing

### 🎯 Текущая работа: Issue #110 - Test Data Generators & Factories

**Progress:** 2/6 задач завершено (33%)
- ✅ **Issue #136:** ListingFactory - базовая фабрика с Faker
- ✅ **Issue #137:** EventFactory - фабрика для messaging events
- 🔄 **Issue #138:** ListingBuilder - fluent API builder (PR #146 готов к merge)
- ⏳ **Issue #139:** Specialized factory methods (fraud scenarios, edge cases)
- ⏳ **Issue #140:** Pytest fixtures для всех фабрик
- ⏳ **Issue #141:** DatabaseSeeder для массовой генерации данных

**Целевые рынки проекта:**
- 🇵🇹 **Португалия** (приоритет #1): Idealista, Imovirtual, OLX Portugal
- 🇺🇦 **Украина** (приоритет #2): OLX Ukraine, DOM.RIA, Lun
- 📱 **Планируется:** Facebook Marketplace (source plugin)
- 🏢 **Планируется:** Крупные риелторы (IAT и другие, через плагины)

### 📈 Метрики качества
- **Code Coverage:** 86%+ (core modules)
- **Tests Passing:** 100% (все PR проходят CI)
- **Integration Tests:** Re-enabled в CI, PostgreSQL + Redis + RabbitMQ
- **Test Data Infrastructure:** Factories для Listing, Event; Builder pattern

---
## Легенда статусов
- ✅ **Завершено** (Done)
- 🚧 **В работе** (In Progress)
- ⏳ **Запланировано** (Planned)
- ❌ **Отложено** (Deferred)

Доп. атрибуты в задачах:
- `P` – Приоритет (1 = критично, 2 = важно, 3 = желательно)
- `Deps` – Явные зависимости (ID задач)
- `Owner` – Ответственный (заполняется позже)

## 0. Выполненные начальные задачи (Bootstrap)
| ID | Задача | Статус | Описание | Что выполнено | Критерий готовности |
|----|--------|--------|----------|---------------|---------------------|
| 0.1 | Структура каталога `core/` | ✅ | Создана базовая иерархия директорий | Созданы: `core/`, `core/api/`, `core/api/routes/`, `core/interfaces/`, `core/models/`, `core/utils/`, `tests/unit/core/` | Директории существуют в репо |
| 0.2 | `requirements.txt` + dev зависимости | ✅ | Добавлены runtime и dev пакеты | **Runtime**: fastapi 0.115.5, uvicorn 0.32.0, pydantic 2.9.2. **Dev**: pytest 8.3.3, pytest-cov 6.0.0, black 24.10.0, flake8 7.1.1, isort 5.13.2, mypy 1.14.0, bandit 1.8.0, safety 3.2.10 | Установка проходит без ошибок |
| 0.3 | Pydantic модели плагина (`plugin.py`) | ✅ | Metadata и registration request | Файл: `core/models/plugin.py`. Классы: `PluginMetadata` (id, name, version, type, enabled, config), `PluginRegistrationRequest` (metadata) | Импортируется, тестируется |
| 0.4 | Pydantic модели UDM (минимальный срез) | ✅ | Базовые поля Listing | Файл: `core/models/udm.py`. Модели: `SourceInfo`, `Price`, `Location`, `Media`, `Listing` (id, source, type, location, price, title, description, media, created_at) | API принимает модель |
| 0.5 | Интерфейсы плагинов (Source/Processing/Detection/Search/Display) | ✅ | Абстрактные классы добавлены | Файлы в `core/interfaces/`: `source_plugin.py` (SourcePlugin с методами scrape, validate), `processing_plugin.py` (process, priority), `detection_plugin.py` (analyze, weight), `search_plugin.py` (index, search), `display_plugin.py` (format_listing) | Классы доступны для имплементаций |
| 0.6 | Plugin Manager (in-memory) | ✅ | Регистрация, enable/disable/remove | Файл: `core/plugin_manager.py`. Класс `PluginManager` с методами: `register()`, `get()`, `list_plugins()`, `enable()`, `disable()`, `remove()`. Thread-safe (Lock). Singleton instance `plugin_manager` | Юнит тест пройден |
| 0.7 | FastAPI приложение (`core/api/main.py`) | ✅ | CORS + health + подключение роутеров | FastAPI app с CORS middleware, `/health` endpoint, подключены роуты из `plugins.py` и `listings.py` с префиксом `/api` | Запуск возвращает 200 /health |
| 0.8 | Роуты `/api/plugins` | ✅ | CRUD операций над плагинами | Файл: `core/api/routes/plugins.py`. Endpoints: POST `/register`, GET `/`, GET `/{plugin_id}`, PUT `/{plugin_id}/enable`, PUT `/{plugin_id}/disable`, DELETE `/{plugin_id}` | curl ответы валидны |
| 0.9 | Роуты `/api/listings` (in-memory CRUD) | ✅ | Создание/получение/удаление | Файл: `core/api/routes/listings.py`. In-memory хранилище (dict). Endpoints: POST `/`, GET `/`, GET `/{listing_id}`, DELETE `/{listing_id}` | Тестовое объявление создаётся |
| 0.10 | Юнит тесты plugin manager | ✅ | Регистрация/enable/disable/remove | Файл: `tests/unit/core/test_plugin_manager.py`. Тесты: `test_plugin_lifecycle` (register→get→enable→disable→remove). Coverage: plugin_manager.py покрыт основными сценариями. Результат: 1 passed in 0.24s | Все тесты зелёные |
| 0.11 | Документация плана разработки | ✅ | Детальный план с задачами, фазами, спринтами | Файл: `docs/CORE_DEVELOPMENT_PLAN.md`. Содержит 21 секцию: задачи по модулям (1-13), риски, метрики, дорожную карту, критерии готовности MVP, предложения спринтов | Документ создан и структурирован |
| 0.12 | Автоматизация создания GitHub Issues | ✅ | Скрипт для генерации issues из плана | Файлы: `scripts/create_github_issues.py` (основной), `scripts/run_create_issues.py` (интерактивный wrapper), `docs/GITHUB_ISSUES_SETUP.md`. Создано 42 issues, 14 labels, milestone "Phase A" | Скрипт выполнен успешно |
| 0.13 | Makefile для автоматизации задач | ✅ | Команды для dev, test, build, deploy | Файл: `Makefile`. Targets: setup, dev, test, lint, build, deploy, plugin operations. Документация использования в комментариях | Make targets работают |

## 1. Архитектурные расширения ядра
| ID | Задача | Статус | P | Deps | Критерии готовности |
|----|--------|--------|---|------|---------------------|
| 1.1 | Проектирование протокола плагинов (manifest spec v1) | ✅ | 1 | 0.x | Документ `PLUGIN_SPEC.md` утверждён |
| 1.2 | Валидация manifest (plugin.yaml schema JSON) | ✅ | 1 | 1.1 | JSON Schema + функция validate_manifest |
| 1.3 | Загрузка плагинов с диска (dynamic discovery) | ✅ | 1 | 1.2 | Плагин появляется после drop в каталог |
| 1.4 | Горячая перезагрузка (reload) | ✅ | 2 | 1.3 | API endpoint /reload + обновление метаданных |
| 1.5 | Модель зависимостей плагинов (dependency graph) | ✅ | 2 | 1.2 | Вычисляется DAG, циклы детектируются |
| 1.6 | Версионирование совместимости (semver constraints) | ✅ | 2 | 1.5 | Отказ при несовместимых версиях |
| 1.7 | Изоляция плагинов (optional sandbox exec) | ❌ | 3 | 1.3 | Контейнеризация / subprocess стратегия описана |
| 1.8 | Регистрация событий (plugin lifecycle hooks) | ⏳ | 2 | 1.3 | on_enable/on_disable/on_remove вызываются |
| 1.9 | Persistence реестра (PostgreSQL таблица plugins) | ⏳ | 1 | 0.6 | Перезапуск сохраняет состояние enabled |

## 2. Конфигурация и управление параметрами
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|----------|
| 2.1 | Единая схема конфигов (core + plugins) | ✅ | 1 | 1.1 | `config/` + `ConfigManager` класс |
| 2.2 | Поддержка env overrides | ✅ | 1 | 2.1 | Переменные ENV перекрывают YAML |
| 2.3 | Secure secrets storage (dotenv + vault placeholder) | ⏳ | 2 | 2.1 | Секреты не логируются, чит. через API |
| 2.4 | Live refresh конфигурации (watch) | ❌ | 3 | 2.1 | Изменение файла перезагружает значения |

## 3. Система логирования и наблюдаемости
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|----------|
| 3.1 | Стандартизированный logger (структурированный JSON) | ✅ | 1 | 0.x | logger доступен через `core.utils.logging` |
| 3.2 | Корреляционные ID (trace & request id middleware) | ✅ | 1 | 3.1 | Каждый запрос включает trace_id |
| 3.3 | Метрики Prometheus (плагины/ошибки/latency) | ⏳ | 2 | 3.1 | /metrics endpoint показывает core метрики |
| 3.4 | OpenTelemetry базовая интеграция (auto-instrumentation) | ⏳ | 1 | 3.2 | Трейсы FastAPI/PostgreSQL/HTTP видны в Jaeger |
| 3.5 | OpenTelemetry custom spans (плагины, fraud detection) | ⏳ | 2 | 3.4 | Кастомные операции трейсятся |
| 3.6 | OpenTelemetry metrics (custom instrumentation) | ⏳ | 2 | 3.4 | Custom метрики экспортируются через OTLP |
| 3.7 | OpenTelemetry logs integration (unified correlation) | ⏳ | 2 | 3.4 | Логи содержат trace_id/span_id из context |
| 3.8 | OpenTelemetry Collector deployment | ⏳ | 2 | 3.4 | Collector собирает и роутит telemetry |
| 3.9 | Алерты базовые (ошибки > threshold) | ❌ | 3 | 3.3 | Документ threshold'ов + mock alert handler |

## 4. Хранилище и персистентность
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|-----------|
| 4.1 | Схема PostgreSQL для listings (v1) | ✅ | 1 | 0.9 | Таблица создана миграцией |
| 4.2 | Миграции (Alembic настройка) | ✅ | 1 | 4.1 | `alembic upgrade head` успешно |
| 4.3 | Repository слой (CRUD + pagination) | ✅ | 1 | 4.2 | Юнит тесты на методы |
| 4.4 | Индексы (platform, price, geo) | ⏳ | 2 | 4.1 | EXPLAIN показывает корректные планы |
| 4.5 | Кэширование read-hot данных (Redis) | ❌ | 2 | 4.3 | Хит > 70% на популярных ключах |
| 4.6 | Архивация устаревших объявлений | ❌ | 3 | 4.3 | Механизм move в архивную таблицу |

## 5. ETL / Processing Pipeline интеграция
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|-----------|
| 5.1 | Абстракция очереди (Kafka/RabbitMQ interface) | ✅ | 1 | 1.3 | Unified Producer/Consumer классы |
| 5.2 | Формат сообщения (raw_listing_event) | ✅ | 1 | 5.1 | JSON Schema описана + тест сериализации |
| 5.3 | Оркестратор последовательности Processing Plugins | ✅ | 1 | 5.2 | Выполняет плагины по priority |
| 5.4 | Параллельное выполнение независимых плагинов | ❌ | 2 | 5.3 | Async/Futures, метрики concurrency |
| 5.5 | Dead-letter queue для ошибок обработки | ❌ | 2 | 5.1 | Сообщения падений сохраняются |
| 5.6 | Реестр состояний обработки (processing_log) | ⏳ | 2 | 5.3 | Запись шага с timestamp в listing |

## 6. Fraud Detection интеграция
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|-----------|
| 6.1 | Интерфейс RiskScoringOrchestrator | ✅ | 1 | 0.6 | Класс orchestrator с run(listing) |
| 6.2 | Подключение detection plugins (метаданные) | ✅ | 1 | 6.1 | Список активных detection plugins |
| 6.3 | Агрегация сигналов и формула fraud_score | ✅ | 1 | 6.2 | Вычисление соответствует спецификации |
| 6.4 | Кеширование результатов скоринга | ❌ | 2 | 6.3 | Повторный вызов < 10ms |
| 6.5 | Стратегия re-score (по изменению данных) | ❌ | 2 | 6.3 | Триггеры обновляют score |
| 6.6 | Лог причин (explainability JSON) | ❌ | 2 | 6.3 | `listing.fraud_explain` содержит детали |

## 7. Search & Indexing (core интеграция)
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|----------|
| 7.1 | Интерфейс IndexManager (routing к search plugins) | ⏳ | 1 | 0.6 | Класс index(listing)/search(query) |
| 7.2 | Событие индексации после финализации обработки | ⏳ | 1 | 5.3 | После pipeline → index вызов |
| 7.3 | Массовая реиндексация (batch API) | ❌ | 2 | 7.2 | Endpoint запускает batch job |
| 7.4 | Стратегия обновления при изменении полей | ❌ | 2 | 7.2 | Изменения → partial update в search |
| 7.5 | Метрики качества поиска (latency, hit ratio) | ❌ | 3 | 7.2 | Метрики доступны /metrics |

## 8. API улучшения (Core REST)
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|-----------|
| 8.1 | Версионирование API (v1 prefix) | ✅ | 1 | 0.7 | Все роуты под `/api/v1/` |
| 8.2 | Response envelope (стандарт формата) | ⏳ | 2 | 8.1 | `{data:..., meta:...}` во всех ответах |
| 8.3 | Глобальная обработка ошибок | ⏳ | 2 | 8.1 | Единый JSON для исключений |
| 8.4 | Пагинация и фильтры для `/listings` | ✅ | 1 | 4.3 | limit/offset/filters работают |
| 8.5 | Аутентификация (JWT middleware) | ❌ | 2 | 8.1 | `/protected` требует токен |
| 8.6 | Rate Limiting (IP + user) | ❌ | 2 | 8.5 | Перегруз → 429 |
| 8.7 | OpenAPI расширения (tags, examples) | ⏳ | 3 | 8.1 | Документация отображает примеры |
| 8.8 | GraphQL шлюз (опционально) | ❌ | 3 | 8.1 | Базовый schema для listings |

## 9. Безопасность
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|----------|
| 9.1 | Input validation audit (все entrypoints) | ⏳ | 1 | 8.1 | Отчет без критичных пробелов |
| 9.2 | SQL Injection защита (ORM parametrization) | ⏳ | 1 | 4.3 | Нет конкатенации сырого SQL |
| 9.3 | Лимит размера запросов (body size) | ❌ | 2 | 8.1 | > лимита → 413 |
| 9.4 | X-Rate trace headers (propagation) | ❌ | 2 | 3.2 | Заголовки присутствуют |
| 9.5 | Скан зависимостей (safety/bandit CI) | ⏳ | 2 | 0.2 | Pipeline краснеет при угрозах |
| 9.6 | Документ политика секретов | ⏳ | 3 | 2.3 | `SECURITY_SECRETS.md` создан |

## 10. Тестирование и качество
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|-----------|
| 10.1 | Расширение unit тестов (>=70% coverage ядра) | ✅ | 1 | 0.x | Coverage report >=70% (86%+ достигнуто) |
| 10.2 | Интеграционные тесты pipeline (mock queue) | ✅ | 1 | 5.3 | end-to-end проходит |
| 10.3 | Тесты на ошибки (negative cases) | ⏳ | 2 | 10.1 | Каталог error scenarios |
| 10.4 | Нагрузочное тестирование API (baseline) | ❌ | 2 | 8.4 | Отчет latency p95 < целевого |
| 10.5 | Security tests (fuzz простых входов) | ❌ | 3 | 9.x | Fuzz проходит без критичных падений |
| 10.6 | Regression тест набор (locking) | ❌ | 3 | 10.1 | Стабильный пакет сценариев |

## 11. CI/CD
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|-----------|
| 11.1 | GitHub Actions базовый CI (tests + lint) | ✅ | 1 | 10.1 | workflow ci.yml зеленый |
| 11.2 | Build Docker image core | ✅ | 1 | 11.1 | Имидж собирается без ошибок |
| 11.3 | Скан уязвимостей образа (Trivy) | ❌ | 2 | 11.2 | Нет HIGH/CRITICAL в отчете |
| 11.4 | Авто-тег релизов (semver) | ❌ | 2 | 11.2 | push tag → release notes |
| 11.5 | CD на staging (manual approval) | ❌ | 3 | 11.2 | job deploy-staging успешен |
| 11.6 | SBOM генерация | ❌ | 3 | 11.2 | Артефакт sbom.json в релизе |

## 12. Performance & Scalability
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|----------|
| 12.1 | Профилирование hotspot’ов (cProfile) | ❌ | 2 | 8.x | Отчет с приоритетами оптимизации |
| 12.2 | Асинхронность части pipeline (I/O bound) | ❌ | 2 | 5.3 | Throughput увеличен >30% |
| 12.3 | Батч вставка listings | ❌ | 2 | 4.3 | Вставка 1000 записей < целевого времени |
| 12.4 | Rate limiter оптимизация (memory usage) | ❌ | 3 | 8.6 | < целевого footprint |
| 12.5 | Горизонтальное масштабирование plugin manager | ❌ | 3 | 1.9 | Кластерная синхронизация состояния |

## 13. Документация
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|----------|
| 13.1 | API docs расширение примеров | ⏳ | 2 | 8.7 | Примеры для ключевых эндпоинтов |
| 13.2 | Developer Guide ядра | ⏳ | 2 | 1.x | `CORE_DEVELOPER_GUIDE.md` создан |
| 13.3 | Operations Guide (deploy, monitoring) | ❌ | 3 | 11.x | Описаны процедуры восстановления |
| 13.4 | Обновление Architecture при изменениях | 🚧 | 2 | ongoing | История версий в ARCHITECTURE.md |
| 13.5 | FAQ для плагин-авторов | ⏳ | 2 | 1.1 | Раздел FAQ в PLUGIN_DEVELOPMENT.md |

## 14. Testing Infrastructure & Data Generators
| ID | Задача | Статус | P | Deps | Критерии |
|----|--------|--------|---|------|----------|
| 14.1 | Integration tests infrastructure setup | ✅ | 1 | 4.1 | Docker Compose тестовая БД, conftest.py fixtures |
| 14.2 | Integration tests для Listings API | ✅ | 1 | 14.1 | CRUD, pagination, filters, concurrent access tests |
| 14.3 | Integration tests в CI (GitHub Actions) | ✅ | 1 | 14.2 | PostgreSQL service в workflow, автоматический запуск |
| 14.4 | Redis test infrastructure | ✅ | 1 | 14.1 | Redis в docker-compose.test.yml, fixtures |
| 14.5 | Plugin test fixtures infrastructure | ✅ | 1 | 1.3 | Mock plugins, test discovery, lifecycle fixtures |
| 14.6 | Unified local test environment | ✅ | 1 | 14.1 | Makefile targets, документация setup |
| 14.7 | Messaging layer integration tests | ✅ | 1 | 5.1 | Queue + orchestrator end-to-end tests |
| 14.8 | Configuration manager integration tests | ✅ | 1 | 2.1 | Config loading, env overrides, validation tests |
| 14.9 | Plugin manager integration tests | ✅ | 1 | 1.3 | Registration, enable/disable, lifecycle tests |
| 14.10 | Coverage improvements (orchestrator, API) | ✅ | 2 | 14.1 | 80%+ coverage для orchestrator, plugins API |
| 14.11 | ListingFactory с Faker | ✅ | 2 | 14.1 | Базовая фабрика, 25 тестов, 100% coverage |
| 14.12 | EventFactory для messaging | ✅ | 2 | 5.1 | Фабрика событий, 33 теста, 100% coverage |
| 14.13 | ListingBuilder с fluent API | 🔄 | 2 | 14.11 | Builder pattern, 44 теста (PR #146) |
| 14.14 | Specialized factory methods | ⏳ | 2 | 14.13 | Fraud scenarios, edge cases, market-specific |
| 14.15 | Pytest fixtures для factories | ⏳ | 2 | 14.13 | Reusable fixtures для всех тестов |
| 14.16 | DatabaseSeeder для bulk data | ⏳ | 2 | 14.13 | Массовая генерация тестовых данных |
| 14.17 | Factory documentation | ⏳ | 3 | 14.13 | Usage examples, best practices |
| 14.18 | Refactor tests to use factories | ⏳ | 3 | 14.15 | Замена старых fixtures на factories |

## 15. Риски & Митигация (ядро)
| Риск | Описание | Митигация | Триггер действия |
|------|----------|-----------|------------------|
| R1 | Рост сложности зависимостей плагинов | Визуализация DAG + CI проверка циклов | Ошибка сборки при цикле |
| R2 | Неуправляемые версии плагинов | Semver + registry lockfile | Конфликт версий при загрузке |
| R3 | Производительность при массовом скрейпе | Батч + асинхронность + профилирование | p95 latency превышает SLA |
| R4 | Потери данных при сбое очереди | DLQ + периодические ретраи | >N ошибок подряд |
| R5 | Неполная валидация входных данных | Автоматизированные тесты схем | Ошибки в проде по валидности |

## 16. Метрики ядра
| Метрика | Цель | Комментарий |
|---------|------|-------------|
| Время регистрации плагина | < 200ms | In-memory + validation |
| Время обработки listing (pipeline) | < 2s p95 | От сырого до persistence |
| Fraud scoring latency | < 100ms | После окончания обработки |
| API /listings p95 | < 150ms | Без кэша |
| Ошибки 5xx доля | < 0.5% | На стабильной нагрузке |
| Coverage ядра | ≥ 70% (этап 1), ≥ 85% (этап 2) | Постепенно увеличиваем |

## 17. Дорожная карта по фазам (ядро)
### Фаза A (Технический фундамент)
- Завершить: 1.1–1.3, 2.1–2.2, 3.1–3.2, 4.1–4.3, 5.1–5.3, 8.1, 11.1–11.2, 13.1–13.2

### Фаза B (Функциональное насыщение + Observability)
- Задачи: 1.5–1.6, 5.6, 6.1–6.3, 7.1–7.2, 8.4, 9.1–9.2, 10.2–10.3, 3.3–3.5

### Фаза C (Надёжность и масштабируемость + Advanced Observability)
- Задачи: 4.4–4.5, 5.4–5.5, 6.4–6.6, 7.3–7.5, 12.1–12.3, 11.3–11.4, 3.6–3.8, 9.5

### Фаза D (Продвинутая безопасность и аналитика)
- Задачи: 8.5–8.6, 9.3–9.6, 10.4–10.6, 11.5–11.6, 3.9, 12.4–12.5, 13.3–13.5

## 18. Зависимости высокого уровня
```
Plugin Manifest Spec → Validation → Dynamic Loading → Dependency Graph → Version Compatibility
Queue Abstraction → Raw Event Format → Processing Orchestrator → Detection Orchestrator → Indexing
Persistence (Listings) → Repository → API Pagination → Search Routing
Logging Base → Trace IDs → OpenTelemetry (base) → Custom Spans → Custom Metrics → Logs Integration → OTel Collector → Alerts
Security Baseline → Auth → Rate Limiting → Input Validation Audit
CI (tests) → Docker Build → Vulnerability Scan → Release Tagging → Staging Deploy
```

## 19. Критерии готовности ядра (MVP Core Definition)
1. Dynamic plugin discovery & registration (1.3) работает
2. Manifest validation (1.2) и отказ при ошибке
3. Базовый ETL orchestrator (5.3) с минимумом 2 processing plugins
4. Persistence в PostgreSQL + CRUD через API (4.1–4.3, 8.4)
5. Риск скоринг базовый (6.1–6.3) интегрирован
6. IndexManager вызывает Elasticsearch plugin (7.1–7.2)
7. Логирование + trace id (3.1–3.2)
8. CI тесты и линт (11.1) зелёные
9. Coverage ≥ 70% (10.1)
10. Документация обновлена (13.1–13.2)

## 20. Следующие ближайшие шаги (Sprint Backlog Предложение)
| Sprint | Предлагаемые задачи | GitHub Issues |
|--------|---------------------|---------------|
| S1 | 1.1, 1.2, 1.3, 2.1, 2.2, 4.1, 4.2, 4.3, 5.1, 5.2 | [#1](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/1), [#2](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/2), [#3](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/3), [#16](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/16), [#17](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/17), [#22](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/22), [#23](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/23), [#24](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/24), [#26](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/26), [#27](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/27) |
| S2 | 5.3, 6.1, 6.2, 6.3, 8.1, 8.4, 11.1, 11.2, 3.1, 3.2 | [#28](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/28), [#30](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/30), [#31](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/31), [#32](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/32), [#35](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/35), [#38](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/38), [#12](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/12), [#13](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/13), [#19](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/19), [#20](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/20) |
| S3 | 7.1, 7.2, 10.1, 3.2, 3.3 | [#33](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/33), [#34](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/34), [#9](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/9), [#20](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/20), [#21](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/21) |
| S4 | 1.5, 1.6, 5.6, 9.1, 9.2, 13.1, 13.2 | [#5](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/5), [#6](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/6), [#29](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/29), [#40](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/40), [#41](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/41), [#14](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/14), [#15](https://github.com/loudmantrade/RealEstatesAntiFraud/issues/15) |

**Быстрые ссылки:**
- 📋 Все Issues: https://github.com/loudmantrade/RealEstatesAntiFraud/issues
- 🎯 Milestone "Phase A": https://github.com/loudmantrade/RealEstatesAntiFraud/milestone/1
- 📊 Проект: _создать GitHub Project Board для визуализации_ (рекомендуется)

## 21. Формат обновления статусов
- Обновление этого файла: pull request с пометкой `[core-plan-update]`
- Изменения: только статус / добавление владельца / уточнение критериев
- История версий: добавить секцию Changelog ниже

## 22. Changelog (история изменений плана)
| Дата | Версия | Изменения |
|------|--------|-----------||
| 2025-11-25 | 0.1 | Инициализация документа, добавлены выполненные задачи bootstrap |
| 2025-11-25 | 0.2 | Расширено описание выполненных задач 0.1-0.13 с деталями реализации. Добавлены: 0.11 (документация плана), 0.12 (скрипты GitHub Issues), 0.13 (Makefile). Создано 42 GitHub Issues с labels и milestone |
| 2024-12-26 | 0.3 | Завершён Sprint 1 (4/10 задач, 40%). Задачи 1.1-1.4 выполнены: Issue #1 (manifest spec, 58 тестов), Issue #2 (validation, 31 тест), Issue #3 (dynamic loading, 23 теста), Issue #4 (hot reload, 16 тестов). Итого 119/129 тестов проходят, покрытие 86%. Commit 315f07d. |
| 2025-11-28 | 0.4 | Завершены observability issues: #19 (Structured JSON logging, 20 тестов, 97% покрытие), #20 (Request tracing, 29 тестов, 100% context coverage). Задачи 3.1-3.2 выполнены. Добавлен OpenTelemetry roadmap: 5 новых подзадач (3.4-3.8) для полной observability интеграции. Обновлена архитектурная диаграмма с OTel Collector. |
| 2025-11-30 | 0.5 | **Массовое завершение testing infrastructure (20 issues за 2 дня).** Закрыты: #83, #93, #103-109, #112, #118-126, #132, #136-137. Integration tests re-enabled. ListingFactory (25 tests), EventFactory (33 tests) созданы. PR #146: ListingBuilder (44 tests) с fluent API готов к merge. **Обновлены целевые рынки:** 🇵🇹 Portugal (priority #1), 🇺🇦 Ukraine (priority #2). Планируется: Facebook Marketplace, IAT plugins. Issue #110 progress: 2/6 задач. Coverage: 86%+. |
| 2025-11-30 | 0.6 | **Синхронизация плана с GitHub Issues.** Обновлены статусы секций 1-13: отмечены завершённые задачи (#5-6, #16-17, #22-24, #26-28, #30-32, #35, #38, #9, #12-13). **Добавлена новая секция 14: Testing Infrastructure** - отражает 20+ issues (#61-93, #103-143) по testing infrastructure, которые не были покрыты в оригинальном плане. Включает: integration tests setup, factories (Listing, Event), Builder pattern, pytest fixtures, DatabaseSeeder. Перенумерованы секции 14→15, 15→16, 16→17, 17→18, 18→19, 19→20, 20→21, 21→22. |

---
**Примечание:** Задачи помеченные ❌ (Deferred) не входят в ближайшие фазы и могут быть возвращены при появлении ресурсов.
