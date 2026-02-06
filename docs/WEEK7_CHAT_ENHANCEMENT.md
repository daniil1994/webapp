# Week 7: Chat UI Enhancement

## Обзор

Реализована улучшенная система чата с поддержкой Markdown, syntax highlighting для code blocks и copy-to-clipboard функциональностью.

## Что реализовано

### 1. Установленные зависимости

```bash
npm install react-markdown react-syntax-highlighter @types/react-syntax-highlighter remark-gfm
```

**Пакеты:**
- `react-markdown` - рендеринг Markdown контента
- `react-syntax-highlighter` - подсветка синтаксиса для code blocks
- `@types/react-syntax-highlighter` - TypeScript типы
- `remark-gfm` - GitHub Flavored Markdown (таблицы, strikethrough, etc.)

### 2. ChatMessage Component (`frontend/src/app/components/ChatMessage.tsx`)

Новый компонент для отображения chat сообщений с rich formatting.

**Основные фичи:**

#### Markdown Rendering
```tsx
<ReactMarkdown
  remarkPlugins={[remarkGfm]}
  components={{
    code: CodeBlock,  // Custom syntax highlighting
    a: StyledLink,    // Styled links with target="_blank"
    ul: StyledList,   // Styled unordered lists
    h1-h3: StyledHeadings,  // Styled headings
  }}
>
  {content}
</ReactMarkdown>
```

#### Code Block с Syntax Highlighting
```tsx
<SyntaxHighlighter
  language={language}
  style={vscDarkPlus}  // VS Code dark theme
  showLineNumbers
  customStyle={{
    background: '#0D1117',
    fontSize: '0.8rem',
  }}
>
  {code}
</SyntaxHighlighter>
```

#### Copy-to-Clipboard
- Кнопка копирования для каждого code block
- Visual feedback (check icon на 2 секунды)
- Работает через `navigator.clipboard.writeText()`

#### Аватары User/Assistant
- User: синий аватар с иконкой User
- Assistant: серый аватар с иконкой Bot
- Сообщения выровнены справа/слева

#### Timestamps
- Опциональные timestamps для каждого сообщения
- Формат: `HH:MM:SS`

### 3. Обновленный ProjectDetail

**Изменения в `frontend/src/app/components/ProjectDetail.tsx`:**

#### Боковая панель чата
- Увеличена ширина с 320px до 384px (w-96)
- Заголовок "AI Assistant" вместо "Контекст задачи"
- Badge с количеством сообщений

#### Chat State Management
```tsx
const [chatMessages, setChatMessages] = useState([...mockMessages]);
const chatEndRef = useRef<HTMLDivElement>(null);

// Auto-scroll to bottom
useEffect(() => {
  chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [chatMessages]);
```

#### Send Message Handler
```tsx
const handleSendMessage = () => {
  if (!chatInput.trim()) return;

  const newMessage = {
    id: Date.now().toString(),
    role: 'user' as const,
    content: chatInput,
    timestamp: new Date().toISOString(),
  };

  setChatMessages([...chatMessages, newMessage]);
  setChatInput('');

  // TODO: Send to API and get response
};
```

#### Keyboard Shortcuts
- `Cmd/Ctrl + Enter` для отправки сообщения
- Visual hint внизу input поля

### 4. Mock Chat Data

Добавлены демонстрационные сообщения для showcase:

```tsx
const mockMessages = [
  {
    role: 'user',
    content: 'Объясни как работает JWT authentication',
  },
  {
    role: 'assistant',
    content: `# JWT Authentication Flow

In this project, JWT is used for stateless authentication...

\`\`\`python
@router.post("/login")
async def login(user: UserLogin):
    token = create_access_token(data={"sub": user.email})
    return {"access_token": token}
\`\`\`
    `,
  },
];
```

## UI/UX Features

### Markdown Support
- **Headings** (H1-H3) - styled with proper hierarchy
- **Links** - открываются в новой вкладке
- **Lists** (ordered & unordered) - styled bullets/numbers
- **Inline code** - highlighted with cyan color
- **Code blocks** - full syntax highlighting
- **Blockquotes** - styled with left border
- **Bold/Italic** - standard markdown formatting

### Code Blocks
- Language label (Python, JavaScript, etc.)
- Line numbers
- Copy button with hover effect
- Syntax highlighting (VS Code dark theme)
- Scrollable для длинных блоков

### Visual Polish
- Smooth animations (fade-in)
- Auto-scroll при новых сообщениях
- Hover effects на кнопках
- Loading states (можно добавить)
- Responsive sizing

## Example Usage

```tsx
import { ChatMessages, ChatMessage } from './ChatMessage';

