# Known Issues

## Chat UI - Send Button Not Responding (Week 5)

**Status:** Unresolved
**Date Reported:** 2026-02-06
**Priority:** High
**Component:** Frontend - ProjectDetail Chat Interface

### Problem Description

The chat send button in ProjectDetail component does not respond to click events. User is unable to send messages through the UI.

### Symptoms

- Send button appears correctly in the UI
- Button visual state changes based on input (enabled/disabled styling)
- onClick handler is properly bound to `handleSendMessage`
- No JavaScript errors in console
- No alert/console.log messages appear when button is clicked
- Event handler is not being triggered at all

### Attempted Solutions

1. ✅ Added debug logging to `handleSendMessage` - no logs appeared
2. ✅ Added inline `alert()` to button onClick - alert did not show
3. ✅ Removed `disabled` attribute temporarily - still no response
4. ✅ Added inline onClick with console.log - no output
5. ✅ Checked browser console - no errors
6. ✅ Verified backend endpoints working (OpenAPI shows all chat endpoints registered)
7. ✅ Checked HMR logs - frontend updates normally

### Technical Details

**File:** `frontend/src/app/components/ProjectDetail.tsx`

**Button Code:**
```tsx
<button
  onClick={handleSendMessage}
  className={cn(...)}
  disabled={!chatInput.trim()}
>
  <Send className="w-3.5 h-3.5" />
</button>
```

**Handler Code:**
```tsx
const handleSendMessage = async () => {
  if (!chatInput.trim() || isSending) return;
  // ... rest of implementation
};
```

### Possible Causes

1. **Z-index/Overlay Issue**: Something might be covering the button
2. **Event Bubbling**: Parent element might be preventing event propagation
3. **React Rendering Issue**: Component might not be fully mounted/updated
4. **Browser Cache**: Frontend changes might not be reflected (unlikely with HMR)
5. **CSS pointer-events**: Button might have `pointer-events: none` applied

### Backend Status

✅ **Backend is working correctly:**
- Chat API endpoints registered: `/api/v1/projects/{id}/chat`
- Database model created: `chat_messages` table
- Migration applied successfully
- LLM integration configured (z.ai)
- RAG system operational

### Workarounds

**Option 1: Use Keyboard Shortcut**
```
Cmd/Ctrl + Enter in textarea should trigger handleSendMessage
```
Status: Not tested

**Option 2: Direct API Testing**
Use API docs at http://localhost:8000/docs to test chat endpoint directly

**Option 3: Curl Testing**
```bash
curl -X POST http://localhost:8000/api/v1/projects/{id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"content": "test message", "use_rag": true}'
```

### Next Steps

1. Test keyboard shortcut (Cmd+Enter) - might work if only button click is broken
2. Inspect element in browser DevTools to check:
   - Z-index stacking
   - Computed CSS (pointer-events, cursor)
   - Event listeners attached
3. Try hard refresh (Cmd+Shift+R) to clear cache
4. Check if issue persists in different browser
5. Consider rebuilding frontend (`npm run build`)

### Impact

**User Experience:**
- ⛔ Unable to send messages via button click
- ⚠️ Chat functionality completely blocked in UI
- ✅ Backend/API fully functional
- ✅ Chat history loading works

**Development:**
- Backend implementation complete
- Frontend UI exists but non-functional
- Integration code written but untested

### Related Files

- `frontend/src/app/components/ProjectDetail.tsx` (lines 66-123, 298-312)
- `frontend/src/lib/api.ts` (lines 428-446)
- `backend/src/api/v1/chat.py`
- `backend/src/services/chat_service.py`

### Environment

- OS: macOS
- Browser: Not specified
- Frontend: Vite + React + TypeScript
- Backend: FastAPI + Python 3.9
- Frontend Port: 5173
- Backend Port: 8000

---

## ✅ Recently Fixed Issues

### Index Status Endpoint 404

**Status:** ✅ FIXED
**Date Fixed:** 2026-02-06
**Priority:** Medium

**Problem:**
Эндпоинт `GET /api/v1/projects/{id}/index/status` возвращал 404 Not Found если у проекта еще не было ни одного indexing job.

**Error Logs:**
```
INFO: "GET /api/v1/projects/.../index/status HTTP/1.1" 404 Not Found
SELECT indexing_jobs.* FROM indexing_jobs WHERE project_id = ... LIMIT 1
ROLLBACK
```

**Root Cause:**
```python
# Line 299 in projects.py
if not jobs:
    raise HTTPException(status_code=404, detail="No indexing jobs found")
```

**Solution:**
Изменено поведение - теперь возвращает placeholder response вместо 404:

```python
if not jobs:
    # Return placeholder status for projects without indexing jobs
    placeholder_job = IndexingJobResponse(
        id=project_id,
        project_id=project_id,
        status="pending",
        progress=0,
        total_files=0,
        current_file=None,
        error=None,
        started_at=None,
        completed_at=None,
        created_at=datetime.utcnow()
    )

    return IndexingStatusResponse(
        job=placeholder_job,
        percentage=0.0,
        is_running=False,
        is_completed=False,
        is_failed=False
    )
```

**File Changed:** `backend/src/api/v1/projects.py` (lines 298-328)

**Impact:** Frontend теперь корректно отображает статус "pending" для проектов без индексации

---

## Other Minor Issues

None currently tracked.
