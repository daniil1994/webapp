# Week 8: Code Execution & Validation

## Обзор

Реализована система автоматической валидации и тестирования кода перед применением изменений. Теперь каждый diff можно проверить на синтаксические ошибки и запустить тесты перед применением.

## Что реализовано

### Backend Services

#### 1. Code Validator Service (`backend/src/services/code_validator.py`)

Валидация синтаксиса кода для различных языков:

**Поддерживаемые языки:**
- Python (`.py`) - через `ast.parse`
- JavaScript (`.js`, `.jsx`) - через Node.js `--check`
- TypeScript (`.ts`, `.tsx`) - через `tsc --noEmit`

**Возможности:**
```python
from src.services.code_validator import get_code_validator

validator = get_code_validator()

# Валидация кода
result = await validator.validate_code(
    code="def hello(): print('world')",
    file_path="example.py"
)

# result.is_valid - True/False
# result.errors - список ошибок
# result.warnings - список предупреждений
# result.details - дополнительная информация

# Валидация diff
result = await validator.validate_diff(
    original_content="old code",
    new_content="new code",
    file_path="file.py"
)
```

**Проверки:**
- Синтаксические ошибки
- Trailing whitespace (warning)
- Tabs vs spaces (warning)
- Lines changed delta

#### 2. Test Runner Service (`backend/src/services/test_runner.py`)

Автоматический запуск тестов проекта:

**Поддерживаемые фреймворки:**
- pytest (Python)
- Jest (JavaScript/TypeScript)
- npm test (generic)

**Автоопределение:**
```python
from src.services.test_runner import get_test_runner

runner = get_test_runner()

# Автоопределение фреймворка
framework = await runner.detect_test_framework("/path/to/project")

# Запуск тестов
result = await runner.run_tests(
    project_path="/path/to/project",
    test_files=["test_file.py"],  # опционально
    timeout=300  # секунды
)

# result.passed - True/False
# result.total_tests - общее количество
# result.passed_tests - успешных
# result.failed_tests - провалившихся
# result.failures - детали провалов
# result.duration - время выполнения
# result.output - полный вывод
```

**Формат результатов:**
```json
{
    "passed": true,
    "total_tests": 42,
    "passed_tests": 42,
    "failed_tests": 0,
    "skipped_tests": 0,
    "duration": 12.5,
    "failures": [],
    "output": "...",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 3. Enhanced Diff Application (`backend/src/services/diff_application.py`)

Обновленный сервис применения diffs с валидацией и тестированием:

**Новые возможности:**
```python
from src.services.diff_application import DiffApplicationService

service = DiffApplicationService()

# Валидация перед применением
validation = await service.validate_diff(diff, project)

# Применение с валидацией и тестированием
result = await service.apply_diff(
    diff,
    project,
    validate=True,      # проверить синтаксис
    run_tests=False     # запустить тесты
)

