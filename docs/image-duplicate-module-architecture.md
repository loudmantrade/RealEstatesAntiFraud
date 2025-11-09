# Image Duplicate Detection Module — Architecture Overview

## 🎯 Цель
Модуль определяет использование одинаковых или схожих изображений в объявлениях (например, при повторной публикации, переклейке объявлений или мошенничестве).  
Он устойчив к watermark, изменению размера, отражению, обрезке, изменению яркости и контраста.

---

## 🧩 Общая схема взаимодействия

```mermaid
sequenceDiagram
    participant Portal as "Ad Portal Backend"
    participant IngestAPI as "Image Duplicate API"
    participant Queue as "Task Queue (Celery/RabbitMQ)"
    participant Worker as "Image Worker"
    participant VectorDB as "Faiss / Milvus"
    participant Verifier as "Verification Worker"
    participant Postgres as "Results DB"
    participant UI as "Admin UI / Portal"

    Portal ->> IngestAPI: POST /api/v1/image/ingest (ad_id, image_urls)
    IngestAPI ->> Queue: enqueue(download_image, ad_id, urls)
    Queue ->> Worker: start(download_image)
    Worker ->> ExternalStorage: GET image
    Worker ->> Worker: preprocess (resize, normalize)
    Worker ->> Worker: compute pHash + CLIP embedding
    Worker ->> VectorDB: add embedding to index
    Worker ->> Postgres: insert metadata (ad_id, hash, url)
    Worker ->> Queue: enqueue(search_duplicates)
    Queue ->> Worker: start(search_duplicates)
    Worker ->> VectorDB: query top-K nearest embeddings
    Worker ->> Verifier: verify_candidates (SIFT, SSIM, LPIPS)
    Verifier ->> Postgres: insert duplicate relations
    Verifier ->> Queue: enqueue(cluster_duplicates)
    Queue ->> Worker: cluster_duplicates()
    Worker ->> Postgres: create/update cluster entry
    Postgres ->> UI: provide REST/GraphQL for clusters
    UI ->> Postgres: GET /clusters, /duplicates/{ad_id}
    UI ->> Portal: display duplicates summary
```

---

## ⚙️ Компоненты и ответственность

| Компонент | Тип | Функции | Технологии |
|------------|------|----------|-------------|
| **Ingest API** | Deployment | REST/gRPC endpoint для приёма изображений и метаданных | FastAPI / Flask |
| **Task Queue** | StatefulSet | Диспетчеризация задач загрузки и анализа | Redis / RabbitMQ + Celery |
| **Image Worker** | Deployment | Скачивание, нормализация, вычисление pHash + CLIP-эмбеддингов | Python, OpenCV, Torch, imagehash |
| **Vector Store** | StatefulSet | Хранение и поиск векторов изображений | Faiss / Milvus / Qdrant |
| **Verifier Worker** | Deployment | Верификация похожих изображений (SIFT + RANSAC + SSIM/LPIPS) | OpenCV, scikit-image |
| **PostgreSQL (pgvector)** | StatefulSet | Метаданные, связи дубликатов, кластеры | PostgreSQL + pgvector |
| **Admin UI** | Deployment | Просмотр кластеров и отчётов | Streamlit / React / Vue |
| **Storage (S3/minio)** | External | Сохранение оригиналов изображений и thumbnail | MinIO / AWS S3 |

---

## 📦 Схема данных (PostgreSQL)

```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    ad_id BIGINT,
    source VARCHAR(100),
    url TEXT,
    phash BIGINT,
    embedding VECTOR(512),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE duplicates (
    id SERIAL PRIMARY KEY,
    image_id INT REFERENCES images(id),
    duplicate_id INT REFERENCES images(id),
    similarity FLOAT,
    verified BOOLEAN DEFAULT FALSE,
    method VARCHAR(20),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE duplicate_clusters (
    id SERIAL PRIMARY KEY,
    cluster_hash VARCHAR(64),
    image_ids INT[],
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT now()
);
```

---

## 🚀 Pipeline обработки

1. **Ингест**  
   - API получает `ad_id`, `source`, `image_urls`.  
   - Добавляет задачу `download_image` в очередь.

2. **Image Worker**  
   - Скачивает изображение.  
   - Вычисляет `pHash`, `CLIP embedding`.  
   - Сохраняет метаданные и добавляет эмбеддинг в векторный индекс.

3. **Search Duplicates**  
   - Выполняет ANN-поиск по Faiss/Milvus (top-K ближайших).  
   - Передаёт кандидатов на верификацию.

4. **Verification**  
   - Использует SIFT + RANSAC + SSIM для подтверждения.  
   - Записывает связи (image_id ↔ duplicate_id).

