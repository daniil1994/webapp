# Phase 1: Detailed Roadmap - Cursor Clone + React MVP
**Период:** Week 1-12 (3 месяца)
**Цель:** Создать полнофункциональный AI coding assistant с CLI + React Web интерфейсом

---

## Week 1: Backend Foundation + Docker Infrastructure
**Цель:** Создать базовую инфраструктуру и auth систему

### Backend Tasks (5-6 дней)

#### 1.1. Project Setup
- [ ] Создать структуру проекта `backend/`
  ```
  backend/
  ├── src/
  │   ├── api/           # FastAPI routes
  │   ├── core/          # Config, security
  │   ├── db/            # Database models
  │   ├── services/      # Business logic
  │   └── main.py
  ├── tests/
  ├── alembic/           # DB migrations
  ├── Dockerfile
  ├── pyproject.toml
  └── .env.example
  ```
- [ ] Setup Poetry/pip для зависимостей
- [ ] Конфигурация Ruff/Black для code style

#### 1.2. Database Setup
- [ ] Docker Compose: PostgreSQL 16 + pgvector
- [ ] Docker Compose: Redis 7.4+
- [ ] Alembic migrations setup
- [ ] Create tables:
  ```sql
  - organizations (id, name, created_at)
  - users (id, org_id, email, hashed_password, role)
  - api_keys (id, user_id, key_hash, created_at)
  - projects (id, org_id, name, repo_path, status)
  ```

#### 1.3. Auth System
- [ ] `/api/v1/auth/register` - регистрация пользователя
- [ ] `/api/v1/auth/login` - JWT токен
- [ ] `/api/v1/auth/refresh` - обновление токена
- [ ] Middleware для проверки JWT
- [ ] Password hashing (bcrypt)
- [ ] Role-based access control (RBAC) - базовый

#### 1.4. Core API
- [ ] Health check: `GET /health`
- [ ] User info: `GET /api/v1/users/me`
- [ ] Organization info: `GET /api/v1/orgs/{id}`
- [ ] Error handling middleware
- [ ] CORS configuration

#### 1.5. CLI Skeleton
- [ ] Click CLI setup
- [ ] `repa auth login` - сохранение API key
- [ ] `repa auth logout`
- [ ] Config файл `~/.repa/config.json`
- [ ] Rich для красивого вывода

### Frontend Tasks (1-2 дня)

#### 1.6. Package Updates
- [ ] Обновить React 18.3 → 19+
- [ ] Добавить зависимости:
  ```bash
  npm install @tanstack/react-query zustand react-router-dom axios
  ```
- [ ] Удалить MUI (заменен на shadcn/ui)

#### 1.7. Auth UI (базовый)
- [ ] Страница `/login` - форма входа
- [ ] Страница `/register` - форма регистрации
- [ ] Zustand store для auth state
- [ ] API client setup (`lib/api.ts`)

### Definition of Done (Week 1)
- ✅ Docker Compose поднимает Postgres + Redis
- ✅ API принимает запросы на /health, /auth/login
- ✅ CLI может залогиниться и сохранить токен
- ✅ Frontend может залогиниться через UI
- ✅ JWT токены работают

---

## Week 2-3: Repository Indexing + Code Embeddings
**Цель:** Индексация кодовой базы в pgvector

### Backend Tasks (Week 2: 5-6 дней)

#### 2.1. Database Schema
- [ ] Create table `code_embeddings`:
  ```sql
  CREATE TABLE code_embeddings (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    file_path TEXT,
    chunk_text TEXT,
    line_start INT,
    line_end INT,
    embedding VECTOR(1536),  -- OpenAI ada-002
    created_at TIMESTAMPTZ
  );
  CREATE INDEX ON code_embeddings USING ivfflat (embedding vector_cosine_ops);
  ```
- [ ] Create table `indexing_jobs`:
  ```sql
  CREATE TABLE indexing_jobs (
    id UUID PRIMARY KEY,
    project_id UUID,
    status TEXT,  -- pending, running, completed, failed
    progress INT,
    total_files INT,
    error TEXT,
    created_at TIMESTAMPTZ
  );
  ```

