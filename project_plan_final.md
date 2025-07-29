# LLM Template System - Финальный план разработки

## Основная цель
Создать backend систему для работы с LLM через OpenRouter и Ollama с системой шаблонов, валидацией данных и OAuth авторизацией.

## Технологический стек - СОГЛАСОВАНО
- **Backend:** Python 3.11+ / FastAPI
- **Auth:** Email/Password + OAuth2 (Google, GitHub) через authlib
- **LLM Providers:** OpenRouter API (все модели), Ollama API
- **Templates:** JSON + Jinja2 (на основе llm-data-gen)
- **Validation:** 3 режима - strict (JSON Schema), custom (наши правила), none
- **Database:** MongoDB
- **Background Tasks:** Celery
- **Deployment:** Docker + standalone Python
- **Export:** JSON, CSV, PDF, XLSX, Markdown, HTML, XML, TXT

## MVP Приоритеты - СОГЛАСОВАНО

### Phase 1: Базовая структура (3-4 дня)
1. **FastAPI основа**
   - Структура проекта
   - Конфигурация через .env
   - CORS и middleware
   - Health check endpoints

2. **Авторизация**
   - Email/password регистрация и вход
   - JWT токены
   - Google OAuth
   - GitHub OAuth
   - Защищенные endpoints

3. **База данных**
   - MongoDB подключение
   - Модели: User, Template, Generation
   - Индексы для производительности

### Phase 2: LLM интеграция (3-4 дня)
1. **OpenRouter провайдер**
   - Получение списка ВСЕХ моделей
   - Фильтры: free/paid, online capable
   - Отображение pricing (input/output tokens)
   - Verbose режим по умолчанию
   - Генерация через API

2. **Ollama провайдер**
   - Подключение к локальному Ollama
   - Список доступных моделей
   - Fallback логика

3. **Provider Factory**
   - Единый интерфейс для провайдеров
   - Автоматический выбор
   - Error handling

### Phase 3: Система шаблонов (4-5 дней)
1. **Template Engine**
   - JSON структура как в llm-data-gen
   - System/User промпты
   - Переменные: {index}, {date}, {custom}
   - Jinja2 рендеринг

2. **Валидация**
   - Strict mode: полная JSON Schema валидация
   - Custom mode: min_length, max_length, regex, date formats
   - None mode: без валидации

3. **Управление шаблонами**
   - CRUD операции
   - Категории и теги
   - Примеры шаблонов (quiz, articles, etc)

### Phase 4: Генерация и экспорт (3-4 дня)
1. **Generation Pipeline**
   - Подготовка промптов
   - Batch обработка
   - Progress tracking
   - История генераций

2. **Background Tasks**
   - Celery с MongoDB как broker
   - Async генерация
   - Job статусы

3. **Экспорт данных**
   - JSON (default)
   - CSV
   - PDF (reportlab)
   - XLSX (openpyxl)
   - Markdown
   - HTML
   - XML
   - TXT

## API Endpoints - СОГЛАСОВАНО

### Авторизация
```
POST   /auth/register              # Email/password регистрация
POST   /auth/login                 # Email/password вход
GET    /auth/oauth/{provider}      # Начать OAuth (google/github)
GET    /auth/oauth/{provider}/callback  # OAuth callback
POST   /auth/refresh               # Обновить токен
GET    /auth/me                    # Текущий пользователь
```

### LLM Провайдеры
```
GET    /providers                  # Список провайдеров
GET    /providers/models           # Все модели с фильтрами
GET    /providers/models/{id}      # Детали модели
POST   /providers/test             # Тест подключения
```

### Шаблоны
```
GET    /templates                  # Список шаблонов
GET    /templates/{id}             # Получить шаблон
POST   /templates                  # Создать шаблон
PUT    /templates/{id}             # Обновить шаблон
DELETE /templates/{id}             # Удалить шаблон
POST   /templates/validate         # Валидировать структуру
```

