# Repa Development Plan - Complete Documentation
**Product Agent Platform: From Idea to 1M Users**

---

## 📋 Документация

Эта папка содержит полную документацию для разработки Repa Phase 1.

### Основные документы

1. **[prd.md](../prd.md)** - Исходное техническое задание (PRD)
   - Общее видение продукта
   - Технический стек
   - Архитектура Product Memory

2. **[frontend-audit.md](./frontend-audit.md)** - Аудит текущего состояния frontend
   - Что уже реализовано (40% готовности)
   - Критические пробелы
   - Приоритеты рефакторинга

3. **[phase1-roadmap-detailed.md](./phase1-roadmap-detailed.md)** - Детальный roadmap с декомпозицией
   - Week 1-12: пошаговый план
   - Backend + Frontend задачи
   - Definition of Done для каждой недели

4. **[product-improvements.md](./product-improvements.md)** - Конкурентные преимущества
   - Уникальные фичи vs Cursor/Copilot
   - Phase 1-3 улучшения
   - Метрики успеха

5. **[frontend-tasks-weekly.md](./frontend-tasks-weekly.md)** - Frontend доработки по неделям
   - Конкретные изменения в коде
   - Новые компоненты и хуки
   - Интеграция с backend API

---

## 🚀 Quick Start Guide (для тимлида)

### Неделя 1: С чего начать?

#### День 1-2: Backend Setup
```bash
# 1. Создать структуру проекта
mkdir -p backend/src/{api,core,db,services}
cd backend

# 2. Установить зависимости
poetry init
poetry add fastapi uvicorn sqlalchemy asyncpg alembic pydantic-settings

# 3. Docker Compose
docker-compose up -d postgres redis

# 4. Первый API endpoint
# Следовать phase1-roadmap-detailed.md → Week 1 → Backend Tasks
```

#### День 3-4: Frontend Architecture
```bash
cd frontend

# 1. Обновить зависимости
npm install react@19 react-dom@19
npm install @tanstack/react-query zustand react-router-dom axios

# 2. Создать структуру
mkdir -p src/{lib,hooks,store,types,pages}

# 3. Следовать frontend-tasks-weekly.md → Week 1
```

#### День 5: Интеграция
- Backend: `POST /api/v1/auth/login` работает
- Frontend: Login page подключается к backend
- E2E тест: можно залогиниться через UI

---

## 📊 Current Status

### Frontend (40% готово)
✅ **Сильные стороны:**
- Отличный UI/UX дизайн (GitHub-style)
- shadcn/ui компоненты полностью настроены
- Основные страницы существуют

❌ **Критические пробелы:**
- Нет роутинга (React Router)
- Нет API интеграции (React Query)
- Нет state management (Zustand)
- Все данные захардкожены (mock)

### Backend (0% готово)
❌ Полностью отсутствует - начать с нуля

**Рекомендация:** Backend first подход (Week 1-2), затем интеграция с frontend (Week 3-6)

---

## 🎯 Phase 1 Goals (Week 1-12)

### Milestone 1: Auth + Infrastructure (Week 1)
- [ ] Docker Compose: Postgres + Redis
- [ ] Backend: FastAPI + JWT auth
- [ ] Frontend: Login page + React Router
- [ ] E2E: можно залогиниться

### Milestone 2: Repository Indexing (Week 2-3)
- [ ] Backend: индексация кода в pgvector
- [ ] CLI: `repa repo index`
- [ ] Frontend: Projects page с реальными данными
- [ ] E2E: можно проиндексировать репо и увидеть прогресс

### Milestone 3: Plan Generation (Week 4-5)
- [ ] Backend: LLM генерирует план изменений
- [ ] Backend: генерация диффов
- [ ] Frontend: создание плана через UI
- [ ] E2E: можно создать план и применить diff

### Milestone 4: Real-Time Features (Week 6-7)
- [ ] Backend: WebSocket server
- [ ] Frontend: WebSocket client
- [ ] E2E: прогресс обновляется в real-time