// Single message
<ChatMessage
  role="assistant"
  content="Here's how to implement JWT:\n\n```python\ndef create_token():\n    return jwt.encode(payload)\n```"
  timestamp={new Date().toISOString()}
/>

// Multiple messages
<ChatMessages
  messages={[
    { id: '1', role: 'user', content: 'How does this work?' },
    { id: '2', role: 'assistant', content: 'Let me explain...' },
  ]}
/>
```

## Styling

### Dark Theme Colors
- Background: `#0D1117` (GitHub dark)
- Cards: `#161B22`
- Borders: `#30363D`
- Text: `#E6EDF3`
- Accent: `#00D4FF` (cyan)
- Code blocks: VS Code dark+ theme

### Typography
- Body: `text-sm` (0.875rem)
- Code: `font-mono` with smaller size
- Headings: Bold with proper sizing hierarchy

## Integration Points

### API Integration (TODO)
Для полной интеграции с backend нужно:

1. **Chat API Endpoint**
```python
@router.post("/api/v1/projects/{project_id}/chat")
async def send_chat_message(
    project_id: UUID,
    message: ChatMessage,
    current_user: User = Depends(get_current_user)
):
    # 1. Save message to DB
    # 2. Get relevant code context via RAG
    # 3. Send to LLM (Claude/GPT-4)
    # 4. Stream response via WebSocket
    # 5. Return response
    pass
```

2. **WebSocket Streaming**
```typescript
const ws = new WebSocket(`/ws/chat/${projectId}`);
ws.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  // Append to current message (streaming)
  updateLastMessage(chunk.content);
};
```

3. **React Query Integration**
```tsx
const sendMessage = useMutation({
  mutationFn: async (content: string) => {
    const response = await chatAPI.sendMessage(projectId, content);
    return response.data;
  },
  onSuccess: (data) => {
    setChatMessages((prev) => [...prev, data]);
  },
});
```

## Testing

### Manual Testing
1. Открыть ProjectDetail
2. Боковая панель должна показывать mock сообщения
3. Проверить:
   - Markdown rendering (headings, lists, links)
   - Code blocks с syntax highlighting
   - Copy button работает
   - Отправка сообщений (mock response)
   - Auto-scroll при новых сообщениях
   - Keyboard shortcut (Cmd+Enter)

### Visual Testing
- Messages выровнены (user справа, assistant слева)
- Code blocks имеют syntax highlighting
- Copy button показывает "Copied!" feedback
- Scrollbar появляется когда много сообщений

## Next Steps

1. **Backend API Integration**
   - Создать chat API endpoint
   - Подключить RAG для code context
   - Интегрировать LLM (Claude Sonnet 4.5)

2. **WebSocket Streaming**
   - Real-time streaming ответов LLM
   - Progress indicators

3. **Chat History**
   - Сохранение истории чата в DB
   - Загрузка previous conversations

4. **Advanced Features**
   - Message editing
   - Message deletion
   - Regenerate response
   - Code execution preview
   - Attach files/code snippets

## Performance Considerations

- **Code Highlighting**: Heavy для больших code blocks
  - Solution: Lazy loading, virtual scrolling
- **Auto-scroll**: Может быть jarring
  - Solution: Smooth scroll с animation
- **Message List**: Memory leak риск с большим history
  - Solution: Pagination, virtual list

## Accessibility

- Keyboard navigation (Tab, Enter)
- Screen reader friendly (semantic HTML)
- Focus indicators на buttons
- High contrast colors

## Files Changed

1. `frontend/src/app/components/ChatMessage.tsx` - новый файл
2. `frontend/src/app/components/ProjectDetail.tsx` - обновлен
3. `frontend/package.json` - добавлены зависимости
4. `docs/WEEK7_CHAT_ENHANCEMENT.md` - документация

## Заметки

- Компонент полностью типизирован (TypeScript)
- Использует lucide-react icons
- Совместим с существующими UI primitives
- Ready для API integration
- Поддерживает GitHub Flavored Markdown (tables, strikethrough, task lists)
