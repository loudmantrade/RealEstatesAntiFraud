# RealEstatesAntiFraud

Интеллектуальный аггрегатор объявлений о недвижимости с системой автоматической детекции мошенничества.

## 🎯 Цель проекта

Создание надежной платформы для поиска недвижимости, которая:
- Собирает объявления с популярных досок объявлений
- Автоматически выявляет мошеннические объявления
- Предоставляет удобный поиск и фильтрацию
- Защищает пользователей от fraud

## 🏗️ Архитектура

Проект построен на микросервисной архитектуре. Подробное описание см. в [ARCHITECTURE.md](./ARCHITECTURE.md)

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

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- Kubernetes (для production)
- PostgreSQL 14+
- Elasticsearch 8+
- Redis 7+
- MongoDB 6+

## 🏁 Быстрый старт

```bash
# Клонирование репозитория
git clone https://github.com/yourusername/RealEstatesAntiFraud.git
cd RealEstatesAntiFraud

# Запуск с Docker Compose (для разработки)
docker-compose up -d

# Установка зависимостей Python
pip install -r requirements.txt

# Установка зависимостей Node.js
npm install

# Запуск миграций
python manage.py migrate

# Запуск в режиме разработки
python manage.py runserver
```

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

```bash
# Unit тесты
pytest tests/unit

# Integration тесты
pytest tests/integration

# E2E тесты
npm run test:e2e

# Coverage report
pytest --cov=services --cov-report=html
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
