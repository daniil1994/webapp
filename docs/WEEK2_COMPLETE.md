# ✅ Week 2: Repository Indexing - COMPLETE

## 🎯 Цель достигнута
Реализована полная система индексации кодовых баз с генерацией embeddings через OpenAI API.

---

## 📊 Что реализовано

### 1. Database Schema ✅
**Файл:** `backend/alembic/versions/001_initial_schema.py`

**Таблицы:**
- `organizations` - организации пользователей
- `users` - пользователи с JWT аутентификацией
- `projects` - репозитории для индексации
- `code_embeddings` - векторные представления кода (1536 размерность)
- `indexing_jobs` - трекинг прогресса индексации

**Важно:** Используется `ARRAY[Float]` вместо `pgvector.Vector` из-за отсутствия прав superuser на БД.
- Когда pgvector станет доступен, можно будет мигрировать на оптимизированный тип
- Текущее решение полностью функционально для хранения и извлечения embeddings

### 2. SQLAlchemy Models ✅
**Файл:** `backend/src/db/models/project.py`

**Модели:**
```python
class Project:
    - repo_path, repo_url, description
    - status: active, indexing, failed
    - total_files, indexed_files
    - last_indexed_at

class CodeEmbedding:
    - file_path, chunk_text, chunk_type
    - line_start, line_end
    - embedding: ARRAY[Float] (1536 dims)
    - extra_metadata: JSONB

class IndexingJob:
    - status: pending, running, completed, failed
    - progress, total_files, current_file
    - error, started_at, completed_at
```

### 3. Services Layer ✅

#### RepoIndexer (`backend/src/services/repo_indexer.py`)
```python
class RepoIndexer:
    ✓ Поддержка .gitignore + default ignore patterns
    ✓ 20+ языков: Python, JS, TS, Go, Rust, Java, etc.
    ✓ Chunking стратегия:
      - Функции (function)
      - Классы (class)
      - Импорты (import)
      - Блоки кода (block)
    ✓ Async генератор для эффективной обработки больших репо
    ✓ Определение типа чанка через regex patterns
```

**Поддерживаемые расширения:**
`.py`, `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.rs`, `.java`, `.rb`, `.php`, `.cpp`, `.c`, `.h`, `.cs`, `.swift`, `.kt`, `.scala`, `.md`, `.json`, `.yaml`, `.toml`, `.sql`

#### EmbeddingsService (`backend/src/services/embeddings.py`)
```python
class EmbeddingsService:
    ✓ OpenAI text-embedding-3-small интеграция
    ✓ Batch processing (до 100 текстов за раз)
    ✓ Rate limiting с configurable delay
    ✓ Exponential backoff retry (max 3 попытки)
    ✓ Автоматическое truncation для длинных текстов (8000 tokens)
    ✓ Token counting с tiktoken
```

#### IndexingService (`backend/src/services/indexing.py`)
```python
class IndexingService:
    ✓ Оркестрация: scan → chunk → embed → save
    ✓ Real-time progress tracking
    ✓ Background job support (FastAPI BackgroundTasks)
    ✓ Error handling с сохранением статуса
    ✓ Batch commit для оптимизации DB операций
```

### 4. API Endpoints ✅
**Файл:** `backend/src/api/v1/projects.py`

```bash
# Projects CRUD
GET    /api/v1/projects              # Список проектов
POST   /api/v1/projects              # Создать проект
GET    /api/v1/projects/{id}         # Детали проекта
PATCH  /api/v1/projects/{id}         # Обновить проект
DELETE /api/v1/projects/{id}         # Удалить проект

# Indexing Control
POST   /api/v1/projects/{id}/index           # Запустить индексацию
GET    /api/v1/projects/{id}/index/status    # Статус индексации (с %)
GET    /api/v1/projects/{id}/index/history   # История индексаций
```

**Auth:** Все endpoints защищены JWT токеном

### 5. Schemas ✅
**Файл:** `backend/src/schemas/project.py`

```python
ProjectCreate, ProjectUpdate, ProjectResponse
IndexingJobResponse, IndexingStatusResponse
```

---

## 🔧 Конфигурация

### Database Connection
**Файл:** `backend/.env`
```env
DATABASE_URL=postgresql+asyncpg://admin_repa:PASSWORD@cabc149f4093f502673ee7d4.twc1.net:5432/repa
OPENAI_API_KEY=<ваш_ключ>
EMBEDDING_MODEL=text-embedding-3-small
```

### Dependencies Added
**Файл:** `backend/requirements.txt`
```
pgvector==0.4.2
tiktoken==0.8.0
pathspec==0.12.1
```

---

## 🚀 Использование

### 1. Запуск приложения
```bash
./start.sh
```

**Доступ:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

### 2. Создание проекта
```bash
POST /api/v1/projects
Authorization: Bearer YOUR_JWT_TOKEN

{
  "name": "My Repo",
  "repo_path": "/path/to/local/repo",
  "description": "Test project"
}
```

### 3. Запуск индексации
```bash
POST /api/v1/projects/{project_id}/index
Authorization: Bearer YOUR_JWT_TOKEN

# Ответ:
{
  "id": "job-uuid",
  "project_id": "project-uuid",
  "status": "pending",
  "progress": 0,
  "total_files": 0
}
```

