# Week 5: Chat Backend with RAG Integration

## Обзор

Реализован полноценный backend для чата с интеграцией LLM (z.ai) и RAG (Retrieval-Augmented Generation) для контекстно-зависимых ответов на основе кодовой базы проекта.

## Что реализовано

### 1. Database Model ([backend/src/db/models/chat_message.py](../backend/src/db/models/chat_message.py))

Создана модель `ChatMessage` для хранения истории чата:

```python
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    context_chunks = Column(Text, nullable=True)  # JSON string of chunk IDs
    created_at = Column(DateTime, default=datetime.utcnow)
```

**Особенности:**
- UUID primary keys для безопасности
- Cascade delete при удалении проекта/пользователя
- Индексы на project_id, user_id, created_at для производительности
- Хранение IDs контекстных chunks для отслеживания RAG

### 2. Chat Service ([backend/src/services/chat_service.py](../backend/src/services/chat_service.py))

Сервис объединяет RAG и LLM для генерации ответов:

```python
class ChatService:
    async def send_message(
        self,
        project_id: UUID,
        user: User,
        content: str,
        use_rag: bool = True,
        top_k_chunks: int = 5,
    ) -> ChatMessage
```

**Workflow:**

1. **Сохранение user message** в БД
2. **RAG поиск** (если включен):
   - Использует `CodeSearchService` для поиска релевантных code chunks
   - Cosine similarity с минимальным порогом 0.7
   - Возвращает top-K наиболее релевантных кусков кода
3. **Формирование контекста**:
   - Извлечение последних 10 сообщений для conversation context
   - Форматирование code chunks с file paths и line numbers
4. **LLM генерация**:
   - Отправка system prompt + user prompt в LLM
   - Использует `get_llm_client()` (поддерживает z.ai/Claude/GPT-4)
5. **Сохранение assistant message** в БД

**Методы:**
- `send_message()` - отправка сообщения и получение ответа
- `get_chat_history()` - получение истории с pagination
- `delete_message()` - удаление конкретного сообщения
- `clear_chat_history()` - очистка всей истории для проекта

### 3. LLM Client ([backend/src/services/llm_client.py](../backend/src/services/llm_client.py))

**Уже существовал**, поддерживает:
- **Z.AI** (GLM-4.7) - используется по умолчанию
- **Anthropic Claude** (Sonnet 4.5)
- **OpenAI** (GPT-4)

```python
def get_llm_client() -> LLMClient:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "zai" or provider == "z.ai":
        return ZAIClient()
    elif provider == "openai":
        return OpenAIClient()
    elif provider == "anthropic" or provider == "claude":
        return ClaudeClient()
```

**Z.AI Configuration** (из `.env`):
```bash
LLM_PROVIDER=zai
ZAI_API_KEY=d14ca4e2c655498db428664a3412abc0.S9yfoUmWTJYzQdgn
ZAI_MODEL=glm-4.7
ZAI_BASE_URL=https://api.z.ai/api/paas/v4
```

### 4. Chat API ([backend/src/api/v1/chat.py](../backend/src/api/v1/chat.py))

Реализованы 4 endpoint:

#### POST `/api/v1/projects/{project_id}/chat`
Отправка сообщения и получение AI ответа.

**Request:**
```json
{
  "content": "How does JWT authentication work?",
  "use_rag": true,
  "top_k_chunks": 5
}
```

**Response:**
```json
{
  "id": "uuid",
  "project_id": "uuid",
  "user_id": "uuid",
  "role": "assistant",
  "content": "# JWT Authentication...",
  "context_chunks": "chunk_id1,chunk_id2,...",
  "created_at": "2026-02-06T12:00:00Z"
}
```

#### GET `/api/v1/projects/{project_id}/chat/history`
Получение истории чата.

**Query params:**
- `limit` (default: 50)
- `offset` (default: 0)

**Response:**
```json
{
  "messages": [...],
  "total": 42
}
```

#### DELETE `/api/v1/projects/{project_id}/chat/{message_id}`
Удаление конкретного сообщения.

#### DELETE `/api/v1/projects/{project_id}/chat`
Очистка всей истории чата для проекта.

### 5. Database Migration ([backend/alembic/versions/5b9c0d3e4f5g_add_chat_messages_table.py](../backend/alembic/versions/5b9c0d3e4f5g_add_chat_messages_table.py))

Создана Alembic миграция для `chat_messages` таблицы:

