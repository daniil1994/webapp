# Week 8: Frontend Integration - Validation UI

## Обзор

Добавлены React компоненты и hooks для отображения результатов валидации и тестирования кода в UI.

## Что реализовано

### 1. API Client Updates ([frontend/src/lib/api.ts](frontend/src/lib/api.ts))

**Новые типы:**
```typescript
interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
  details: {
    language?: string;
    lines_changed?: { original: number; new: number; delta: number };
  };
}

interface TestResult {
  passed: boolean;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  failures: TestFailure[];
  duration: number;
  output: string;
}
```

**Новые методы:**
```typescript
diffsAPI.validate(diffId) // Валидация diff
diffsAPI.applyWithValidation(diffId, validate, runTests) // Применение с опциями
projectsAPIExtended.runTests(projectId, timeout) // Запуск тестов
```

### 2. Validation Hooks ([frontend/src/hooks/useValidation.ts](frontend/src/hooks/useValidation.ts))

```typescript
// Валидация diff
const validateDiff = useValidateDiff();
await validateDiff.mutateAsync(diffId);

// Применение с валидацией
const applyDiff = useApplyDiffWithValidation();
await applyDiff.mutateAsync({ diffId, validate: true, runTests: false });

// Запуск тестов проекта
const runTests = useRunProjectTests();
await runTests.mutateAsync({ projectId, timeout: 300 });

// Автоматическая валидация при загрузке
const { data: validation } = useAutoValidateDiff(diffId);
```

### 3. Validation Results Component ([frontend/src/app/components/ValidationResults.tsx](frontend/src/app/components/ValidationResults.tsx))

**Полный компонент результатов:**
```tsx
<ValidationResults
  validation={validationResult}
  testResult={testResult}
/>
```

**Компактный badge:**
```tsx
<ValidationBadge validation={validationResult} />
```

## Использование в компонентах

### Example 1: DiffCard с валидацией

```tsx
import { useValidateDiff, useApplyDiffWithValidation } from '../../hooks/useValidation';
import { ValidationResults, ValidationBadge } from './ValidationResults';

function DiffCard({ diff }) {
  const [showValidation, setShowValidation] = useState(false);
  const [runTests, setRunTests] = useState(false);

  const validateDiff = useValidateDiff();
  const applyDiff = useApplyDiffWithValidation();

  const handleValidate = async () => {
    const result = await validateDiff.mutateAsync(diff.id);
    setShowValidation(true);
  };

  const handleApply = async () => {
    if (!confirm(`Apply diff to ${diff.file_path}?`)) return;

    try {
      const result = await applyDiff.mutateAsync({
        diffId: diff.id,
        validate: true,
        runTests: runTests
      });

      if (result.status === 'applied') {
        toast.success('Diff applied successfully!');
        refetchDiffs();
      } else {
        toast.error(result.error || 'Failed to apply diff');
      }
    } catch (error) {
      toast.error('Failed to apply diff');
    }
  };

  return (
    <div className="border rounded-lg p-4">
      <h3>{diff.file_path}</h3>

      {/* Validation badge */}
      {validateDiff.data && (
        <ValidationBadge validation={validateDiff.data.validation} />
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-4">
        <button
          onClick={handleValidate}
          disabled={validateDiff.isPending}
        >
          {validateDiff.isPending ? 'Validating...' : 'Validate'}
        </button>

        <label>
          <input
            type="checkbox"
            checked={runTests}
            onChange={(e) => setRunTests(e.target.checked)}
          />
          Run tests
        </label>

        <button
          onClick={handleApply}
          disabled={applyDiff.isPending || (validateDiff.data && !validateDiff.data.validation.is_valid)}
        >
          {applyDiff.isPending ? 'Applying...' : 'Apply'}
        </button>
      </div>

      {/* Validation results */}
      {showValidation && validateDiff.data && (
        <ValidationResults validation={validateDiff.data.validation} />
      )}
    </div>
  );
}
```

### Example 2: Project Tests

```tsx
import { useRunProjectTests } from '../../hooks/useValidation';
import { ValidationResults } from './ValidationResults';

function ProjectTests({ projectId }) {
  const runTests = useRunProjectTests();

  const handleRunTests = async () => {
    const result = await runTests.mutateAsync({
      projectId,
      timeout: 300
    });
  };

  return (
    <div>
      <button
        onClick={handleRunTests}
        disabled={runTests.isPending}
      >
        {runTests.isPending ? 'Running tests...' : 'Run All Tests'}
      </button>

      {runTests.data && (
        <ValidationResults testResult={runTests.data} />
      )}
    </div>
  );
}
```