#### 2.2. Repository Parser
- [ ] Service `RepoIndexer` (async)
  - Поддержка `.gitignore`
  - Фильтр по расширениям (.py, .js, .ts, .tsx, .go, и т.д.)
  - Tree-sitter parsing для структурного анализа
- [ ] Chunking strategy:
  - Функции (full function body)
  - Классы (full class)
  - Imports (отдельный чанк)
  - Max chunk size: 500 tokens

#### 2.3. Embeddings Generation
- [ ] OpenAI API integration (text-embedding-3-small или ada-002)
- [ ] Batch processing (100 чанков за раз)
- [ ] Rate limiting
- [ ] Retry logic
- [ ] Progress tracking

#### 2.4. API Endpoints
- [x] `POST /api/v1/projects` - создать проект + git clone ✅ **Week 5** (2026-02-06)
- [x] `POST /api/v1/projects/{id}/sync` - синхронизация с remote ✅ **Week 5**
- [x] `POST /api/v1/projects/{id}/index` - запустить индексацию (background job) ✅
- [ ] `GET /api/v1/projects/{id}/index/status` - прогресс индексации
- [x] `GET /api/v1/projects` - список проектов ✅
- [x] Background jobs с asyncio.create_task ✅

#### 2.5. CLI Commands
- [ ] `repa repo init <path>` - добавить локальный репо
- [ ] `repa repo index` - запустить индексацию
- [ ] `repa repo status` - статус индексации (прогресс-бар)

### Frontend Tasks (Week 3: 3-4 дня)

#### 3.1. React Router Setup
- [ ] Установка `react-router-dom`
- [ ] Layout с `<Outlet />`
- [ ] Routes:
  ```tsx
  /login
  /register
  /dashboard
  /projects
  /projects/:id
  /settings
  ```
- [ ] Protected routes (auth guard)
- [ ] Заменить useState роутинг на React Router

#### 3.2. React Query Setup
- [ ] QueryClient configuration
- [ ] QueryClientProvider в `main.tsx`
- [ ] Devtools (development only)

#### 3.3. Projects Integration
- [ ] Hook `useProjects()` - React Query
  ```ts
  const { data: projects, isLoading } = useProjects();
  ```
- [ ] Hook `useProject(id)` - детали проекта
- [ ] Hook `useIndexStatus(projectId)` - прогресс индексации
- [ ] Обновить `Projects.tsx` - реальные данные вместо mock
- [ ] Кнопка "Новый проект" → форма с git clone
- [ ] Кнопка "Index" → запуск индексации
- [ ] Real-time обновление прогресса (polling каждые 2 сек)

### Definition of Done (Week 2-3)
- ✅ CLI: `repa repo init .` индексирует локальный проект
- ✅ Backend генерирует embeddings и сохраняет в pgvector
- ✅ Frontend показывает реальные проекты из API
- ✅ Progress bar обновляется при индексации
- ✅ pgvector поиск работает (тестовый запрос)

---

## Week 4-5: Plan Generation + Diff Application
**Цель:** Генерация планов изменений и применение диффов

### Backend Tasks (Week 4: 5-6 дней)

#### 4.1. RAG Search
- [ ] Service `CodeSearch`:
  ```python
  async def search_relevant_code(
      project_id: UUID,
      query: str,
      top_k: int = 10
  ) -> List[CodeChunk]
  ```
- [ ] Embeddings для query
- [ ] Cosine similarity search в pgvector
- [ ] Re-ranking (опционально)

#### 4.2. Plan Generation
- [ ] Service `PlanGenerator`:
  - LLM prompt engineering (Claude Sonnet 4.5 или GPT-4)
  - Контекст: relevant code + user query
  - Вывод: список шагов в JSON
    ```json
    {
      "steps": [
        {
          "description": "Add JWT middleware",
          "files": ["src/auth/middleware.py"],
          "reasoning": "..."
        }
      ]
    }
    ```
- [ ] Database table `plans`:
  ```sql
  CREATE TABLE plans (
    id UUID PRIMARY KEY,
    project_id UUID,
    user_prompt TEXT,
    steps JSONB,
    status TEXT,
    created_at TIMESTAMPTZ
  );
  ```

