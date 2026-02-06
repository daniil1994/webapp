# Getting Started - Quick Setup Guide
**Быстрый старт разработки Repa**

---

## Prerequisites

### Required Software
```bash
# Backend
Python 3.12+
Poetry (или pip)
Docker & Docker Compose

# Frontend
Node.js 20+ (LTS)
npm или pnpm

# Optional
VS Code (рекомендуется)
PostgreSQL client (TablePlus, pgAdmin)
```

### Проверка версий
```bash
python --version   # 3.12+
node --version     # v20+
docker --version   # 24+
docker-compose --version
```

---

## Week 1 Setup: Backend First

### Step 1: Clone & Structure (5 мин)

```bash
cd /Users/daniilladejsikov/Documents/Repa

# Создать backend структуру
mkdir -p backend/src/{api/v1,core,db/models,services}
mkdir -p backend/tests
mkdir -p backend/alembic/versions

# Создать CLI структуру (для Week 1.5)
mkdir -p cli/repa/commands
```

### Step 2: Backend Dependencies (10 мин)

**Создать:** `backend/pyproject.toml`
```toml
[tool.poetry]
name = "repa-backend"
version = "0.1.0"
description = "Repa Backend API"
authors = ["Your Team"]

[tool.poetry.dependencies]
python = "^3.12"
fastapi = "^0.115.0"
uvicorn = {extras = ["standard"], version = "^0.31.0"}
sqlalchemy = "^2.0.35"
asyncpg = "^0.30.0"
alembic = "^1.13.0"
pydantic = "^2.9.0"
pydantic-settings = "^2.5.0"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
python-multipart = "^0.0.12"
redis = {extras = ["hiredis"], version = "^5.1.0"}
openai = "^1.54.0"
httpx = "^0.27.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.3.0"
pytest-asyncio = "^0.24.0"
pytest-cov = "^6.0.0"
ruff = "^0.7.0"
black = "^24.10.0"
mypy = "^1.13.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Установка:**
```bash
cd backend
poetry install
# или
pip install -r requirements.txt  # если без Poetry
```

### Step 3: Docker Compose (5 мин)

**Создать:** `docker-compose.yml` (в корне проекта)
```yaml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: repa-postgres
    environment:
      POSTGRES_USER: repa
      POSTGRES_PASSWORD: repa_dev_password
      POSTGRES_DB: repa
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U repa"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: repa-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

**Запуск:**
```bash
docker-compose up -d

# Проверка
docker-compose ps
# Должны быть запущены: repa-postgres, repa-redis

# Логи
docker-compose logs -f postgres
```

### Step 4: Backend Config (10 мин)

**Создать:** `backend/src/core/config.py`
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Repa API"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://repa:repa_dev_password@localhost:5432/repa"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # OpenAI (для Phase 1)
    OPENAI_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
```

**Создать:** `backend/.env`
```env
DATABASE_URL=postgresql+asyncpg://repa:repa_dev_password@localhost:5432/repa
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-me
OPENAI_API_KEY=sk-...  # Ваш ключ
DEBUG=True
```

**Создать:** `backend/.env.example` (для git)
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/repa
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=change-me-in-production
OPENAI_API_KEY=sk-your-key-here
DEBUG=True
```

### Step 5: Database Models (15 мин)

**Создать:** `backend/src/db/base.py`
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from src.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**Создать:** `backend/src/db/models/user.py`
```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..base import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="member")  # member, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### Step 6: Alembic Setup (10 мин)

```bash
cd backend
alembic init alembic
```

**Обновить:** `backend/alembic.ini`
```ini
# Закомментировать эту строку:
# sqlalchemy.url = driver://user:pass@localhost/dbname

# Мы используем env.py для URL из .env
```

**Обновить:** `backend/alembic/env.py`
```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import asyncio

from src.core.config import settings
from src.db.base import Base
from src.db.models.user import Organization, User  # Импорт моделей

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Создать первую миграцию:**
```bash
cd backend
alembic revision --autogenerate -m "Create users and organizations tables"
alembic upgrade head

# Проверка
docker exec -it repa-postgres psql -U repa -d repa -c "\dt"
# Должны быть таблицы: alembic_version, organizations, users
```

### Step 7: FastAPI App (15 мин)

**Создать:** `backend/src/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}

@app.get("/")
async def root():
    return {"message": "Repa API v0.1.0"}

# TODO: добавить роуты auth, projects, plans
```