```bash
cd backend
python3 -m alembic upgrade head
```

**Результат:**
```
INFO  [alembic.runtime.migration] Running upgrade 4a8b9c1d2e3f -> 5b9c0d3e4f5g, add_chat_messages_table
```

### 6. Frontend Integration ([frontend/src/lib/api.ts](../frontend/src/lib/api.ts))

Добавлен `chatAPI` клиент:

```typescript
export const chatAPI = {
  sendMessage: (projectId: string, message: ChatMessageCreate) =>
    apiClient.post<ChatMessage>(`/api/v1/projects/${projectId}/chat`, message),

  getHistory: (projectId: string, limit = 50, offset = 0) =>
    apiClient.get<ChatHistoryResponse>(`/api/v1/projects/${projectId}/chat/history`),

  deleteMessage: (projectId: string, messageId: string) =>
    apiClient.delete(`/api/v1/projects/${projectId}/chat/${messageId}`),

  clearHistory: (projectId: string) =>
    apiClient.delete(`/api/v1/projects/${projectId}/chat`),
};
```

### 7. Updated ProjectDetail Component ([frontend/src/app/components/ProjectDetail.tsx](../frontend/src/app/components/ProjectDetail.tsx))

**Ключевые изменения:**

1. **Load Chat History on Mount**:
```typescript
useEffect(() => {
  const loadChatHistory = async () => {
    const response = await chatAPI.getHistory(projectId.toString(), 50, 0);
    setChatMessages(response.data.messages.map(msg => ({
      id: msg.id,
      role: msg.role,
      content: msg.content,
      timestamp: msg.created_at,
    })));
  };
  loadChatHistory();
}, [projectId]);
```

2. **Real API Integration**:
```typescript
const handleSendMessage = async () => {
  // Send message to backend
  const response = await chatAPI.sendMessage(projectId.toString(), {
    content: userMessageContent,
    use_rag: true,
    top_k_chunks: 5,
  });

  // Add assistant response to UI
  setChatMessages(prev => [...prev, response.data]);
};
```

3. **Loading States**:
- `isSending` - показывает когда идет отправка
- `isLoadingHistory` - показывает загрузку истории

## RAG Implementation Details

### How RAG Works

1. **User Query** → Embedding generation
2. **Vector Search** → pgvector cosine similarity
3. **Top-K Retrieval** → Most relevant code chunks
4. **Context Formatting** → Markdown format with metadata
5. **LLM Prompt** → System prompt + context + user query
6. **AI Response** → Generated answer with code references

### Example RAG Context

```markdown
**File:** `backend/src/api/v1/auth.py` (Lines 45-62)
**Type:** function
**Similarity:** 0.89
```
async def login(form_data: OAuth2PasswordRequestForm):
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token}
```

---

**File:** `backend/src/core/security.py` (Lines 12-25)
**Type:** function
**Similarity:** 0.82
```
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```
```

### System Prompt

```
You are an AI coding assistant helping developers understand and work with their codebase.

Your capabilities:
- Answer questions about code structure, functionality, and patterns
- Explain how specific code sections work
- Suggest improvements and best practices
- Help debug issues and find bugs
- Provide code examples when helpful

Guidelines:
- Be concise but thorough in explanations
- Use markdown formatting for code blocks with language tags
- Reference specific file paths and line numbers when discussing code
- If you're not sure about something, say so
- Focus on being helpful and educational

## Relevant Code Context

[RAG context injected here]
```

## Performance Optimizations

1. **Database Indexes**:
   - `ix_chat_messages_project_id` - для фильтрации по проекту
   - `ix_chat_messages_user_id` - для фильтрации по пользователю
   - `ix_chat_messages_created_at` - для сортировки по времени

2. **Vector Search**:
   - `min_similarity=0.7` - фильтрует нерелевантные chunks
   - `top_k=5` - ограничивает контекст для LLM

3. **Pagination**:
   - `limit` и `offset` для истории чата
   - Предотвращает загрузку тысяч сообщений

4. **Conversation Context**:
   - Только последние 10 сообщений
   - Truncate длинных сообщений до 500 символов

## Security Considerations

1. **Authorization**:
   - Все endpoints защищены JWT authentication
   - `get_current_user` dependency
   - User может видеть только свои сообщения

2. **Project Access**:
   - TODO: Implement proper project access control
   - Verify user belongs to project's organization