### Milestone 5: VS Code Extension (Week 8-9)
- [ ] Extension: базовая авторизация
- [ ] Extension: генерация плана
- [ ] Frontend: Org Settings с usage metrics

### Milestone 6: Production Ready (Week 10-12)
- [ ] Security audit
- [ ] Monitoring (Grafana + Sentry)
- [ ] 3 пилотные команды
- [ ] Documentation complete

---

## 💡 Конкурентные Преимущества (vs Cursor)

### Phase 1 Killer Features

1. **Multi-File Context** - AI видит ВЕСЬ репо, не только открытые файлы
2. **Plan Approval Flow** - контроль над изменениями, не "черный ящик"
3. **Explainable AI** - AI объясняет reasoning для каждого шага
4. **Test-Driven Mode** - генерация тестов ПЕРЕД кодом
5. **Project Memory** - AI запоминает архитектуру и past decisions

### Phase 2+ Vision

6. **Role-Based Agents** - PM, Marketing, SEO modes (не только dev)
7. **Team Collaboration** - shared plans, approvals, comments
8. **Multi-Repo Support** - cross-repo context (backend + frontend)

**Полный список:** [product-improvements.md](./product-improvements.md)

---

## 📁 Recommended Project Structure

```
Repa/
├── backend/                    # ❌ Создать с нуля
│   ├── src/
│   │   ├── api/               # FastAPI routes
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── projects.py
│   │   │       ├── plans.py
│   │   │       └── websocket.py
│   │   ├── core/              # Config, security
│   │   ├── db/                # SQLAlchemy models
│   │   ├── services/          # Business logic
│   │   │   ├── indexer.py
│   │   │   ├── planner.py
│   │   │   └── diff_generator.py
│   │   └── main.py
│   ├── tests/
│   ├── alembic/
│   ├── Dockerfile
│   └── pyproject.toml
│
├── frontend/                   # ✅ 40% готово
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/   # ✅ Существует
│   │   │   └── App.tsx       # ⚠️ Нужен рефакторинг
│   │   ├── lib/              # ❌ Создать
│   │   │   ├── api.ts
│   │   │   └── websocket.ts
│   │   ├── hooks/            # ❌ Создать
│   │   │   ├── useProjects.ts
│   │   │   ├── usePlans.ts
│   │   │   └── useJobStream.ts
│   │   ├── store/            # ❌ Создать
│   │   │   └── authStore.ts
│   │   ├── types/            # ❌ Создать
│   │   │   └── api.ts
│   │   └── pages/            # ❌ Создать
│   │       ├── LoginPage.tsx
│   │       └── ...
│   └── package.json
│
├── cli/                        # ❌ Создать
│   ├── repa/
│   │   ├── commands/
│   │   │   ├── auth.py
│   │   │   ├── repo.py
│   │   │   └── plan.py
│   │   └── main.py
│   └── setup.py
│
├── vscode-extension/           # Week 8-9
│
├── docs/                       # ✅ Эта папка
│   ├── README.md              # Этот файл
│   ├── frontend-audit.md
│   ├── phase1-roadmap-detailed.md
│   ├── product-improvements.md
│   └── frontend-tasks-weekly.md
│
├── docker-compose.yml          # ❌ Создать
├── prd.md                      # ✅ Исходный PRD
└── README.md                   # ⚠️ Обновить
```

---

## 🔥 Action Plan (Next 2 Weeks)

### Week 1: Backend Foundation

**Понедельник (Backend Dev):**
- [ ] Создать backend/ структуру
- [ ] Docker Compose: postgres + redis
- [ ] Alembic migrations: users, organizations

**Вторник (Backend Dev):**
- [ ] FastAPI setup
- [ ] Auth endpoints (/login, /register)
- [ ] JWT middleware

**Среда (Frontend Dev):**
- [ ] npm install: react@19, react-query, zustand, react-router
- [ ] Создать lib/api.ts
- [ ] Создать store/authStore.ts