## UI Features

### Validation Results Display

**Success State:**
```
✓ Code Validation Passed

Language: python
Lines: 100 → 105 (+5)
```

**Error State:**
```
✗ Code Validation Failed

ERRORS:
  Syntax error at line 42, column 10: invalid syntax

WARNINGS:
  Line 15: Trailing whitespace
  Line 23: Tab character found (use spaces)

Language: python
```

### Test Results Display

**All Passed:**
```
✓ All Tests Passed (12.5s)

Total: 42    Passed: 42
Failed: 0    Skipped: 0
```

**Some Failed:**
```
✗ Tests Failed (15.2s)

Total: 42    Passed: 40
Failed: 2    Skipped: 0

FAILED TESTS:
  test_auth::test_login_invalid_credentials
    AssertionError: Expected status 401, got 200

  test_auth::test_logout
    AttributeError: 'NoneType' object has no attribute 'id'
```

## Integration Points

### 1. DiffViewer Component
```tsx
// Add to existing DiffCard
<button onClick={() => validateDiff(diff.id)}>Validate</button>
<ValidationBadge validation={validation} />
<ValidationResults validation={validation} />
```

### 2. Apply Diff Modal
```tsx
<Modal>
  <h2>Apply Diff</h2>

  <label>
    <input type="checkbox" checked={runTests} onChange={...} />
    Run tests after applying
  </label>

  {validation && !validation.is_valid && (
    <Alert type="error">
      Cannot apply: Code has validation errors
    </Alert>
  )}

  <button onClick={handleApply}>Apply Changes</button>
</Modal>
```

### 3. Project Settings
```tsx
<ProjectSettings>
  <button onClick={() => runProjectTests(projectId)}>
    Run All Tests
  </button>

  {testResult && (
    <ValidationResults testResult={testResult} />
  )}
</ProjectSettings>
```

## Workflow UI

```
┌─────────────────────────────────┐
│ Diff Card: auth.py              │
│                                  │
│ [Action: modify]  [✓ Valid]     │
│                                  │
│ ┌─────────────────────────┐    │
│ │ Code changes here       │    │
│ └─────────────────────────┘    │
│                                  │
│ [Validate] [☑ Run Tests] [Apply]│
│                                  │
│ ✓ Code Validation Passed        │
│   Language: python              │
│   Lines: 100 → 105 (+5)         │
│                                  │
│   WARNINGS:                     │
│   • Line 42: Trailing space     │
└─────────────────────────────────┘
```

## Styling

Все компоненты используют единую тему:
- **Success**: green-500, green-900/20 background
- **Error**: red-500, red-900/20 background
- **Warning**: yellow-500, yellow-900/20 background
- **Neutral**: [#7D8590], [#30363D] borders

## Next Steps для полной интеграции

1. **Обновить DiffViewer.tsx:**
   - Добавить кнопку "Validate"
   - Добавить checkbox "Run tests"
   - Показывать ValidationBadge
   - Отображать ValidationResults при клике

2. **Создать ApplyDiffModal:**
   - Подтверждение применения
   - Опции validate/run_tests
   - Предупреждение при ошибках валидации
   - Прогресс-индикатор

3. **Добавить в ProjectSettings:**
   - Кнопка "Run All Tests"
   - История запусков тестов
   - Статистика (passed/failed ratio)

4. **Уведомления:**
   - Toast при успешной валидации
   - Toast при провале тестов
   - Toast при rollback

## Examples для тестирования

```bash
# Frontend dev server
cd frontend
npm run dev

# Test validation
1. Create/modify diff
2. Click "Validate" button
3. See validation results with errors/warnings

# Test apply with tests
1. Check "Run tests" checkbox
2. Click "Apply"
3. If tests fail, changes are rolled back
4. See test results with failures
```

## Notes

- Validation работает синхронно (<1s обычно)
- Test execution асинхронный (может занять минуты)
- При rollback пользователь видит результаты тестов
- ValidationBadge показывается inline для быстрой оценки
- Полные результаты разворачиваются по клику