3. **Rate Limiting**:
   - TODO: Add rate limiting for chat messages
   - Prevent LLM API abuse

4. **Content Validation**:
   - Max message length: 10,000 characters
   - Pydantic validation on inputs

## Testing

### Manual Testing via API Docs

1. Открыть http://localhost:8000/docs
2. Authorize с JWT token
3. Найти `/api/v1/projects/{project_id}/chat` endpoint
4. Отправить тестовое сообщение:
```json
{
  "content": "Explain how authentication works",
  "use_rag": true,
  "top_k_chunks": 5
}
```

### Expected Response

AI должен вернуть markdown-formatted ответ с:
- Explanation на основе кодовой базы
- Code snippets из релевантных файлов
- File paths и line numbers
- Structured formatting (headings, lists, code blocks)

### Testing RAG

1. Index проект с помощью `/api/v1/projects/{id}/index`
2. Проверить что embeddings созданы: `/api/v1/search/stats/{project_id}`
3. Отправить chat message про конкретную функциональность
4. Verify что ответ содержит релевантный код из проекта

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │
│ (React + TS)│
└──────┬──────┘
       │ chatAPI.sendMessage()
       ▼
┌─────────────┐
│  Chat API   │
│ /chat POST  │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│ ChatService │─────▶│ CodeSearch   │
│             │      │ (RAG)        │
└──────┬──────┘      └──────────────┘
       │                    │
       │                    ▼
       │             ┌──────────────┐
       │             │  pgvector    │
       │             │  embeddings  │
       │             └──────────────┘
       ▼
┌─────────────┐
│ LLM Client  │
│  (z.ai)     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   z.ai API  │
│  GLM-4.7    │
└─────────────┘
```

## Files Changed/Created

### Backend
1. ✨ `backend/src/db/models/chat_message.py` - новая модель
2. ✨ `backend/src/services/chat_service.py` - новый сервис
3. ✨ `backend/src/api/v1/chat.py` - новый роутер
4. ✨ `backend/alembic/versions/5b9c0d3e4f5g_add_chat_messages_table.py` - миграция
5. ✏️ `backend/src/db/models/__init__.py` - добавлен ChatMessage
6. ✏️ `backend/src/db/models/project.py` - добавлен chat_messages relationship
7. ✏️ `backend/src/db/models/user.py` - добавлен chat_messages relationship
8. ✏️ `backend/src/main.py` - добавлен chat router

### Frontend
9. ✏️ `frontend/src/lib/api.ts` - добавлен chatAPI
10. ✏️ `frontend/src/app/components/ProjectDetail.tsx` - интеграция с API

### Documentation
11. ✨ `docs/WEEK5_CHAT_BACKEND.md` - этот файл

## Next Steps

1. **WebSocket Streaming**:
   - Real-time streaming ответов LLM
   - Показывать ответ по мере генерации (как ChatGPT)

2. **Project Access Control**:
   - Verify user belongs to project's organization
   - Implement proper authorization middleware

3. **Advanced RAG**:
   - Re-ranking алгоритмы для better context
   - Hybrid search (vector + keyword)
   - Multi-query retrieval

4. **Conversation Management**:
   - Conversation threads (отдельные чаты для разных задач)
   - Message editing
   - Regenerate response

5. **Analytics**:
   - Track most asked questions
   - Monitor LLM costs
   - Response quality metrics

6. **Rate Limiting**:
   - Redis-based rate limiter
   - Per-user и per-project limits

## Known Issues

⛔ **CRITICAL: Send Button Not Working (Unresolved)**
- Chat send button in UI does not respond to clicks
- onClick handler not being triggered
- See [KNOWN_ISSUES.md](KNOWN_ISSUES.md) for full details
- **Workaround**: Test via API docs (http://localhost:8000/docs) or curl

1. **Project Authorization**: Currently не проверяется доступ пользователя к проекту
2. **Error Handling**: Frontend показывает generic error message
3. **Long Responses**: Нет streaming, пользователь ждет весь ответ
4. **Context Window**: При большом количестве chunks может превысить LLM context limit

## Conclusion

Полноценный Chat Backend с RAG интеграцией реализован и работает. Пользователи могут:
- Задавать вопросы о кодовой базе
- Получать контекстно-зависимые ответы с code snippets
- Просматривать историю чата
- Использовать markdown formatting в сообщениях

Backend использует z.ai (GLM-4.7) по умолчанию, но легко переключается на Claude или GPT-4.