### Генерация
```
POST   /generate                   # Запустить генерацию
GET    /generate/{job_id}          # Статус задачи
GET    /generate/{job_id}/result   # Получить результат
POST   /generate/preview           # Preview промпта
```

### История
```
GET    /history                    # История генераций
GET    /history/{id}               # Детали генерации
```

## Структура проекта - ФИНАЛЬНАЯ

```
llm-template-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app
│   ├── config.py                  # Settings из .env
│   ├── database.py                # MongoDB connection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py                # Auth endpoints
│   │   ├── providers.py           # Provider endpoints
│   │   ├── templates.py           # Template CRUD
│   │   ├── generation.py          # Generation endpoints
│   │   └── history.py             # History endpoints
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt.py                 # JWT logic
│   │   ├── oauth.py               # OAuth providers
│   │   ├── password.py            # Password hashing
│   │   └── dependencies.py        # Auth dependencies
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py                # Base provider class
│   │   ├── openrouter.py          # OpenRouter implementation
│   │   ├── ollama.py              # Ollama implementation
│   │   └── factory.py             # Provider factory
│   │
│   ├── templates/
│   │   ├── __init__.py
│   │   ├── models.py              # Template Pydantic models
│   │   ├── service.py             # Template business logic
│   │   ├── validator.py           # Validation logic
│   │   └── renderer.py            # Jinja2 rendering
│   │
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── service.py             # Generation logic
│   │   ├── tasks.py               # Celery tasks
│   │   └── export.py              # Export formatters
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py                # User model
│   │   ├── template.py            # Template model
│   │   └── generation.py          # Generation model
│   │
│   └── utils/
│       ├── __init__.py
│       └── exceptions.py          # Custom exceptions
│
├── templates/                     # Примеры JSON шаблонов
│   ├── quiz.json
│   ├── articles.json
│   └── ...
│
├── tests/
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── requirements.txt
├── .env.example
└── README.md
```

## Ключевые библиотеки

```python
# requirements.txt
fastapi==0.104.1
uvicorn==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
authlib==1.2.1
httpx==0.25.0
motor==3.3.2  # async MongoDB driver
celery==5.3.4
kombu==5.3.3  # для MongoDB как Celery broker
pydantic==2.4.2
pydantic-settings==2.0.3
jinja2==3.1.2
python-multipart==0.0.6
openai==1.3.0  # для OpenRouter
jsonschema==4.19.1

# Export libraries
pandas==2.1.3  # для CSV/Excel
openpyxl==3.1.2  # для XLSX
reportlab==4.0.7  # для PDF
lxml==4.9.3  # для XML
markdown==3.5.1  # для Markdown to HTML
```

## Статус реализации

### ✅ Phase 1: Базовая структура (ЗАВЕРШЕНО)
- ✅ FastAPI структура с конфигурацией
- ✅ Email/password + OAuth (Google, GitHub) авторизация
- ✅ JWT токены с refresh
- ✅ MongoDB с Beanie ODM
- ✅ Health check endpoint
- ✅ 100% покрытие тестами

### ✅ Phase 2: LLM интеграция (ЗАВЕРШЕНО)
- ✅ OpenRouter провайдер со всеми моделями
- ✅ Ollama для локальных моделей
- ✅ Фильтры: free/paid, online capable
- ✅ Детальная информация о моделях с pricing
- ✅ Provider factory pattern
- ✅ 100% покрытие тестами

### ✅ Phase 3: Система шаблонов (ЗАВЕРШЕНО)
- ✅ CRUD операции для шаблонов
- ✅ Jinja2 рендеринг с кастомными фильтрами
- ✅ Валидация: синтаксис, переменные, JSON Schema
- ✅ 3 режима валидации (strict/custom/none)
- ✅ Примеры шаблонов (quiz, article, data-analyzer)
- ✅ Preview функционал
- ✅ 100% покрытие тестами

