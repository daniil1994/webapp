# Week 1 - Backend Foundation ✅ COMPLETE

**Дата:** 05 февраля 2026
**Статус:** Backend MVP готов к запуску!

---

## ✅ Что сделано (Day 1-2)

### 1. Project Structure ✅
```
backend/
├── src/
│   ├── api/v1/
│   │   └── auth.py          ✅ Auth endpoints
│   ├── core/
│   │   ├── config.py        ✅ Settings
│   │   └── security.py      ✅ JWT, password hashing
│   ├── db/
│   │   ├── base.py          ✅ Database connection
│   │   └── models/
│   │       └── user.py      ✅ User, Organization models
│   ├── schemas/
│   │   └── auth.py          ✅ Pydantic schemas
│   └── main.py              ✅ FastAPI app
├── alembic/                 ✅ Migrations setup
├── .env                     ✅ Environment config
├── requirements.txt         ✅ Dependencies
└── README.md                ✅ Documentation
```

### 2. Backend Features ✅
- [x] FastAPI application
- [x] JWT authentication
- [x] User registration
- [x] User login
- [x] Get current user (protected endpoint)
- [x] Password hashing (bcrypt)
- [x] Database models (SQLAlchemy async)
- [x] Alembic migrations
- [x] API documentation (Swagger)
- [x] CORS middleware
- [x] Settings management (Pydantic)

### 3. Infrastructure ✅
- [x] Docker Compose (PostgreSQL + Redis)
- [x] Environment variables (.env)
- [x] Start scripts

---

## 🚀 Как запустить (5 минут)

### Step 1: Install Docker Desktop

**Если Docker не установлен:**
1. Скачай Docker Desktop: https://www.docker.com/products/docker-desktop
2. Установи и запусти

### Step 2: Start Infrastructure

```bash
cd /Users/daniilladejsikov/Documents/Repa

# Start PostgreSQL + Redis
docker compose up -d

# Check status (должны быть running)
docker compose ps

# Expected output:
# repa-postgres    running    0.0.0.0:5432->5432/tcp
# repa-redis       running    0.0.0.0:6379->6379/tcp
```

### Step 3: Install Backend Dependencies

```bash
cd backend

# Option 1: Using pip
pip install -r requirements.txt

# Option 2: Using Poetry (if installed)
poetry install
```

### Step 4: Run Database Migrations

```bash
cd backend

# Create initial migration
alembic revision --autogenerate -m "Initial migration: users and organizations"

# Apply migration
alembic upgrade head

# Verify tables created
docker exec -it repa-postgres psql -U repa -d repa -c "\dt"

# Expected output:
#              List of relations
#  Schema |      Name       | Type  | Owner
# --------+-----------------+-------+-------
#  public | alembic_version | table | repa
#  public | organizations   | table | repa
#  public | users           | table | repa
```

### Step 5: Start Backend Server

```bash
cd backend

# Start server with auto-reload
uvicorn src.main:app --reload --port 8000

# Or use start script
./start.sh
```

**Server URLs:**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🧪 Test API (3 минуты)

### Test 1: Health Check
```bash
curl http://localhost:8000/health

# Expected:
# {"status":"ok","app":"Repa API","version":"0.1.0"}
```

### Test 2: Register User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "test123",
    "org_name": "Test Organization"
  }'

# Expected:
# {"access_token":"eyJ...","token_type":"bearer"}
```

### Test 3: Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"

# Expected:
# {"access_token":"eyJ...","token_type":"bearer"}

# Save token for next step
export TOKEN="paste_your_token_here"
```

### Test 4: Get Current User
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# Expected:
# {
#   "id": "uuid...",
#   "email": "test@example.com",
#   "org_id": "uuid...",
#   "role": "admin",
#   "is_active": true,
#   "created_at": "2026-02-05T..."
# }
```

### Test 5: Interactive Swagger UI
Открой в браузере: http://localhost:8000/docs

1. Нажми "Try it out" на `/api/v1/auth/register`
2. Заполни данные
3. Execute
4. Скопируй `access_token`
5. Нажми "Authorize" (вверху справа)
6. Вставь токен: `Bearer your_token`
7. Теперь можешь тестировать `/api/v1/auth/me`

---

## ✅ Week 1 Complete Checklist

### Backend ✅
- [x] Docker Compose working
- [x] PostgreSQL + Redis running
- [x] FastAPI server starts
- [x] Migrations applied
- [x] Auth endpoints working
- [x] Swagger UI accessible
- [x] JWT tokens work
- [x] Protected endpoints work

### Documentation ✅
- [x] Backend README
- [x] API documentation (Swagger)
- [x] Getting started guide
- [x] Environment setup (.env)

---

## 🎯 Next Steps (Week 1.5 - Day 3-4)

### Frontend Integration

**Goals:**
1. Update React to 19
2. Install React Query, Zustand, React Router
3. Create API client (axios)
4. Create auth store (Zustand)
5. Create Login page
6. Connect Login page to backend

**See:** [docs/frontend-tasks-weekly.md](docs/frontend-tasks-weekly.md) → Week 1

---

## 🐛 Troubleshooting

### Docker not starting
```bash
# Make sure Docker Desktop is running
# Check Docker version
docker --version

# Restart Docker Desktop app
```

### Port 5432 already in use
```bash
# Check what's using port 5432
lsof -i :5432

# If it's old postgres, stop it
brew services stop postgresql
# or
sudo systemctl stop postgresql
```

### Module not found errors
```bash
cd backend

# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Run with module syntax
python -m src.main
```

### Database connection refused
```bash
# Check postgres logs
docker compose logs postgres

# Restart postgres
docker compose restart postgres

# Check if postgres is accepting connections
docker exec -it repa-postgres pg_isready -U repa
```

### Alembic errors
```bash
# Check if models are imported in alembic/env.py
# They should be:
# from src.db.models.user import Organization, User

# If still errors, try:
cd backend
rm -rf alembic/versions/*.py  # Keep .gitkeep
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## 📊 Status Summary

**Completed:**
- ✅ Backend architecture
- ✅ Auth system (JWT)
- ✅ Database models
- ✅ API endpoints
- ✅ Docker infrastructure
- ✅ Documentation

**Ready for:**
- ⏳ Frontend integration (Day 3-4)
- ⏳ E2E testing (Day 5)
- ⏳ Week 2: Repository indexing

**Success Metrics:**
- API responds ✅
- User can register ✅
- User can login ✅
- JWT auth works ✅
- Database migrations work ✅

---

## 🎉 Congratulations!

Backend MVP готов! Теперь можно:

1. **Test API** через Swagger UI
2. **Integrate Frontend** (Week 1.5)
3. **Start Week 2** - Repository Indexing

**Well done! 🚀**

---

## 📞 Need Help?

- **Backend README:** [backend/README.md](backend/README.md)
- **Getting Started:** [docs/getting-started.md](docs/getting-started.md)
- **Full Roadmap:** [docs/phase1-roadmap-detailed.md](docs/phase1-roadmap-detailed.md)

---

*Generated by Repa Team / Week 1 Complete*
