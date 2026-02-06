# Activity System - Требования и спецификация

**Статус:** 📋 Планируется
**Приоритет:** Medium
**Требует:** Backend + Frontend работы

---

## Обзор

Activity System - это унифицированная лента активности, которая показывает пользователю все операции в системе в хронологическом порядке.

**Текущее состояние:** Mock данные на Dashboard для UI демонстрации

**Целевое состояние:** Реальная интеграция с различными типами операций

---

## Типы активностей

### 1. План (Plan)
Генерация плана изменений AI

**Данные:**
- ID плана
- Название задачи
- Статус (pending/completed/failed)
- Сложность (low/medium/high)
- Количество затронутых файлов
- Timestamp создания

**Действия:**
- **VIEW** → Навигация на `/projects/{projectId}/plans/{planId}`
- **APPLY** → Генерация и применение всех diff'ов плана

### 2. Diff Application
Применение изменений к файлу

**Данные:**
- ID diff'а
- Путь к файлу
- Статус (pending/applied/rejected/failed)
- Тип действия (modify/create/delete)
- Связанный план
- Timestamp применения

**Действия:**
- **VIEW** → Показать diff в модальном окне
- **REVERT** → Откатить изменения (если применен)

### 3. Indexing Job
Процесс индексации репозитория

**Данные:**
- ID job'а
- ID проекта
- Статус (running/completed/failed)
- Прогресс (%)
- Количество обработанных файлов
- Текущий файл (для running)
- Timestamp старта/завершения

**Действия:**
- **VIEW** → Показать детали индексации
- **CANCEL** → Остановить running job

### 4. Git Sync
Синхронизация с удаленным репозиторием

**Данные:**
- ID проекта
- Тип операции (pull/push/clone)
- Статус (success/failed)
- Количество изменений
- Commit hash
- Timestamp

**Действия:**
- **VIEW** → Показать git log
- **RETRY** → Повторить операцию (если failed)

---

## Backend API Requirements

### Endpoint: GET /api/v1/activities

**Query Parameters:**
```typescript
{
  limit?: number;          // Default: 20
  offset?: number;         // Default: 0
  type?: ActivityType[];   // Filter by types
  project_id?: string;     // Filter by project
  status?: string;         // Filter by status
  since?: datetime;        // Activities after this timestamp
}
```

**Response:**
```typescript
interface ActivityResponse {
  activities: Activity[];
  total: number;
  has_more: boolean;
}

interface Activity {
  id: string;
  type: 'plan' | 'diff' | 'indexing' | 'git_sync';
  timestamp: string;
  status: 'pending' | 'running' | 'completed' | 'failed';

  // Common fields
  project_id: string;
  project_name: string;
  user_id: string;

  // Type-specific metadata
  metadata: PlanMetadata | DiffMetadata | IndexingMetadata | GitSyncMetadata;

  // Progress (for running operations)
  progress?: {
    current: number;
    total: number;
    percentage: number;
  };

  // Error info (for failed)
  error?: {
    message: string;
    code: string;
    details?: any;
  };
}
```

### Backend Implementation Tasks

1. **Database Schema**
   ```sql
   CREATE TABLE activities (
     id UUID PRIMARY KEY,
     type VARCHAR(50) NOT NULL,
     timestamp TIMESTAMP NOT NULL,
     status VARCHAR(50) NOT NULL,
     project_id UUID NOT NULL,
     user_id UUID NOT NULL,
     metadata JSONB NOT NULL,
     created_at TIMESTAMP DEFAULT NOW(),
     updated_at TIMESTAMP DEFAULT NOW()
   );

   CREATE INDEX idx_activities_project_timestamp
     ON activities(project_id, timestamp DESC);
   CREATE INDEX idx_activities_user_timestamp
     ON activities(user_id, timestamp DESC);
   CREATE INDEX idx_activities_type_status
     ON activities(type, status);
   ```

2. **Activity Aggregation Service**
   - Собирает данные из разных таблиц (plans, diffs, indexing_jobs, git_operations)
   - Нормализует в единый формат Activity
   - Сортирует по timestamp
   - Поддерживает pagination и фильтрацию