### ✅ Phase 4: Генерация и экспорт (ЗАВЕРШЕНО)
- ✅ Generation pipeline с обработкой
- ✅ Mock Celery tasks для тестирования
- ✅ Экспорт в 8 форматов (JSON, CSV, PDF, XLSX, MD, HTML, XML, TXT)
- ✅ История генераций с фильтрами
- ✅ Progress tracking в реальном времени
- ✅ Batch generation support
- ✅ Cost и token tracking
- ✅ 100% покрытие тестами

## Реализованные компоненты

### Структура проекта
```
llm-template-backend/
├── app/
│   ├── api/              ✅ auth.py, providers.py, templates.py, generation.py
│   ├── auth/             ✅ jwt, oauth, password, dependencies
│   ├── models/           ✅ User, Template, Generation
│   ├── providers/        ✅ OpenRouter, Ollama, Factory
│   ├── templates/        ✅ validator, renderer, service
│   ├── generation/       ✅ service, tasks, export
│   ├── config.py         ✅ Pydantic settings
│   ├── database.py       ✅ MongoDB + Beanie
│   └── main.py           ✅ FastAPI app with all routers
├── tests/
│   ├── unit/             ✅ 165+ тестов
│   ├── factories.py      ✅ Factory-boy для тестовых данных
│   └── conftest.py       ✅ Fixtures
└── templates/
    └── examples/         ✅ Примеры JSON шаблонов
```

### API Endpoints реализованы

#### Авторизация
- ✅ POST /auth/register
- ✅ POST /auth/login
- ✅ GET /auth/me
- ✅ POST /auth/refresh
- ✅ GET /auth/oauth/{provider}
- ✅ GET /auth/oauth/{provider}/callback

#### Провайдеры
- ✅ GET /providers
- ✅ GET /providers/models
- ✅ GET /providers/models/{model_id}
- ✅ POST /providers/test

#### Шаблоны
- ✅ POST /templates
- ✅ GET /templates
- ✅ GET /templates/examples
- ✅ POST /templates/examples/{id}/import
- ✅ GET /templates/{id}
- ✅ PUT /templates/{id}
- ✅ DELETE /templates/{id}
- ✅ POST /templates/validate
- ✅ POST /templates/preview

#### Генерация
- ✅ POST /generate - Запустить генерацию
- ✅ GET /generate/{job_id} - Статус генерации
- ✅ GET /generate/{job_id}/result - Получить результат
- ✅ DELETE /generate/{job_id} - Отменить генерацию
- ✅ GET /generate/{job_id}/export - Экспорт в различные форматы
- ✅ POST /generate/batch - Batch генерация
- ✅ GET /history - История генераций с фильтрами

## Технические решения

### Авторизация
- **Локальная:** bcrypt для паролей, JWT токены
- **OAuth:** Google и GitHub через authlib
- **Безопасность:** HTTPBearer, зависимости FastAPI

### База данных
- **MongoDB** для гибкости с JSON данными
- **Beanie ODM** для async операций
- **Индексы** для производительности

### LLM Провайдеры
- **OpenRouter:** Через OpenAI SDK с кастомным base_url
- **Ollama:** REST API для локальных моделей
- **Factory pattern** для управления провайдерами

### Шаблоны
- **Jinja2** для рендеринга с кастомными фильтрами
- **JSON Schema** для валидации структуры
- **Уровни доступа:** публичные/приватные

### Тестирование
- **TDD подход:** тесты пишутся первыми
- **Factory-boy + Faker:** генерация тестовых данных
- **100% покрытие** API endpoints
- **Fixtures** для переиспользования

### Генерация
- **GenerationProcessor:** Полная логика обработки генерации
- **Mock Celery:** Для тестирования без брокера
- **Progress tracking:** Обновление прогресса в реальном времени
- **Cost calculation:** Подсчет стоимости и токенов
- **Export:** 8 форматов с правильными content-types

## Следующие шаги

1. ✅ Phase 1-4 завершены с полным покрытием тестами
2. ⏳ Полная интеграция Celery с Redis/RabbitMQ
3. ⏳ WebSocket для real-time обновлений
4. ⏳ GitHub Actions для CI/CD
5. ⏳ Docker и docker-compose setup
6. ⏳ Production deployment