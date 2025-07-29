# LLM Template System - План разработки

## Основная цель
Создать backend систему для работы с LLM через OpenRouter и Ollama с системой шаблонов, валидацией данных и OAuth авторизацией.

## Технологический стек
- **Backend:** Python 3.11+ / FastAPI
- **Auth:** Email/Password + OAuth2 (Google, GitHub) через authlib
- **LLM Providers:** OpenRouter API (все модели), Ollama API
- **Templates:** JSON + Jinja2 (на основе llm-data-gen)
- **Validation:** Pydantic + custom rules
- **Database:** MongoDB
- **Background Tasks:** Celery
- **Deployment:** Docker + standalone Python

## Архитектура проекта

```
llm-template-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI приложение
│   │   ├── config.py            # Настройки через pydantic-settings
│   │   │
│   │   ├── api/                 # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # OAuth endpoints
│   │   │   ├── templates.py     # CRUD шаблонов
│   │   │   ├── generation.py    # LLM генерация
│   │   │   └── users.py         # Управление пользователями
│   │   │
│   │   ├── auth/                # Аутентификация
│   │   │   ├── __init__.py
│   │   │   ├── oauth.py         # OAuth2 логика
│   │   │   ├── jwt.py           # JWT токены
│   │   │   └── dependencies.py  # FastAPI dependencies
│   │   │
│   │   ├── providers/           # LLM провайдеры
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # Базовый класс
│   │   │   ├── openrouter.py    # OpenRouter интеграция
│   │   │   ├── ollama.py        # Ollama интеграция
│   │   │   └── factory.py       # Provider factory
│   │   │
│   │   ├── templates/           # Система шаблонов
│   │   │   ├── __init__.py
│   │   │   ├── models.py        # Pydantic модели
│   │   │   ├── service.py       # Бизнес-логика
│   │   │   ├── validator.py     # Валидация шаблонов
│   │   │   └── renderer.py      # Jinja2 рендеринг
│   │   │
│   │   ├── models/              # Модели данных
│   │   │   ├── __init__.py
│   │   │   ├── user.py          # User model
│   │   │   ├── template.py      # Template model
│   │   │   └── generation.py    # Generation history
│   │   │
│   │   └── utils/               # Утилиты
│   │       ├── __init__.py
│   │       ├── database.py      # Database connection
│   │       └── exceptions.py    # Custom exceptions
│   │
│   ├── templates/               # JSON файлы шаблонов
│   │   ├── examples/
│   │   └── user/
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
│
├── docs/
└── README.md
```

## Детали реализации - требуют уточнения

### 1. Аутентификация и авторизация
**Вопросы для уточнения:**
- Только Google OAuth или добавить другие провайдеры (GitHub, Microsoft)?
- Нужна ли регистрация через email/password как fallback?
- Какие роли пользователей планируются (admin, user, guest)?
- Нужны ли API keys для программного доступа?

### 2. База данных
**Вопросы для уточнения:**
- PostgreSQL подходит или предпочитаете другую БД?
- Нужна ли миграция данных (Alembic)?
- Хранить ли историю генераций?
- Нужны ли пользовательские шаблоны в БД или только файловые?

### 3. LLM провайдеры
**Вопросы для уточнения:**
- Какие модели OpenRouter приоритетны (Claude, GPT-4, другие)?
- Ollama будет на том же сервере или удаленно?
- Нужна ли поддержка streaming ответов?
- Как обрабатывать лимиты и ошибки провайдеров?

### 4. Система шаблонов
**Вопросы для уточнения:**
- Структура шаблона - какие поля обязательны?
- Типы переменных в шаблонах (text, number, select, file)?
- Нужна ли версионность шаблонов?
- Публичные vs приватные шаблоны?

### 5. Валидация данных
**Вопросы для уточнения:**
- Какие форматы выходных данных (JSON, CSV, text)?
- Нужна ли валидация по JSON Schema?
- Как обрабатывать невалидные ответы от LLM?
- Retry логика при ошибках валидации?

### 6. API дизайн
**Вопросы для уточнения:**
- REST или добавить GraphQL?
- Нужны ли webhooks для долгих операций?
- Rate limiting - какие лимиты?
- Версионирование API (/v1/, /v2/)?

### 7. Безопасность
**Вопросы для уточнения:**
- Где хранить API ключи провайдеров (env, БД, vault)?
- Нужно ли шифрование sensitive данных?
- CORS политика - какие домены разрешить?
- Логирование - что логировать, что нет?

### 8. Производительность
**Вопросы для уточнения:**
- Нужен ли Redis для кеширования?
- Background tasks для долгих генераций (Celery)?
- Максимальный размер запроса/ответа?
- Нужны ли метрики (Prometheus)?

### 9. Развертывание
**Вопросы для уточнения:**
- Docker/Docker Compose?
- Где будет хоститься (VPS, Cloud, on-premise)?
- CI/CD pipeline нужен?
- Мониторинг и алерты?

### 10. Интеграции
**Вопросы для уточнения:**
- Нужна ли интеграция с внешними сервисами?
- Экспорт данных - какие форматы?
- Импорт шаблонов - откуда?
- API для будущего фронтенда - что критично?

## Приоритеты разработки

### Phase 1: MVP (1-2 недели)
1. Базовая структура FastAPI
2. OAuth авторизация (Google)
3. Интеграция с OpenRouter
4. Простая система шаблонов
5. Базовая валидация

### Phase 2: Core Features (2-3 недели)
1. Полная система шаблонов
2. Интеграция Ollama
3. База данных и модели
4. API для всех операций
5. Тесты

### Phase 3: Production Ready (1-2 недели)
1. Оптимизация производительности
2. Безопасность и rate limiting
3. Документация API
4. Docker и deployment
5. Мониторинг

## Следующие шаги
1. Ответить на вопросы выше
2. Обновить план с учетом ответов
3. Начать реализацию с Phase 1