#### 4.3. Code Diff Generation
- [ ] Service `DiffGenerator`:
  - LLM генерирует изменения для каждого файла
  - Формат: unified diff
  - Валидация синтаксиса
- [ ] Database table `diffs`:
  ```sql
  CREATE TABLE diffs (
    id UUID PRIMARY KEY,
    plan_id UUID,
    file_path TEXT,
    diff_content TEXT,
    status TEXT,  -- pending, applied, rejected
    created_at TIMESTAMPTZ
  );
  ```

#### 4.4. Diff Application
- [ ] Service `DiffApplier`:
  ```python
  async def apply_diff(project_id: UUID, diff_id: UUID):
      # 1. Read file
      # 2. Apply patch
      # 3. Write file
      # 4. Update status
  ```
- [ ] Git integration (auto-commit опционально)

#### 4.5. API Endpoints
- [ ] `POST /api/v1/projects/{id}/plan` - создать план
  ```json
  { "prompt": "Add JWT authentication" }
  → { "plan_id": "...", "steps": [...] }
  ```
- [ ] `GET /api/v1/plans/{id}` - детали плана
- [ ] `POST /api/v1/plans/{id}/generate-diffs` - генерация диффов
- [ ] `POST /api/v1/diffs/{id}/apply` - применить diff
- [ ] `POST /api/v1/diffs/{id}/reject` - отклонить

#### 4.6. CLI Commands
- [ ] `repa plan "add JWT auth"` - генерация плана
- [ ] `repa plan show <plan_id>` - просмотр
- [ ] `repa apply <diff_id>` - применить diff
- [ ] `repa apply --all` - применить все

### Frontend Tasks (Week 5: 3-4 дня)

#### 5.1. Plan Viewer Integration
- [ ] Hook `usePlan(planId)` - React Query
- [ ] Hook `useCreatePlan()` - mutation
- [ ] Обновить `ProjectDetail.tsx`:
  - Реальные планы вместо mock
  - Кнопка "Новый План" → форма с промптом
  - Список планов с прогрессом

#### 5.2. Diff Viewer Integration
- [ ] Установить `react-diff-viewer-continued`
- [ ] Обновить `DiffViewer.tsx`:
  - Реальный diff из API
  - Кнопки Apply/Reject
  - Syntax highlighting
- [ ] Hook `useApplyDiff()` - mutation
- [ ] Оптимистичные обновления UI

#### 5.3. Chat Interface (базовый)
- [ ] Форма в `ProjectDetail.tsx` → вкладка "Чат"
- [ ] `POST /api/v1/projects/{id}/chat` - отправка сообщения
- [ ] История чата (не WebSocket пока, просто polling)

### Definition of Done (Week 4-5)
- ✅ CLI: `repa plan "add feature"` генерирует план
- ✅ CLI: `repa apply step-1` применяет изменения к файлам
- ✅ Frontend: создание плана через UI
- ✅ Frontend: просмотр diff и apply через кнопку
- ✅ LLM генерирует валидный код (хотя бы 70% успеха)

---

## Week 6-7: WebSocket Real-Time + Test Generation
**Цель:** Real-time прогресс и автоматическая генерация тестов

### Backend Tasks (Week 6: 4-5 дней)

#### 6.1. WebSocket Server
- [ ] FastAPI WebSocket endpoint: `/ws/{job_id}`
- [ ] Job stream format:
  ```json
  {
    "type": "progress",
    "data": { "step": 1, "total": 5, "message": "Indexing files..." }
  }
  {
    "type": "complete",
    "data": { "result": {...} }
  }
  {
    "type": "error",
    "data": { "error": "..." }
  }
  ```
- [ ] Integration с indexing jobs
- [ ] Integration с plan generation jobs

#### 6.2. Test Generation
- [ ] Service `TestGenerator`:
  - Анализ функции/класса
  - LLM генерирует pytest тесты
  - Coverage analysis (опционально)
- [ ] API Endpoint: `POST /api/v1/files/{path}/generate-tests`
- [ ] CLI: `repa tests generate <file_path>`

#### 6.3. Background Jobs Refactoring
- [ ] Перевести все долгие операции на background jobs
- [ ] Job queue (Redis-based или asyncio)
- [ ] Retry logic
- [ ] Job cancellation