**Четверг (Frontend Dev):**
- [ ] LoginPage.tsx
- [ ] React Router setup
- [ ] App.tsx рефакторинг

**Пятница (Integration):**
- [ ] E2E тест: login через UI
- [ ] Cleanup + documentation

---

## 📚 Reading Order

Для нового разработчика в команде:

1. **Start:** [../prd.md](../prd.md) - понять видение продукта
2. **Current State:** [frontend-audit.md](./frontend-audit.md) - что уже есть
3. **Plan:** [phase1-roadmap-detailed.md](./phase1-roadmap-detailed.md) - план на 12 недель
4. **Differentiation:** [product-improvements.md](./product-improvements.md) - почему мы лучше Cursor
5. **Implementation:** [frontend-tasks-weekly.md](./frontend-tasks-weekly.md) - конкретные задачи

---

## 🎨 Design System

Frontend использует:
- **Colors:**
  - Background: `#0D1117`
  - Cards: `#161B22`
  - Borders: `#30363D`
  - Primary: `#00D4FF` (cyan)
  - Secondary: `#7C3AED` (purple)
- **Typography:** Monospace font (GitHub-style)
- **Components:** shadcn/ui (Radix UI + Tailwind)
- **Icons:** lucide-react

**Не переделывать UI** - он отличный. Фокус на архитектуре и интеграции.

---

## ⚠️ Important Notes

### Backend Development
- **100% async** - использовать asyncio, asyncpg, aioredis
- **Type hints везде** - Pydantic models для API
- **Testing** - pytest-asyncio, coverage > 70%
- **Security** - OWASP Top 10 checklist

### Frontend Development
- **Не удалять существующий UI** - только рефакторинг
- **TypeScript strict mode** - включить в tsconfig.json
- **React Query для API** - не useState для async data
- **Zustand только для auth/UI state** - не для server state

### Product Strategy
- **Backend first** - фронт интегрируется после
- **MVP фичи** - не over-engineer в Phase 1
- **User feedback** - пилотные команды с Week 10
- **Cursor competitor** - но с уникальными фичами (см. product-improvements.md)

---

## 📞 Communication

### Daily Standup (15 min)
- Что сделано вчера?
- Что делаю сегодня?
- Есть блокеры?

### Weekly Demo (пятница)
- Демо новых фич
- Review кода
- Обновление roadmap

### Documentation
- Код должен быть self-documenting
- Сложная логика → комментарии
- API changes → обновить swagger

---

## 🎯 Success Criteria (End of Phase 1)

### Technical
- ⚡ API p95 latency < 500ms
- 🔒 0 критических security issues
- 📊 Test coverage > 70%
- 🐛 < 5 критических багов/неделю

### Product
- 👥 3-10 пилотных команд активны
- ✅ Plan acceptance rate > 60%
- ⏱️ Time saved: 10+ часов/dev/неделю
- 💬 NPS > 7/10

### Business
- 📈 User retention > 70% (week 2)
- 🚀 1+ команда конвертируется в платную подписку
- 💰 MRR > $1000

---

## 🔮 Vision: Repa in 1 Year

```
Phase 1 (0-3 мес):  Cursor Clone + Web UI
Phase 2 (3-6 мес):  Multi-Agent Platform (PM, Marketing, SEO)
Phase 3 (6-12 мес): Full Product Lifecycle Management

Result: "Product Acceleration Platform" - не просто dev tool
```

**Это не coding assistant. Это платформа для всей продуктовой команды.**

---

## ✅ Next Steps

1. **Read all docs** - понять полную картину
2. **Setup development environment**
   - Docker Compose
   - Backend Python 3.12
   - Frontend Node.js 20+
3. **Start with Week 1 tasks**
   - Backend: auth system
   - Frontend: React Router + API client
4. **Daily commits** - маленькие итерации
5. **Weekly demos** - показывать прогресс

**Let's build something amazing! 🚀**