**Запуск:**
```bash
cd backend
uvicorn src.main:app --reload --port 8000

# Проверка
curl http://localhost:8000/health
# {"status":"ok","app":"Repa API"}

# Swagger UI
open http://localhost:8000/docs
```

### Step 8: Auth Implementation (30-40 мин)

**Создать:** `backend/src/core/security.py`
```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
```

**Создать:** `backend/src/api/v1/auth.py`
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from src.db.base import get_db
from src.db.models.user import User, Organization
from src.core.security import verify_password, get_password_hash, create_access_token
from src.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    org_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    email: str
    org_id: str
    role: str

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create organization
    org = Organization(name=user_data.org_name)
    db.add(org)
    await db.flush()

    # Create user
    user = User(
        org_id=org.id,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        role="admin"
    )
    db.add(user)
    await db.commit()

    # Create token
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    from src.core.security import verify_token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=str(user.id),
        email=user.email,
        org_id=str(user.org_id),
        role=user.role
    )
```

**Обновить:** `backend/src/main.py`
```python
from src.api.v1 import auth

app.include_router(auth.router, prefix="/api/v1")
```

**Тест:**
```bash
# Restart server
# Ctrl+C, затем
uvicorn src.main:app --reload --port 8000

# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","org_name":"Test Org"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=test@example.com&password=test123"

# Сохрани access_token
export TOKEN="eyJ..."

# Me
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

## Week 1 Setup: Frontend Integration

### Step 1: Frontend Dependencies (5 мин)

```bash
cd frontend

# Update React & add new deps
npm install react@19 react-dom@19
npm install @tanstack/react-query zustand react-router-dom axios

# Remove MUI (optional)
npm uninstall @mui/material @mui/icons-material @emotion/react @emotion/styled

# Install toast notifications
npm install sonner
```

### Step 2: Create Frontend Structure (2 мин)

```bash
cd frontend/src
mkdir -p lib hooks store types pages
```

### Step 3: Follow frontend-tasks-weekly.md

Остальные шаги детально описаны в [frontend-tasks-weekly.md](./frontend-tasks-weekly.md) → Week 1

---

## Troubleshooting

### Backend не запускается

**Problem:** `ModuleNotFoundError: No module named 'src'`
**Solution:**
```bash
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn src.main:app --reload
```

### Postgres connection refused

**Problem:** `could not connect to server`
**Solution:**
```bash
docker-compose down
docker-compose up -d
docker-compose ps  # Check status
docker-compose logs postgres
```

### Frontend не подключается к backend

**Problem:** CORS error
**Solution:** Проверь `backend/src/core/config.py`:
```python
CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
```

---

## Development Workflow

### Daily Work

```bash
# 1. Start services
docker-compose up -d

# 2. Start backend
cd backend
uvicorn src.main:app --reload --port 8000

# 3. Start frontend (new terminal)
cd frontend
npm run dev

# 4. Access
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Swagger: http://localhost:8000/docs
```

### Before Commit

```bash
# Backend
cd backend
ruff check .
black .
pytest

# Frontend
cd frontend
npm run build  # Check for TS errors
```

---

## Next Steps

После завершения Week 1 setup:

1. ✅ Backend auth работает
2. ✅ Frontend login page подключен
3. ✅ E2E flow: можно зарегистрироваться и залогиниться

**Переходи к Week 2:** Repository Indexing
- Backend: pgvector setup
- Backend: code embeddings
- Frontend: Projects page integration

**См.:** [phase1-roadmap-detailed.md](./phase1-roadmap-detailed.md) → Week 2-3

---

## Useful Commands

```bash
# Docker
docker-compose up -d         # Start all services
docker-compose down          # Stop all services
docker-compose ps            # List services
docker-compose logs -f       # Follow logs

# Postgres
docker exec -it repa-postgres psql -U repa -d repa
\dt                          # List tables
\d users                     # Describe table
SELECT * FROM users;         # Query

# Redis
docker exec -it repa-redis redis-cli
KEYS *                       # List all keys

# Backend
alembic revision --autogenerate -m "message"
alembic upgrade head
alembic downgrade -1

# Tests
pytest                       # Run all
pytest tests/test_auth.py    # Run specific
pytest --cov                 # With coverage
```

---

**Ready to start! 🚀**

Если возникнут проблемы - смотри [docs/README.md](./README.md) или пиши в team chat.