# Автоматический rollback при провале тестов
# Если run_tests=True и тесты провалятся, изменения откатятся
```

### API Endpoints

#### 1. Validate Diff
```http
POST /api/v1/diffs/{diff_id}/validate
```

Проверка diff без применения.

**Response:**
```json
{
    "success": true,
    "validation": {
        "is_valid": true,
        "errors": [],
        "warnings": ["Line 42: Trailing whitespace"],
        "details": {
            "language": "python",
            "lines_changed": {
                "original": 100,
                "new": 105,
                "delta": 5
            }
        }
    }
}
```

#### 2. Apply Diff with Validation
```http
POST /api/v1/diffs/{diff_id}/apply-with-validation?validate=true&run_tests=false
```

Применение diff с опциональной валидацией и тестированием.

**Query Parameters:**
- `validate` (bool) - валидировать синтаксис перед применением (default: true)
- `run_tests` (bool) - запустить тесты после применения (default: false)

**Response:**
```json
{
    "diff_id": "uuid",
    "status": "applied",
    "error": null,
    "applied_at": "2024-01-01T00:00:00Z"
}
```

**Если тесты провалились:**
```json
{
    "success": false,
    "message": "Tests failed after applying diff. Changes rolled back.",
    "test_result": {
        "passed": false,
        "failed_tests": 2,
        "failures": [
            {
                "test": "test_authentication",
                "message": "AssertionError: Expected 200, got 401"
            }
        ]
    },
    "rollback": {
        "success": true,
        "message": "Rolled back diff for auth.py"
    }
}
```

#### 3. Run Project Tests
```http
POST /api/v1/projects/{project_id}/test?timeout=300
```

Запуск всех тестов проекта.

**Response:**
```json
{
    "passed": true,
    "total_tests": 42,
    "passed_tests": 42,
    "failed_tests": 0,
    "skipped_tests": 0,
    "duration": 12.5,
    "failures": [],
    "output": "===== test session starts =====\n...",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## Workflow

### 1. Safe Diff Application Flow

```
User clicks "Apply"
    ↓
Validate Code Syntax ────→ Errors? → Reject
    ↓ (pass)
Apply to File System
    ↓
Create Backup
    ↓
Run Tests? ────→ Yes ────→ Tests Pass? ─→ No ──→ Rollback
    ↓                           ↓ Yes
    No                      Success!
    ↓
Success!
```

### 2. Example Usage

```python
# 1. Генерация плана
POST /api/v1/plans/generate
→ job_id

# 2. Ожидание завершения через WebSocket
WS /api/v1/jobs/{job_id}
→ plan_id

# 3. Одобрение плана
PATCH /api/v1/plans/{plan_id}
{"status": "approved"}

# 4. Генерация diffs
POST /api/v1/diffs/generate
{"plan_id": "uuid"}
→ [diff_ids]

# 5. Валидация каждого diff
POST /api/v1/diffs/{diff_id}/validate
→ {"is_valid": true, "warnings": [...]}

# 6. Применение с тестированием
POST /api/v1/diffs/{diff_id}/apply-with-validation?run_tests=true
→ {"status": "applied"} или rollback

# 7. Проверка тестов проекта
POST /api/v1/projects/{project_id}/test
→ {"passed": true, "total_tests": 42}
```

## Детали реализации

### Python Validation

```python
try:
    ast.parse(code)
    return ValidationResult(is_valid=True)
except SyntaxError as e:
    return ValidationResult(
        is_valid=False,
        errors=[f"Line {e.lineno}: {e.msg}"]
    )
```

### JavaScript Validation

```bash
# Создаем временный файл
temp_file=$(mktemp --suffix=.js)
echo "$code" > $temp_file

# Проверяем через Node.js
node --check $temp_file

# Если returncode != 0, то ошибка синтаксиса
```

### Test Detection

**pytest:**
- Ищем `pytest.ini`, `setup.cfg`, `pyproject.toml`
- Проверяем `requirements.txt` на наличие pytest
- Ищем директорию `tests/`

**Jest:**
- Ищем `jest.config.js`
- Проверяем `package.json` devDependencies

### Rollback Mechanism

```python
# При применении создается backup
backup_path = self._create_backup(file_path)

# Если тесты провалились
if not test_result.passed:
    # Восстанавливаем из original_content
    with open(file_path, 'w') as f:
        f.write(diff.original_content)

    return {"success": False, "message": "Tests failed, rolled back"}
```

## Преимущества

1. **Безопасность** - код проверяется перед применением
2. **Качество** - автоматические тесты предотвращают регрессию
3. **Откат** - автоматический rollback при провале тестов
4. **Мульти-язык** - поддержка Python, JS, TS
5. **Расширяемость** - легко добавить новые языки/фреймворки

## Ограничения

### Node.js/TypeScript Validation
Требует установки:
```bash
# Node.js
brew install node  # macOS
apt install nodejs # Linux

# TypeScript
npm install -g typescript
```

Если не установлено - validation пропускается с warning.

### Test Frameworks
Требует установки в проекте:
```bash
# Python
pip install pytest pytest-json-report

# JavaScript
npm install --save-dev jest
```

## Следующие шаги

- [ ] Добавить поддержку Go, Rust
- [ ] Линтеры (pylint, eslint)
- [ ] Code coverage metrics
- [ ] Frontend UI для отображения результатов валидации
- [ ] Batch validation (валидация всех diffs плана)
- [ ] Parallel test execution
- [ ] Test result caching

## Примеры ошибок

### Syntax Error
```json
{
    "is_valid": false,
    "errors": [
        "Syntax error at line 42, column 10: invalid syntax"
    ],
    "warnings": [],
    "details": {"language": "python"}
}
```

### Tests Failed
```json
{
    "passed": false,
    "total_tests": 10,
    "passed_tests": 8,
    "failed_tests": 2,
    "failures": [
        {
            "test": "test_auth::test_login_invalid_credentials",
            "message": "AssertionError: Expected status 401, got 200"
        },
        {
            "test": "test_auth::test_logout",
            "message": "AttributeError: 'NoneType' object has no attribute 'id'"
        }
    ]
}
```

## Тестирование

```bash
# Запуск backend
cd backend
python -m uvicorn src.main:app --reload

# Тест валидации
curl -X POST http://localhost:8000/api/v1/diffs/{diff_id}/validate \
  -H "Authorization: Bearer $TOKEN"

# Тест применения с валидацией
curl -X POST "http://localhost:8000/api/v1/diffs/{diff_id}/apply-with-validation?validate=true&run_tests=true" \
  -H "Authorization: Bearer $TOKEN"

# Запуск тестов проекта
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/test?timeout=300" \
  -H "Authorization: Bearer $TOKEN"
```

## Заметки

- Validation работает синхронно (не через WebSocket)
- Test execution может занять долго - лучше увеличить timeout
- Backups сохраняются в `.repa_backups/` директорию
- При rollback восстанавливается `original_content` из diff
- Временные файлы для validation автоматически удаляются