3. **Real-time Updates (Optional)**
   - WebSocket канал для live обновлений
   - Push уведомления при изменении статуса
   - Server-Sent Events как альтернатива

---

## Frontend Implementation

### 1. React Hook: useActivities

```typescript
// hooks/useActivities.ts
export function useActivities(options?: {
  limit?: number;
  projectId?: string;
  type?: ActivityType[];
  autoRefresh?: boolean;
}) {
  return useQuery({
    queryKey: ['activities', options],
    queryFn: async () => {
      const response = await activitiesAPI.list(options);
      return response.data;
    },
    refetchInterval: options?.autoRefresh ? 5000 : false,
  });
}
```

### 2. Activity Card Component

```typescript
interface ActivityCardProps {
  activity: Activity;
  onView: (id: string) => void;
  onAction: (id: string, action: string) => void;
}

export function ActivityCard({ activity, onView, onAction }: ActivityCardProps) {
  // Render based on activity.type
  // Show appropriate status badge
  // Display progress bar for running operations
  // Render action buttons based on type and status
}
```

### 3. Dashboard Integration

**Заменить mock activities:**

```typescript
// Dashboard.tsx
const { data: activities, isLoading } = useActivities({
  limit: 5,
  autoRefresh: true
});

// Render real activities
{activities?.activities.map((activity) => (
  <ActivityCard
    key={activity.id}
    activity={activity}
    onView={(id) => handleViewActivity(id, activity.type)}
    onAction={(id, action) => handleActivityAction(id, action, activity.type)}
  />
))}
```

---

## UI/UX Considerations

### Status Indicators

**Colors:**
- 🟡 Pending: Yellow
- 🔵 Running: Blue (with pulse animation)
- 🟢 Completed: Green
- 🔴 Failed: Red

**Icons:**
- Plan: `<FileCode />`
- Diff: `<GitCommit />`
- Indexing: `<Database />`
- Git Sync: `<GitBranch />`

### Progress Display

**Running operations показывают:**
- Progress bar (0-100%)
- Current status text ("Processing file 47/120")
- Elapsed time
- Cancel button (if applicable)

### Empty States

**Когда нет активностей:**
```
🎉 Всё спокойно!
Здесь будут отображаться ваши операции:
планы, применение изменений, индексация.
```

---

## API Routes (Backend)

### Required Endpoints

```python
# backend/src/api/v1/activities.py

@router.get("/activities", response_model=ActivityResponse)
async def list_activities(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    type: Optional[List[ActivityType]] = Query(None),
    project_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List user's activities with filtering and pagination"""
    pass

@router.get("/activities/{activity_id}", response_model=Activity)
async def get_activity(
    activity_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get activity details"""
    pass

@router.post("/activities/{activity_id}/cancel")
async def cancel_activity(
    activity_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Cancel a running activity (if supported)"""
    pass
```

### Service Layer

```python
# backend/src/services/activity_service.py

class ActivityService:
    async def get_activities(
        self,
        user_id: UUID,
        limit: int,
        offset: int,
        filters: ActivityFilters
    ) -> ActivityResponse:
        # Aggregate from multiple sources
        plans = await self._get_recent_plans(user_id, filters)
        diffs = await self._get_recent_diffs(user_id, filters)
        indexing = await self._get_recent_indexing(user_id, filters)
        git_ops = await self._get_recent_git_ops(user_id, filters)

        # Normalize and merge
        activities = self._normalize_activities([
            *plans, *diffs, *indexing, *git_ops
        ])

        # Sort by timestamp
        activities.sort(key=lambda x: x.timestamp, reverse=True)

        # Paginate
        return ActivityResponse(
            activities=activities[offset:offset+limit],
            total=len(activities),
            has_more=offset + limit < len(activities)
        )
```

---

## Migration Plan

### Phase 1: Backend Foundation (Estimate: 2-3 days)
1. ✅ Create activities database table
2. ✅ Implement ActivityService aggregation
3. ✅ Create API endpoints
4. ✅ Add unit tests
5. ✅ Test with Postman/curl

