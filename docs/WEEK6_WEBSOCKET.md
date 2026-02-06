# Week 6: WebSocket Real-Time Progress Streaming

## Обзор

Реализован real-time прогресс стриминг для долгих операций через WebSocket. Теперь пользователь может видеть прогресс индексации и генерации планов в реальном времени.

## Что реализовано

### Backend

#### 1. Job Manager (`backend/src/services/job_manager.py`)
- **JobManager** - Singleton для управления фоновыми задачами
- **Job** - Класс для представления задач с прогрессом
- Publisher-Subscriber pattern через `asyncio.Queue`
- Поддержка прогресса, статусов (pending, running, completed, failed, cancelled)
- WebSocket subscribers для реального времени

```python
# Создание job
job = job_manager.create_job(
    name="Indexing Project",
    task_func=indexing_function,
    project_id=project_id
)

# Запуск job
job_manager.start_job(job.id)

# Обновление прогресса внутри task_func
await progress_callback(50, 100, "Processing file.py")
```

#### 2. WebSocket Endpoint (`backend/src/api/v1/websocket.py`)
- Эндпоинт: `ws://localhost:8000/api/v1/jobs/{job_id}?token={auth_token}`
- Аутентификация через query parameter `token`
- Типы сообщений:
  - `init` - Начальная информация о job
  - `started` - Job запущен
  - `progress` - Обновление прогресса
  - `completed` - Job завершен успешно
  - `error` - Ошибка выполнения
  - `cancelled` - Job отменен
  - `heartbeat` - Keepalive (каждые 30 сек)

#### 3. Обновленные API

**Indexing API** (`backend/src/api/v1/projects.py`):
```python
# POST /api/v1/projects/{project_id}/index
# Ответ:
{
  "job_id": "uuid",
  "project_id": "uuid",
  "project_name": "My Project",
  "message": "Connect to WebSocket at /api/v1/jobs/{job_id}"
}
```

**Plan Generation API** (`backend/src/api/v1/plans.py`):
```python
# POST /api/v1/plans/generate
# Ответ:
{
  "job_id": "uuid",
  "plan_id": "uuid",
  "project_id": "uuid",
  "task": "Add authentication",
  "message": "Connect to WebSocket at /api/v1/jobs/{job_id}"
}
```

#### 4. Обновленные Services

**IndexingService** - поддержка `progress_callback`:
```python
await indexing_service.index_project(
    project_id,
    repo_path,
    progress_callback=progress_callback  # опционально
)
```

**PlanGenerationService** - поддержка `progress_callback`:
```python
await plan_service.generate_plan(
    task=task,
    project_id=project_id,
    search_service=search_service,
    progress_callback=progress_callback  # опционально
)
```

### Frontend

#### 1. WebSocket Client (`frontend/src/lib/websocket.ts`)
- **JobWebSocket** class с автоматическим переподключением
- Обработка всех типов сообщений
- Reconnection logic (3 попытки с задержкой 1 сек)

```typescript
const ws = connectToJob(jobId, token, {
  onUpdate: (update) => console.log(update),
  onComplete: (result) => console.log('Done!', result),
  onError: (error) => console.error('Error:', error),
});
```

#### 2. React Hooks (`frontend/src/hooks/useJobStream.ts`)

**useJobStream** - базовый хук:
```tsx
const { progress, isConnected, connect, disconnect } = useJobStream({
  onComplete: (result) => refetchData(),
  onError: (error) => showError(error)
});

// Подключение
connect(jobId);

// Прогресс
console.log(progress.percentage, progress.message);
```

**useAutoJobStream** - автоматическое подключение:
```tsx
const { progress, isConnected } = useAutoJobStream(jobId, {
  onComplete: () => refetchProjects()
});
```

#### 3. Progress Components (`frontend/src/app/components/JobProgress.tsx`)

**JobProgress** - полный компонент прогресса:
```tsx
<JobProgress
  progress={progress}
  showDetails={true}
/>
```

**CompactJobProgress** - компактный inline:
```tsx
<CompactJobProgress progress={progress} />
```

## Как использовать

### Backend API

1. **Запустить долгую операцию:**
```bash
# Индексация
POST /api/v1/projects/{project_id}/index
# Получаем job_id

# Генерация плана
POST /api/v1/plans/generate
# Получаем job_id
```

2. **Подключиться к WebSocket:**
```javascript
const ws = new WebSocket(
  `ws://localhost:8000/api/v1/jobs/${jobId}?token=${authToken}`
);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update.type, update.data);
};
```

### Frontend Integration

```tsx
import { useAutoJobStream } from '../../hooks/useJobStream';
import { JobProgress } from './JobProgress';

function MyComponent() {
  const [jobId, setJobId] = useState<string | null>(null);

  const { progress, isConnected } = useAutoJobStream(jobId, {
    onComplete: () => {
      // Refresh data after completion
      refetchProjects();
    },
    onError: (error) => {
      alert(`Error: ${error}`);
    }
  });

  const handleStartIndexing = async () => {
    const response = await projectsAPI.startIndexing(projectId);
    setJobId(response.data.job_id);
  };

  return (
    <>
      <button onClick={handleStartIndexing}>
        Start Indexing
      </button>

      {progress && <JobProgress progress={progress} />}
    </>
  );
}
```

## Архитектура

```
┌─────────────┐          ┌──────────────┐          ┌────────────┐
│   Frontend  │  HTTP    │   Backend    │          │ JobManager │
│             ├─────────►│ API Endpoint │──create─►│            │
│             │          │              │          │  Job Pool  │
└──────┬──────┘          └──────────────┘          └─────┬──────┘
       │                                                  │
       │ WebSocket                                        │
       │ /api/v1/jobs/{job_id}                           │
       │                                                  │
       └──────────────────────────────────────────────►  │
                                                          │
                                          ┌───────────────▼────────┐
                                          │  Background Worker     │
                                          │  - Run task_func       │
                                          │  - Update progress     │
                                          │  - Broadcast to WS     │
                                          └────────────────────────┘
```

## Преимущества

1. **Real-Time Updates** - Мгновенное обновление прогресса без polling
2. **Низкая нагрузка** - WebSocket более эффективен чем HTTP polling
3. **Масштабируемость** - JobManager может управлять множеством задач
4. **Переиспользование** - Легко добавить streaming к любой долгой операции
5. **Отказоустойчивость** - Автоматическое переподключение при разрыве

## Следующие шаги

- [ ] Интегрировать JobProgress в Projects.tsx для отображения прогресса индексации
- [ ] Интегрировать в PlanGeneration.tsx для прогресса генерации планов
- [ ] Добавить JobProgress в DiffGeneration для генерации diffs
- [ ] Добавить отмену задач (Cancel Job)
- [ ] Персистентность jobs в базе данных (опционально)
- [ ] Rate limiting для WebSocket connections

## Тестирование

1. Запустить backend:
```bash
cd backend
python -m uvicorn src.main:app --reload
```

2. Запустить frontend:
```bash
cd frontend
npm run dev
```

3. Создать проект и запустить индексацию
4. Открыть WebSocket DevTools в браузере
5. Наблюдать real-time сообщения прогресса

## Заметки

- WebSocket подключается автоматически при получении `job_id`
- Токен аутентификации передается через query parameter `?token=`
- При разрыве соединения происходит автоматическое переподключение (3 попытки)
- После completion/error WebSocket закрывается автоматически
- Heartbeat каждые 30 секунд предотвращает таймауты