### Frontend Tasks (Week 7: 3-4 дня)

#### 7.1. WebSocket Client
- [ ] Create `lib/websocket.ts`:
  ```ts
  class JobStream {
    connect(jobId: string)
    onProgress(callback)
    onComplete(callback)
    onError(callback)
    disconnect()
  }
  ```
- [ ] Hook `useJobStream(jobId)`:
  ```ts
  const { progress, isComplete, error } = useJobStream(jobId);
  ```

#### 7.2. Real-Time Progress UI
- [ ] Обновить `Projects.tsx`:
  - WebSocket прогресс индексации (вместо polling)
- [ ] Обновить `ProjectDetail.tsx`:
  - Real-time прогресс генерации плана
  - Real-time прогресс применения diff
- [ ] Toast уведомления при завершении

#### 7.3. Chat UI Enhancement
- [ ] Markdown rendering (react-markdown)
- [ ] Code blocks с syntax highlighting
- [ ] Копирование кода
- [ ] Автоскролл

### Definition of Done (Week 6-7)
- ✅ WebSocket: прогресс индексации обновляется в real-time
- ✅ WebSocket: генерация плана стримится в UI
- ✅ CLI: `repa tests generate auth.py` создает тесты
- ✅ Frontend: чат с markdown и code blocks

---

## Week 8-9: VS Code Extension MVP + Billing
**Цель:** Базовое расширение VS Code и система биллинга

### Backend Tasks (Week 8: 3-4 дня)

#### 8.1. Billing System (базовый)
- [ ] Database tables:
  ```sql
  CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    org_id UUID,
    plan TEXT,  -- free, pro, enterprise
    status TEXT,
    current_period_end TIMESTAMPTZ
  );
  CREATE TABLE usage (
    id UUID PRIMARY KEY,
    org_id UUID,
    metric TEXT,  -- api_calls, embeddings, llm_tokens
    value INT,
    period DATE
  );
  ```
- [ ] API Endpoints:
  - `GET /api/v1/orgs/{id}/usage` - текущее потребление
  - `GET /api/v1/orgs/{id}/subscription` - план подписки
  - `POST /api/v1/orgs/{id}/upgrade` - апгрейд плана

#### 8.2. Rate Limiting
- [ ] Middleware для лимитов:
  - Free: 10 планов/день
  - Pro: 100 планов/день
  - Enterprise: unlimited
- [ ] Redis для rate limiting (sliding window)

### VS Code Extension (Week 8-9: 4-5 дней)

#### 9.1. Extension Setup
- [ ] Создать проект `vscode-extension/`
- [ ] TypeScript + esbuild
- [ ] VS Code API setup
- [ ] Package.json с activationEvents

#### 9.2. Basic Features
- [ ] Sidebar панель Repa
- [ ] Авторизация (API key)
- [ ] Список проектов
- [ ] Кнопка "Generate Plan" → inline input
- [ ] Diff preview
- [ ] Apply/Reject патчи

#### 9.3. Extension Commands
- [ ] `repa.login` - авторизация
- [ ] `repa.generatePlan` - генерация плана
- [ ] `repa.applyDiff` - применение патча

### Frontend Tasks (Week 9: 2-3 дня)

#### 9.4. Org Settings Page
- [ ] Обновить `OrgSettings.tsx`:
  - Usage dashboard (графики)
  - Current plan
  - Upgrade кнопка
  - API keys management
- [ ] Hook `useOrgUsage()` - React Query
- [ ] Recharts графики потребления

### Definition of Done (Week 8-9)
- ✅ VS Code extension устанавливается и подключается к backend
- ✅ Extension: можно создать план из VS Code
- ✅ Extension: можно применить diff из VS Code
- ✅ Frontend: страница настроек с usage metrics
- ✅ Rate limiting работает

---

## Week 10-12: Security Audit + Pilot Launch
**Цель:** Безопасность, оптимизация, запуск пилота

### Backend Tasks (Week 10: 4-5 дней)

#### 10.1. Security Hardening
- [ ] OWASP Top 10 проверка:
  - SQL injection (parameterized queries)
  - XSS (санитизация выводов)
  - CSRF (tokens)
  - Auth bypass (проверка middleware)