### Phase 2: Frontend Integration (Estimate: 1-2 days)
1. ✅ Create useActivities hook
2. ✅ Create ActivityCard component
3. ✅ Integrate into Dashboard
4. ✅ Remove mock activities
5. ✅ Add loading/error states

### Phase 3: Real-time Updates (Optional, Estimate: 1 day)
1. ✅ WebSocket integration
2. ✅ Auto-refresh on status changes
3. ✅ Push notifications

### Phase 4: Polish (Estimate: 0.5 day)
1. ✅ Empty states
2. ✅ Error handling
3. ✅ Animations
4. ✅ Keyboard shortcuts (Cmd+R to refresh)

**Total Estimate:** 4-6 days of development time

---

## Testing Strategy

### Backend Tests
```python
def test_list_activities_empty():
    # New user should have no activities
    pass

def test_list_activities_pagination():
    # Test limit/offset
    pass

def test_list_activities_filter_by_type():
    # Filter by plan/diff/indexing
    pass

def test_activity_aggregation_order():
    # Most recent first
    pass
```

### Frontend Tests
```typescript
describe('ActivityCard', () => {
  it('renders plan activity correctly', () => {});
  it('shows progress for running operations', () => {});
  it('displays error message for failed activities', () => {});
  it('calls onView when VIEW button clicked', () => {});
});
```

---

## Security Considerations

1. **Authorization**
   - Users can only see their own activities
   - Admins can see all org activities
   - Proper JWT validation

2. **Rate Limiting**
   - Max 100 requests per minute per user
   - Prevents abuse of auto-refresh

3. **Data Privacy**
   - Don't expose sensitive file contents in metadata
   - Sanitize error messages
   - Filter deleted projects

---

## Performance Optimization

### Database
- Indexed queries on (project_id, timestamp)
- Consider materialized views for aggregation
- Cleanup old activities (retention policy: 90 days)

### Caching
```python
@cache(ttl=60)  # Cache for 1 minute
async def get_user_activities(user_id: UUID):
    # Expensive aggregation
    pass
```

### Pagination
- Always use limit/offset
- Default limit: 20 (balance between UX and performance)
- Max limit: 100

---

## Future Enhancements

### 1. Activity Filtering UI
- Dropdown to filter by type
- Date range picker
- Status filter buttons

### 2. Activity Search
- Full-text search across activity metadata
- Search by file name, commit hash, etc.

### 3. Activity Export
- Export to JSON/CSV
- For audit logs
- For analytics

### 4. Activity Grouping
- Group related activities (plan + its diffs)
- Collapsible groups
- "Show all X diffs for this plan"

---

## Current Workaround (Mock Data)

**На данный момент:**
- Dashboard использует mock activities для UI демонстрации
- Кнопки показывают toast уведомления
- Это позволяет продемонстрировать UX без backend работы

**Файл:** `frontend/src/app/components/Dashboard.tsx` (lines 16-43)

**Mock данные:**
```typescript
const activities = [
  {
    id: 1,
    title: 'Патч "JWT Auth"',
    repo: 'repo/next-dash',
    progress: 87,
    time: '2 мин. назад',
    details: '3 файла, 47 строк изменено',
    status: 'running',
  },
  // ... more mock activities
];
```

---

## Decision Points

### When to implement?

**Implement when:**
- ✅ Users need visibility into their operations
- ✅ Multiple concurrent operations are common
- ✅ Debugging requires operation history

**Can wait if:**
- ⏸️ Single-user MVP phase
- ⏸️ Operations are instant (no async jobs)
- ⏸️ Other features are higher priority

**Current Recommendation:**
Phase 1-2 (backend + basic frontend) should be implemented before public beta. Real-time updates can wait for v2.

---

## Related Documentation

- [Week 6 Continued Work](WEEK6_CONTINUED_WORK.md) - Current implementation status
- [API Documentation](../backend/docs/API.md) - Existing API endpoints
- [Frontend Architecture](FRONTEND_ARCHITECTURE.md) - Component structure

---

**Document Created:** 2026-02-06
**Author:** Claude Sonnet 4.5
**Status:** Planning Document

---

**Next Steps:**
1. Review and approve requirements
2. Create backend tickets
3. Estimate sprint allocation
4. Begin Phase 1 implementation