### 4. Проверка статуса
```bash
GET /api/v1/projects/{project_id}/index/status
Authorization: Bearer YOUR_JWT_TOKEN

# Ответ:
{
  "job": {...},
  "percentage": 45.5,
  "is_running": true,
  "is_completed": false,
  "is_failed": false
}
```

---

## 📐 Архитектура потока индексации

```
User Request (POST /projects/{id}/index)
     ↓
API Endpoint validates auth & project ownership
     ↓
IndexingService.index_project(project_id, repo_path)
     ├─ Create IndexingJob (status: pending)
     ├─ Update status → running
     └─ Start indexing
          ↓
     RepoIndexer.index_repository(repo_path)
          ├─ Load .gitignore patterns
          ├─ Scan files (skip ignored)
          ├─ Extract chunks per file:
          │    ├─ Read file content
          │    ├─ Split by lines/functions/classes
          │    └─ Yield CodeChunk objects
          └─ Return all chunks
          ↓
     EmbeddingsService.generate_embeddings_batch(texts)
          ├─ Batch chunks (100 at a time)
          ├─ Truncate long texts (8000 tokens max)
          ├─ Call OpenAI API
          ├─ Rate limiting (0.1s delay between batches)
          └─ Return vectors (1536 dimensions)
          ↓
     Save to Database
          ├─ Insert CodeEmbedding records
          ├─ Update IndexingJob progress
          └─ Update Project stats
          ↓
     Complete Job (status: completed)
```

---

## 🧪 Тестирование

### Manual Testing
1. **Swagger UI:** http://localhost:8000/docs
2. **Зарегистрировать пользователя:** `/api/v1/auth/register`
3. **Получить JWT токен:** `/api/v1/auth/login`
4. **Создать проект:** `/api/v1/projects`
5. **Запустить индексацию:** `/api/v1/projects/{id}/index`
6. **Проверить статус:** `/api/v1/projects/{id}/index/status`

### Example: Index Backend Repo
```python
# 1. Create project
project = {
    "name": "Repa Backend",
    "repo_path": "/Users/daniilladejsikov/Documents/Repa/backend",
    "description": "Self-indexing test"
}

# 2. Start indexing
# Background job will:
# - Scan ~20-30 Python files
# - Extract ~100-200 code chunks
# - Generate embeddings (via OpenAI)
# - Save to database
# Total time: ~2-5 minutes (depends on repo size)

# 3. Check status
# {
#   "percentage": 75.0,
#   "is_running": true,
#   "current_file": "src/services/indexing.py"
# }
```

---

## ⚠️ Важные заметки

### pgvector Limitation
- Текущая БД не имеет установленного `pgvector` extension
- Используется `ARRAY[Float]` для хранения embeddings
- **Функционал полностью работает**, но без оптимизированных vector indices
- Для миграции на pgvector потребуется:
  1. Попросить админа БД выполнить: `CREATE EXTENSION vector;`
  2. Создать миграцию для конвертации `ARRAY → VECTOR`
  3. Создать IVFFlat index для быстрого cosine similarity search

### OpenAI API Key
- **Обязательно** добавь свой ключ в `backend/.env`:
  ```env
  OPENAI_API_KEY=sk-...
  ```
- Без ключа индексация не будет работать
- Модель: `text-embedding-3-small` (1536 dimensions)
- Стоимость: ~$0.02 на 1M tokens

### Background Jobs
- Используется FastAPI `BackgroundTasks`
- Для production рекомендуется Celery + Redis
- Текущее решение подходит для dev и small-scale

---

## 📈 Метрики производительности

**Примерная скорость индексации:**
- Малый проект (10-50 файлов): 1-2 минуты
- Средний проект (50-200 файлов): 2-5 минут
- Большой проект (200-1000 файлов): 5-15 минут

**Факторы:**
- Размер файлов
- Количество chunks (функции/классы)
- OpenAI API latency (~100-300ms на batch)
- Rate limiting delays

---

## ⏭️ Следующие шаги (Week 3-4)

### Frontend Integration (Week 3)
- [ ] React Query hooks для Projects API
- [ ] Projects страница с реальными данными
- [ ] Real-time progress bar для индексации
- [ ] Project details page

### RAG Search (Week 4)
- [ ] Semantic code search по embeddings
- [ ] Cosine similarity вычисления (NumPy/Python)
- [ ] Search API endpoint: `POST /api/v1/search`
- [ ] Re-ranking опционально

### Plan Generation (Week 4-5)
- [ ] Claude/GPT-4 интеграция для генерации планов
- [ ] Context building: query + relevant code chunks
- [ ] Plan schema (steps, files, reasoning)
- [ ] Plan API endpoints

---

## 🎉 Статус: Week 2 COMPLETE

**Готово:**
- ✅ Database schema с миграциями
- ✅ SQLAlchemy models
- ✅ RepoIndexer service (gitignore, chunking, 20+ languages)
- ✅ EmbeddingsService (OpenAI, batching, retry logic)
- ✅ IndexingService (orchestration, progress tracking)
- ✅ Full CRUD API для Projects
- ✅ Indexing control endpoints
- ✅ Backend запущен с production DB

**В процессе:**
- ⏳ Frontend integration (Week 3)

**След этап:**
- 🎯 Week 3: React Query + Projects UI + Real-time progress

---

**Система готова к полноценному использованию!** 🚀