- [ ] Secrets management (env vars, Vault опционально)
- [ ] Input validation (Pydantic models)
- [ ] Rate limiting на всех эндпоинтах
- [ ] API key rotation

#### 10.2. Logging & Monitoring
- [ ] Structured logging (structlog)
- [ ] Sentry integration для errors
- [ ] Prometheus metrics:
  - API latency
  - DB queries
  - LLM calls
  - Embeddings generated
- [ ] Grafana dashboard

#### 10.3. Performance Optimization
- [ ] Database indexing review
- [ ] Query optimization (N+1 проблемы)
- [ ] Caching стратегия (Redis)
- [ ] Connection pooling

### Frontend Tasks (Week 11: 3-4 дня)

#### 11.1. Analytics Dashboard
- [ ] Новая страница `/analytics`
- [ ] Графики:
  - AI requests по времени
  - Acceptance rate планов
  - Top используемые файлы
  - Экономия времени (mock calculation)
- [ ] Recharts или Chart.js

#### 11.2. Error Handling
- [ ] Error boundary компоненты
- [ ] Toast/snackbar для ошибок API
- [ ] Retry логика для failed requests
- [ ] Fallback UI

#### 11.3. UI Polish
- [ ] Loading states везде
- [ ] Empty states (нет проектов, нет планов)
- [ ] Skeleton loaders
- [ ] Smooth transitions
- [ ] Accessibility audit (a11y)

### Week 12: Pilot Launch (4-5 дней)

#### 12.1. Documentation
- [ ] README.md с setup инструкциями
- [ ] API documentation (Swagger/OpenAPI)
- [ ] User guide (Notion/GitBook)
- [ ] Video demo (Loom/YouTube)

#### 12.2. Deployment
- [ ] Production Docker Compose
- [ ] Environment variables setup
- [ ] Database backup strategy
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Deploy на Cloud.ru/VK Cloud

#### 12.3. Pilot Users
- [ ] Onboarding flow
- [ ] Feedback form
- [ ] Analytics tracking (PostHog/Mixpanel)
- [ ] Bug reporting (GitHub Issues)

### Definition of Done (Week 10-12)
- ✅ Security audit пройден (0 критических уязвимостей)
- ✅ Monitoring dashboard работает (Grafana)
- ✅ 3 пилотные команды используют продукт
- ✅ Documentation complete
- ✅ Deployment в production

---

## Success Metrics (End of Phase 1)

### Technical KPIs
- ⚡ API Latency: p95 < 500ms
- 🔒 Security: 0 критических уязвимостей
- 📊 Test Coverage: > 70%
- 🐛 Bug Rate: < 5 критичных багов в неделю

### Product KPIs
- 👥 Active Users: 3-10 команд
- ✅ Plan Acceptance Rate: > 60%
- ⏱️ Time Saved: ~10+ часов/команда/неделю
- 💬 NPS: > 7/10

### Infrastructure
- 🐳 Docker: полностью контейнеризировано
- 🔄 CI/CD: автоматический деплой
- 📈 Monitoring: Grafana + Sentry
- 💾 Database: PostgreSQL + pgvector работает на 10k+ embeddings

---

## Risks & Mitigation

### Technical Risks
1. **LLM качество кода низкое**
   - Mitigation: Prompt engineering итерации, использование лучших моделей (Claude Sonnet 4.5)

2. **pgvector медленный на больших репо**
   - Mitigation: Оптимизация индексов, chunking стратегия, HNSW вместо ivfflat

3. **WebSocket проблемы на production**
   - Mitigation: Polling fallback, sticky sessions, load balancer настройка

### Business Risks
1. **Пилотные пользователи не видят ценность**
   - Mitigation: Частые интервью, быстрые итерации, фокус на real pain points

2. **Конкуренция с Cursor/GitHub Copilot**
   - Mitigation: Уникальное УТП (multi-agent платформа, не только dev), см. product-improvements.md

---

## Next Steps → Phase 2

После завершения Phase 1:
- Product Manager Agent (идея → PRD)
- Marketing Agent (УТП + контент)
- SEO Agent (техSEO аудит)
- Multi-Agent Router
- Expanded RAG (дизайн, маркетинг материалы)