5. **Clustering**  
   - Объединяет найденные пары в кластеры.  
   - Сохраняет в таблицу `duplicate_clusters`.

6. **UI / Report**  
   - REST API и админ-панель отображают кластеры и метаданные.

---

## 🧠 Методы и пороги

| Метрика | Метод | Типичный порог |
|----------|--------|----------------|
| CLIP cosine similarity | Embedding (512-d) | > 0.35 |
| pHash Hamming distance | Perceptual hash | < 15 |
| SIFT inliers | Геометрическое совпадение | > 30 |
| SSIM | Перцептивное сходство | > 0.8 |

---

## ☸️ Kubernetes Deployment Layout

```
┌───────────────────────────────┐
│           Ingress             │
│     (nginx / traefik)         │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│ image-dup-api (FastAPI)       │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│  Redis / RabbitMQ (broker)    │
└───────┬──────────────┬────────┘
        │              │
        ▼              ▼
┌─────────────┐   ┌──────────────┐
│ image-worker│   │verifier-worker│
└─────┬───────┘   └──────┬───────┘
      │                  │
      ▼                  ▼
┌──────────────┐   ┌──────────────┐
│ Faiss/Milvus │   │ PostgreSQL   │
└──────┬────────┘   └─────┬────────┘
       │                  │
       ▼                  ▼
┌───────────────────────────────┐
│  Admin UI (Streamlit/React)   │
└───────────────────────────────┘
```

---

## ⚙️ Конфигурация (ConfigMap / Secrets)

```yaml
VECTOR_BACKEND: faiss
FAISS_INDEX_PATH: /data/faiss/index.ivf
MODEL_PATH: /models/clip-vit-b32
SIMILARITY_THRESHOLD: 0.35
DB_URL: postgresql://user:pass@postgres:5432/duplicates
BROKER_URL: redis://redis:6379/0
STORAGE_URL: s3://images/
```

---

## 📊 Мониторинг (Prometheus metrics)

| Метрика | Источник | Назначение |
|----------|-----------|------------|
| `dup_embeddings_processed_total` | image-worker | количество эмбеддингов |
| `faiss_query_latency_ms` | image-worker | время поиска ANN |
| `duplicates_found_total` | verifier-worker | количество совпадений |
| `queue_backlog_size` | Celery/Redis | нагрузка очередей |
| `api_ingest_requests_total` | image-dup-api | запросы к API |

---

## 🧰 Масштабирование

- `image-worker` и `verifier-worker` масштабируются горизонтально через HPA.  
- Векторные индексы шардируются по категориям (`real_estate`, `cars`, `electronics`).  
- Faiss / Milvus — отдельный StatefulSet с SSD volume.  
- PostgreSQL — с репликами для чтения.  
- Все сервисы объединены в namespace `image-detection`.

---

## 🔐 Безопасность

- Секреты хранятся в Kubernetes Secrets (DB, Redis, S3).  
- RBAC для доступа только к нужным PVC и сервисам.  
- HTTPS через cert-manager / Let's Encrypt.  
- Rate limiting на ingest API.  
- Очереди и задачи — идемпотентные.

---

## 🧮 API контракты

### POST /api/v1/image/ingest
```json
{
  "ad_id": 12345,
  "source": "olx.pt",
  "images": [
    "https://olx.pt/imgs/house1.jpg",
    "https://olx.pt/imgs/house2.jpg"
  ]
}
```

### GET /api/v1/duplicates/{ad_id}
Возвращает список похожих объявлений с оценкой совпадения.

### GET /api/v1/clusters
Возвращает кластеры с одинаковыми изображениями.

---

## 🔭 Возможные расширения

- TorchServe / Triton для CLIP inference.
- Patch-based индекс для обработки кропов.
- Auto-retraining на локальных данных.
- Кеширование результатов Faiss в Redis.
- Analytics API `/api/v1/stats` (top repeated domains, duplicate ratios).

---

## 🧱 Helm Chart структура

```
charts/image-duplicate/
├── templates/
│   ├── deployment-api.yaml
│   ├── deployment-worker.yaml
│   ├── deployment-verifier.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── secrets.yaml
├── values.yaml
├── Chart.yaml
└── README.md
```

---

## 🧠 Основные принципы

1. **Изоляция** — модуль независим, общается через API и очереди.  
2. **Устойчивость** — сочетает перцептивные и нейронные признаки.  
3. **Масштабируемость** — горизонтальное масштабирование и ANN-индексы.  
4. **Наблюдаемость** — метрики, логирование, UI для проверки кластеров.  
5. **Безопасность** — RBAC, Secrets, TLS, идемпотентные задачи.

